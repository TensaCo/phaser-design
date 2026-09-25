"""Run fal jobs from a JSON list: [{"id", "endpoint", "payload", "out"}]. "@file:path" strings in payloads become data URIs.
Skips jobs whose output exists. python src/jobs.py jobs.json [--only id,id] [-j 4]"""
import base64, json, mimetypes, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
KEY = [l.split('=', 1)[1].strip().strip('"') for l in open(os.path.expanduser('~/Documents/commandagi/.env')) if l.startswith('FAL_KEY=')][0]
LOG = os.path.join(os.path.dirname(__file__), '..', 'docs', 'generation-log.jsonl')

def req(url, data=None):
    cmd = ['curl', '-s', '-m', '300', '-H', 'Authorization: Key ' + KEY, '-H', 'Content-Type: application/json', url]
    if data is not None:
        p = f'/tmp/claude-1000/falpayload-{os.getpid()}-{time.time_ns()}.json'
        os.makedirs('/tmp/claude-1000', exist_ok=True); open(p, 'w').write(json.dumps(data))
        cmd[1:1] = ['-X', 'POST', '--data-binary', '@' + p]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out)
    except Exception: return {'_raw': out[:500]}

UPLOADED = {}
def upload(p):
    if p in UPLOADED: return UPLOADED[p]
    mt = mimetypes.guess_type(p)[0] or 'application/octet-stream'
    r = req('https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3', {'content_type': mt, 'file_name': os.path.basename(p)})
    subprocess.run(['curl', '-s', '-m', '600', '-X', 'PUT', '-H', 'Content-Type: ' + mt, '--data-binary', '@' + p, r['upload_url']], check=True)
    UPLOADED[p] = r['file_url']; return r['file_url']

def inline(v):
    if isinstance(v, str) and v.startswith('@upload:'): return upload(v[8:])
    if isinstance(v, str) and v.startswith('@file:'):
        p = v[6:]; mt = mimetypes.guess_type(p)[0] or 'application/octet-stream'
        return f'data:{mt};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    if isinstance(v, list): return [inline(x) for x in v]
    if isinstance(v, dict): return {k: inline(x) for k, x in v.items()}
    return v

def done(out):
    d = os.path.dirname(out) or '.'
    return os.path.isdir(d) and any(f.startswith(os.path.basename(out) + '.') or f.startswith(os.path.basename(out) + '-0.') for f in os.listdir(d))

def run(job):
    out = job['out']
    if done(out): return f"skip {job['id']}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sub = req('https://queue.fal.run/' + job['endpoint'], inline(job['payload']))
    if 'status_url' not in sub: return f"FAIL submit {job['id']}: {json.dumps(sub)[:400]}"
    t0 = time.time()
    while True:
        st = req(sub['status_url'])
        if st.get('status') == 'COMPLETED': break
        if time.time() - t0 > 1800: return f"TIMEOUT {job['id']}"
        time.sleep(6)
    r = req(sub['response_url'])
    urls = [i['url'] for i in r.get('images', [])]
    for k in ('video', 'audio', 'audio_file'):
        if isinstance(r.get(k), dict) and 'url' in r[k]: urls.append(r[k]['url'])
    if not urls: return f"FAIL {job['id']}: {json.dumps(r)[:400]}"
    saved = []
    for n, u in enumerate(urls):
        if u.startswith('data:'):
            head, b = u.split(',', 1); ext = head.split('/')[1].split(';')[0]
            p = f'{out}-{n}.{ext}' if len(urls) > 1 else f'{out}.{ext}'; open(p, 'wb').write(base64.b64decode(b))
        else:
            ext = u.split('?')[0].rsplit('.', 1)[-1]
            p = f'{out}-{n}.{ext}' if len(urls) > 1 else f'{out}.{ext}'
            subprocess.run(['curl', '-s', '-m', '600', '-o', p, u])
        saved.append(p)
    with open(LOG, 'a') as f:
        f.write(json.dumps({'id': job['id'], 'endpoint': job['endpoint'], 'payload': job['payload'], 'outputs': saved,
                            'request_id': sub.get('request_id'), 'seconds': round(time.time() - t0)}) + '\n')
    return f"ok {job['id']} {saved} {round(time.time() - t0)}s"

if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1]))
    if '--only' in sys.argv: ids = sys.argv[sys.argv.index('--only') + 1].split(','); jobs = [j for j in jobs if j['id'] in ids]
    n = int(sys.argv[sys.argv.index('-j') + 1]) if '-j' in sys.argv else 4
    with ThreadPoolExecutor(n) as ex:
        for msg in ex.map(run, jobs): print(msg, flush=True)
