"""Fused CUDA kernel for the LINEAR runs of a twin round trip (2026-10-12): consecutive prop / scale / flip / mul ops are
applied to a 64×64 complex64 field held in shared memory by one thread block per sample, with 64-point FFTs done as an
8×8 (four-step) decomposition in registers. Backward = the exact adjoint (reversed program: prop → ×W, FFT, ×conj H, IFFT;
mul → ×conj T), so torch autograd sees an ordinary linear Function. The nonlinear / programmable head stays in torch.

Frequency-domain layout: after a forward pass, position p (per axis) holds frequency swap(p) = p//8 + 8·(p%8); kernels H are
permuted the same way on the host, so no reordering is ever done on the device.
"""
import math, os
import torch
from torch.utils.cpp_extension import load_inline

CUDA = r'''
#include <torch/extension.h>
#include <cuda_runtime.h>
#define NN 64
#define LD 65
__constant__ float2 TW[64];

__device__ __forceinline__ float2 cmul(float2 a, float2 b) { return make_float2(a.x*b.x - a.y*b.y, a.x*b.y + a.y*b.x); }
__device__ __forceinline__ float2 cmulc(float2 a, float2 b) { return make_float2(a.x*b.x + a.y*b.y, a.y*b.x - a.x*b.y); }  // a·conj(b)
__device__ __forceinline__ float2 cadd(float2 a, float2 b) { return make_float2(a.x + b.x, a.y + b.y); }
__device__ __forceinline__ float2 csub(float2 a, float2 b) { return make_float2(a.x - b.x, a.y - b.y); }

// 8-point DFT in registers, v[k] = sum_m v[m] exp(D·2πi·m·k/8), D = -1 forward, +1 inverse (unnormalised). Radix-2 DIF.
template <int D> __device__ __forceinline__ void dft8(float2* x) {
  const float r = 0.70710678118654752f;
  float2 t;
  #pragma unroll
  for (int i = 0; i < 4; i++) { t = csub(x[i], x[i + 4]); x[i] = cadd(x[i], x[i + 4]); x[i + 4] = t; }
  x[5] = cmul(x[5], make_float2(r, D * r));
  x[6] = make_float2(-D * x[6].y, D * x[6].x);
  x[7] = cmul(x[7], make_float2(-r, D * r));
  #pragma unroll
  for (int b = 0; b < 8; b += 4) {
    #pragma unroll
    for (int i = 0; i < 2; i++) { t = csub(x[b + i], x[b + i + 2]); x[b + i] = cadd(x[b + i], x[b + i + 2]); x[b + i + 2] = t; }
    x[b + 3] = make_float2(-D * x[b + 3].y, D * x[b + 3].x);
  }
  #pragma unroll
  for (int b = 0; b < 8; b += 2) { t = csub(x[b], x[b + 1]); x[b] = cadd(x[b], x[b + 1]); x[b + 1] = t; }
  t = x[1]; x[1] = x[4]; x[4] = t;
  t = x[3]; x[3] = x[6]; x[6] = t;
}

// op codes: 0 PROP(H, W, flags: 1 conjH, 2 W-before (adjoint), 4 no W), 1 SCALE(a), 2 MUL(T, flags 1 conj), 3 FLIPX, 4 FLIPY
__global__ void __launch_bounds__(512) linear_run_kernel(const float2* __restrict__ Ein, float2* __restrict__ Eout, const int4* __restrict__ prog, int nops,
    const float2* __restrict__ Hs, const float* __restrict__ Ws, const float2* __restrict__ Ts, const float* __restrict__ scales) {
  __shared__ float2 s[NN * LD];
  const int tid = threadIdx.x;
  const int lo = tid & 63, hi = tid >> 6;  // lo: row (row passes) or column (column passes); hi: 0..7 digit
  const float2* E = Ein + (size_t)blockIdx.x * NN * NN;
  for (int i = tid; i < NN * NN; i += 512) s[(i >> 6) * LD + (i & 63)] = E[i];
  __syncthreads();
  float2 v[8];
  for (int o = 0; o < nops; o++) {
    const int4 op = prog[o];
    if (op.x == 0) {
      const float2* H = Hs + (size_t)op.y * NN * NN;
      const float* W = (op.w & 4) ? nullptr : Ws + (size_t)op.z * NN * NN;
      const bool conjH = op.w & 1, wBefore = op.w & 2;
      // row forward, step 1: thread (r = lo, j = hi) — elements j + 8m of row r
      #pragma unroll
      for (int m = 0; m < 8; m++) {
        float2 a = s[lo * LD + hi + 8 * m];
        if (wBefore && W) { float w = W[lo * NN + hi + 8 * m]; a.x *= w; a.y *= w; }
        v[m] = a;
      }
      dft8<-1>(v);
      #pragma unroll
      for (int k = 0; k < 8; k++) s[lo * LD + hi + 8 * k] = cmul(v[k], TW[hi * 8 + k]);
      __syncthreads();
      // row forward, step 2: thread (r = lo, k1 = hi) — contiguous 8k1..8k1+7
      #pragma unroll
      for (int j = 0; j < 8; j++) v[j] = s[lo * LD + 8 * hi + j];
      dft8<-1>(v);
      #pragma unroll
      for (int k = 0; k < 8; k++) s[lo * LD + 8 * hi + k] = v[k];
      __syncthreads();
      // column forward, step 1: thread (c = lo, j = hi)
      #pragma unroll
      for (int m = 0; m < 8; m++) v[m] = s[(hi + 8 * m) * LD + lo];
      dft8<-1>(v);
      #pragma unroll
      for (int k = 0; k < 8; k++) s[(hi + 8 * k) * LD + lo] = cmul(v[k], TW[hi * 8 + k]);
      __syncthreads();
      // column forward step 2 (thread (c = lo, k1 = hi)), × H, column inverse step 2' — all in registers
      #pragma unroll
      for (int j = 0; j < 8; j++) v[j] = s[(8 * hi + j) * LD + lo];
      dft8<-1>(v);
      #pragma unroll
      for (int k = 0; k < 8; k++) { float2 h = H[(8 * hi + k) * NN + lo]; v[k] = conjH ? cmulc(v[k], h) : cmul(v[k], h); }
      dft8<1>(v);
      #pragma unroll
      for (int j = 0; j < 8; j++) s[(8 * hi + j) * LD + lo] = cmulc(v[j], TW[j * 8 + hi]);
      __syncthreads();
      // column inverse step 1': thread (c = lo, j = hi) gathers k1 = 0..7 at rows 8k1 + j
      #pragma unroll
      for (int k = 0; k < 8; k++) v[k] = s[(8 * k + hi) * LD + lo];
      dft8<1>(v);
      #pragma unroll
      for (int m = 0; m < 8; m++) s[(hi + 8 * m) * LD + lo] = v[m];
      __syncthreads();
      // row inverse step 2': thread (r = lo, k1 = hi)
      #pragma unroll
      for (int k = 0; k < 8; k++) v[k] = s[lo * LD + 8 * hi + k];
      dft8<1>(v);
      #pragma unroll
      for (int j = 0; j < 8; j++) s[lo * LD + 8 * hi + j] = cmulc(v[j], TW[j * 8 + hi]);
      __syncthreads();
      // row inverse step 1': thread (r = lo, j = hi), normalise 1/4096, × W after (forward op)
      #pragma unroll
      for (int k = 0; k < 8; k++) v[k] = s[lo * LD + 8 * k + hi];
      dft8<1>(v);
      #pragma unroll
      for (int m = 0; m < 8; m++) {
        float w = (1.0f / 4096.0f);
        if (!wBefore && W) w *= W[lo * NN + hi + 8 * m];
        s[lo * LD + hi + 8 * m] = make_float2(v[m].x * w, v[m].y * w);
      }
      __syncthreads();
    } else if (op.x == 1) {
      const float a = scales[op.y];
      for (int i = tid; i < NN * NN; i += 512) { float2 z = s[(i >> 6) * LD + (i & 63)]; s[(i >> 6) * LD + (i & 63)] = make_float2(z.x * a, z.y * a); }
      __syncthreads();
    } else if (op.x == 2) {
      const float2* T = Ts + (size_t)op.y * NN * NN;
      for (int i = tid; i < NN * NN; i += 512) { float2 z = s[(i >> 6) * LD + (i & 63)]; s[(i >> 6) * LD + (i & 63)] = (op.w & 1) ? cmulc(z, T[i]) : cmul(z, T[i]); }
      __syncthreads();
    } else {
      // flips: each thread owns 8 elements; read all, sync, write mirrored
      #pragma unroll
      for (int q = 0; q < 8; q++) { int i = tid + 512 * q; v[q] = s[(i >> 6) * LD + (i & 63)]; }
      __syncthreads();
      #pragma unroll
      for (int q = 0; q < 8; q++) { int i = tid + 512 * q; int r = i >> 6, c = i & 63; if (op.x == 3) c = 63 - c; else r = 63 - r; s[r * LD + c] = v[q]; }
      __syncthreads();
    }
  }
  float2* O = Eout + (size_t)blockIdx.x * NN * NN;
  for (int i = tid; i < NN * NN; i += 512) O[i] = s[(i >> 6) * LD + (i & 63)];
}


// ── nonlinear head (elementwise) ──
// pre:  v = a·E + c·inj,  u = t·v,  y = u·A(|u|²),  A = sqrt(max(0, 1 + s/(1 + I/Ia)))   (absorber; t = combined SLM × amplitude program)
__global__ void pre_fwd_kernel(const float2* E, const float2* inj, int injD, const float2* t, float2* y, long total, int B, int N, float a, float c, float s, float Ia) {
  for (long i = blockIdx.x * (long)blockDim.x + threadIdx.x; i < total; i += (long)gridDim.x * blockDim.x) {
    const int p = i % N; const long db = i / N; const int b = db % B; const int d = db / B;
    float2 v = E[i]; v.x *= a; v.y *= a;
    if (inj) { float2 q = inj[((long)(injD == 1 ? 0 : d) * B + b) * N + p]; v.x += c * q.x; v.y += c * q.y; }
    float2 u = cmul(t[(long)d * N + p], v);
    float I = u.x * u.x + u.y * u.y;
    float g = 1.f + s / (1.f + I / Ia);
    float A = g > 0.f ? sqrtf(g) : 0.f;
    y[i] = make_float2(u.x * A, u.y * A);
  }
}
__global__ void pre_bwd_kernel(const float2* G, const float2* E, const float2* inj, int injD, const float2* t, float2* gE, float2* gt, long total, int B, int N, float a, float c, float s, float Ia) {
  for (long i = blockIdx.x * (long)blockDim.x + threadIdx.x; i < total; i += (long)gridDim.x * blockDim.x) {
    const int p = i % N; const long db = i / N; const int b = db % B; const int d = db / B;
    float2 v = E[i]; v.x *= a; v.y *= a;
    if (inj) { float2 q = inj[((long)(injD == 1 ? 0 : d) * B + b) * N + p]; v.x += c * q.x; v.y += c * q.y; }
    const float2 tt = t[(long)d * N + p];
    float2 u = cmul(tt, v);
    float I = u.x * u.x + u.y * u.y;
    float x = 1.f + I / Ia;
    float g = 1.f + s / x;
    float A = 0.f, dA = 0.f;
    if (g > 0.f) { A = sqrtf(g); dA = (-s / (Ia * x * x)) / (2.f * A); }
    float2 gy = G[i];
    float re = gy.x * u.x + gy.y * u.y;           // Re(g · conj(u))
    float2 gu = make_float2(gy.x * A + 2.f * dA * re * u.x, gy.y * A + 2.f * dA * re * u.y);
    float2 gv = cmulc(gu, tt);                     // conj(t) · ū
    gE[i] = make_float2(a * gv.x, a * gv.y);
    float2 gtt = cmulc(gu, v);                     // ū · conj(v)
    atomicAdd(&gt[(long)d * N + p].x, gtt.x); atomicAdd(&gt[(long)d * N + p].y, gtt.y);
  }
}
// gain: y = E·A,  A = sqrt(max(0, 1 + (G0 − 1)/(1 + J/Ig))), J = |E|² (local) or the diffused intensity Is (given)
__global__ void gain_fwd_kernel(const float2* E, const float* Is, const float* G0, float2* y, long total, int B, int N, float Ig) {
  for (long i = blockIdx.x * (long)blockDim.x + threadIdx.x; i < total; i += (long)gridDim.x * blockDim.x) {
    const int d = i / ((long)B * N);
    float2 e = E[i];
    float J = Is ? Is[i] : e.x * e.x + e.y * e.y;
    float h = 1.f + (G0[d] - 1.f) / (1.f + J / Ig);
    float A = h > 0.f ? sqrtf(h) : 0.f;
    y[i] = make_float2(e.x * A, e.y * A);
  }
}
// backward: gE = g·A (+ 2·A'·Re(g·conj E)·E when local); q = Re(g·conj E)·A'(Is) (diffusive: caller adds 2·conv(q)·E); gG0[d] = Σ Re(g·conj E)·dA/dG0
__global__ void gain_bwd_kernel(const float2* G, const float2* E, const float* Is, const float* G0, float2* gE, float* q, float* gG0, long total, int B, int N, float Ig) {
    float acc = 0.f; int dcur = -1;
  for (long i = blockIdx.x * (long)blockDim.x + threadIdx.x; i < total; i += (long)gridDim.x * blockDim.x) {
    const int d = i / ((long)B * N);
    if (d != dcur) { if (dcur >= 0 && acc != 0.f) atomicAdd(&gG0[dcur], acc); acc = 0.f; dcur = d; }
    float2 e = E[i], gy = G[i];
    float J = Is ? Is[i] : e.x * e.x + e.y * e.y;
    float x = 1.f + J / Ig;
    float h = 1.f + (G0[d] - 1.f) / x;
    float A = 0.f, dA = 0.f, dAdG = 0.f;
    if (h > 0.f) { A = sqrtf(h); dA = (-(G0[d] - 1.f) / (Ig * x * x)) / (2.f * A); dAdG = 1.f / (x * 2.f * A); }
    float re = gy.x * e.x + gy.y * e.y;
    if (Is) { gE[i] = make_float2(gy.x * A, gy.y * A); q[i] = re * dA; }
    else gE[i] = make_float2(gy.x * A + 2.f * dA * re * e.x, gy.y * A + 2.f * dA * re * e.y);
    acc += re * dAdG;
  }
  if (dcur >= 0 && acc != 0.f) atomicAdd(&gG0[dcur], acc);
}
#define GRID(total) dim3((unsigned)std::min<long>((total + 255) / 256, 4096L)), dim3(256)
static const float2* cptr(const torch::Tensor& x) { return x.numel() ? (const float2*)x.data_ptr() : nullptr; }
static const float* fptr(const torch::Tensor& x) { return x.numel() ? x.data_ptr<float>() : nullptr; }
torch::Tensor pre_fwd(torch::Tensor E, torch::Tensor inj, torch::Tensor t, double a, double c, double s, double Ia) {
  auto y = torch::empty_like(E); long total = E.numel(); int B = E.size(1), N = E.size(2) * E.size(3);
  pre_fwd_kernel<<<GRID(total)>>>(cptr(E), cptr(inj), inj.numel() ? inj.size(0) : 1, cptr(t), (float2*)y.data_ptr(), total, B, N, a, c, s, Ia);
  return y;
}
std::vector<torch::Tensor> pre_bwd(torch::Tensor G, torch::Tensor E, torch::Tensor inj, torch::Tensor t, double a, double c, double s, double Ia) {
  auto gE = torch::empty_like(E); auto gt = torch::zeros_like(t); long total = E.numel(); int B = E.size(1), N = E.size(2) * E.size(3);
  pre_bwd_kernel<<<GRID(total)>>>(cptr(G), cptr(E), cptr(inj), inj.numel() ? inj.size(0) : 1, cptr(t), (float2*)gE.data_ptr(), (float2*)gt.data_ptr(), total, B, N, a, c, s, Ia);
  return {gE, gt};
}
torch::Tensor gain_fwd(torch::Tensor E, torch::Tensor Is, torch::Tensor G0, double Ig) {
  auto y = torch::empty_like(E); long total = E.numel(); int B = E.size(1), N = E.size(2) * E.size(3);
  gain_fwd_kernel<<<GRID(total)>>>(cptr(E), fptr(Is), G0.data_ptr<float>(), (float2*)y.data_ptr(), total, B, N, Ig);
  return y;
}
std::vector<torch::Tensor> gain_bwd(torch::Tensor G, torch::Tensor E, torch::Tensor Is, torch::Tensor G0, double Ig) {
  auto gE = torch::empty_like(E); auto gG0 = torch::zeros_like(G0);
  auto q = Is.numel() ? torch::empty_like(Is) : torch::empty({0}, Is.options());
  long total = E.numel(); int B = E.size(1), N = E.size(2) * E.size(3);
  gain_bwd_kernel<<<GRID(total)>>>(cptr(G), cptr(E), fptr(Is), G0.data_ptr<float>(), (float2*)gE.data_ptr(), q.numel() ? q.data_ptr<float>() : nullptr, gG0.data_ptr<float>(), total, B, N, Ig);
  return {gE, q, gG0};
}

static bool tw_ready = false;
torch::Tensor linear_run(torch::Tensor E, torch::Tensor prog, torch::Tensor Hs, torch::Tensor Ws, torch::Tensor Ts, torch::Tensor scales) {
  if (!tw_ready) {
    float2 tw[64];
    for (int j = 0; j < 8; j++) for (int k = 0; k < 8; k++) { double a = -2.0 * M_PI * j * k / 64.0; tw[j * 8 + k] = make_float2((float)cos(a), (float)sin(a)); }
    cudaMemcpyToSymbol(TW, tw, sizeof(tw));
    tw_ready = true;
  }
  auto Ec = E.contiguous();
  auto out = torch::empty_like(Ec);
  const int S = Ec.numel() / (64 * 64);
  linear_run_kernel<<<S, 512>>>((const float2*)Ec.data_ptr(), (float2*)out.data_ptr(), (const int4*)prog.data_ptr(), prog.size(0),
      (const float2*)Hs.data_ptr(), Ws.data_ptr<float>(), (const float2*)Ts.data_ptr(), scales.data_ptr<float>());
  return out;
}
'''
CPP = '''torch::Tensor linear_run(torch::Tensor E, torch::Tensor prog, torch::Tensor Hs, torch::Tensor Ws, torch::Tensor Ts, torch::Tensor scales);
torch::Tensor pre_fwd(torch::Tensor E, torch::Tensor inj, torch::Tensor t, double a, double c, double s, double Ia);
std::vector<torch::Tensor> pre_bwd(torch::Tensor G, torch::Tensor E, torch::Tensor inj, torch::Tensor t, double a, double c, double s, double Ia);
torch::Tensor gain_fwd(torch::Tensor E, torch::Tensor Is, torch::Tensor G0, double Ig);
std::vector<torch::Tensor> gain_bwd(torch::Tensor G, torch::Tensor E, torch::Tensor Is, torch::Tensor G0, double Ig);'''

_ext = None


def ext():
    global _ext
    if _ext is None:
        import sys
        os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + '/usr/local/cuda/bin' + os.pathsep + os.environ.get('PATH', '')
        os.environ.setdefault('CUDA_HOME', '/usr/local/cuda')
        _ext = load_inline(name='phaser_fused_v2', cpp_sources=CPP, cuda_sources=CUDA, functions=['linear_run', 'pre_fwd', 'pre_bwd', 'gain_fwd', 'gain_bwd'],
                           extra_cuda_cflags=['-O3', '--use_fast_math'], build_directory=_build_dir(), verbose=False)
    return _ext


def _build_dir():
    d = os.path.join(os.environ.get('TMPDIR', '/dev/shm'), 'phaser_fused_build')
    os.makedirs(d, exist_ok=True)
    return d


SWAP = torch.tensor([p // 8 + 8 * (p % 8) for p in range(64)])
LINEAR = ('prop', 'scale', 'flip-x', 'flip-y', 'mul')


class Run:
    """one maximal run of linear ops (must contain a prop), compiled to forward and adjoint programs."""

    def __init__(self, ops, dev):
        Hs, Ws, Ts, sc = [], [], [], []
        idx = {}

        def put(lst, t, key):
            if key not in idx:
                idx[key] = len(lst)
                lst.append(t)
            return idx[key]

        fwd = []
        for o in ops:
            k = o['op']
            if k == 'prop':
                h = put(Hs, o['H'].to(torch.complex64)[SWAP][:, SWAP], ('H', id(o['H'])))
                if o['W'] is None:
                    fwd.append((0, h, 0, 4))
                else:
                    fwd.append((0, h, put(Ws, o['W'].to(torch.float32), ('W', id(o['W']))), 0))
            elif k == 'scale':
                fwd.append((1, put(sc, float(o['a']), ('s', len(sc))), 0, 0))
            elif k == 'mul':
                fwd.append((2, put(Ts, o['T'].to(torch.complex64), ('T', id(o['T']))), 0, 0))
            elif k == 'flip-x':
                fwd.append((3, 0, 0, 0))
            elif k == 'flip-y':
                fwd.append((4, 0, 0, 0))
        adj = []
        for (c, a, b, f) in reversed(fwd):
            if c == 0:
                adj.append((0, a, b, 1 | (2 if not f & 4 else 4)))
            elif c == 2:
                adj.append((2, a, 0, 1))
            else:
                adj.append((c, a, b, f))
        z = lambda dt: torch.zeros(1, 64, 64, dtype=dt, device=dev)
        self.Hs = torch.stack(Hs).contiguous().to(dev) if Hs else z(torch.complex64)
        self.Ws = torch.stack(Ws).contiguous().to(dev) if Ws else z(torch.float32)
        self.Ts = torch.stack(Ts).contiguous().to(dev) if Ts else z(torch.complex64)
        self.sc = torch.tensor(sc or [1.0], dtype=torch.float32, device=dev)
        self.pf = torch.tensor(fwd, dtype=torch.int32, device=dev)
        self.pa = torch.tensor(adj, dtype=torch.int32, device=dev)

    def apply(self, E, adjoint=False):
        sh = E.shape
        out = ext().linear_run(E.reshape(-1, 64, 64), self.pa if adjoint else self.pf, self.Hs, self.Ws, self.Ts, self.sc)
        return out.reshape(sh)


class _Lin(torch.autograd.Function):
    @staticmethod
    def forward(ctx, E, run):
        ctx.run = run
        return run.apply(E)

    @staticmethod
    def backward(ctx, g):
        return ctx.run.apply(g.contiguous(), adjoint=True), None


def segments(tw, ops=None):
    """split a GTwin op list into [('lin', Run) | ('op', o)] for the fused trip (c64, 64×64 only)."""
    out, cur = [], []

    def flush():
        if cur and any(o['op'] == 'prop' for o in cur):
            out.append(('lin', Run(list(cur), tw.dev)))
        else:
            out.extend(('op', o) for o in cur)
        cur.clear()

    for o in (tw.ops if ops is None else ops):
        if o['op'] in LINEAR:
            cur.append(o)
        else:
            flush()
            out.append(('op', o))
    flush()
    return out


def lin(E, run):
    return _Lin.apply(E, run)


# ── fused nonlinear head ──
_EMPTY = {}


def _empty(dt, dev):
    k = (dt, dev)
    if k not in _EMPTY:
        _EMPTY[k] = torch.empty(0, dtype=dt, device=dev)
    return _EMPTY[k]


class _Pre(torch.autograd.Function):
    """y = nl(t ⊙ (a·E + c·inj)); grads for E and t (t: (D, 1, n, n), summed over cases)."""
    @staticmethod
    def forward(ctx, E, t, inj, a, c, s, Ia):
        E = E.contiguous(); t = t.contiguous()
        injc = inj.contiguous() if inj is not None else _empty(torch.complex64, E.device)
        ctx.save_for_backward(E, t, injc)
        ctx.k = (a, c, s, Ia)
        return ext().pre_fwd(E, injc, t, a, c, s, Ia)

    @staticmethod
    def backward(ctx, g):
        E, t, injc = ctx.saved_tensors
        gE, gt = ext().pre_bwd(g.contiguous(), E, injc, t, *ctx.k)
        return gE, gt, None, None, None, None, None


class _Gain(torch.autograd.Function):
    """y = E·sqrt(1 + (G0−1)/(1 + J/Ig)); J = |E|² (local, resp=None) or J = conv(|E|², resp) (diffusive)."""
    @staticmethod
    def forward(ctx, E, G0, Ig, resp):
        E = E.contiguous(); G0 = G0.contiguous()
        if resp is not None:
            Is = torch.fft.irfft2(torch.fft.rfft2(E.real ** 2 + E.imag ** 2) * resp, s=E.shape[-2:]).clamp_min(0).contiguous()
        else:
            Is = _empty(torch.float32, E.device)
        ctx.save_for_backward(E, G0, Is)
        ctx.Ig, ctx.resp = Ig, resp
        return ext().gain_fwd(E, Is, G0, Ig)

    @staticmethod
    def backward(ctx, g):
        E, G0, Is = ctx.saved_tensors
        gE, q, gG0 = ext().gain_bwd(g.contiguous(), E, Is, G0, ctx.Ig)
        if ctx.resp is not None:
            # the clamp at 0 is inactive for a positive kernel; conv adjoint = conv (real, even response)
            gE = gE + 2 * torch.fft.irfft2(torch.fft.rfft2(q) * ctx.resp, s=E.shape[-2:]) * E
        return gE, gG0, None, None


def pre(E, t, inj, a, c, s, Ia):
    return _Pre.apply(E, t, inj, a, c, s, Ia)


def gain(E, G0, Ig, resp):
    return _Gain.apply(E, G0, Ig, resp)
