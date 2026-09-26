"""Generate the shot list, transcripts and typography sheet from the EDL (so the documents always match the cut)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import importlib
V2 = '--v2' in sys.argv
_e = importlib.import_module('edl_v2' if V2 else 'edl'); EDL, CUTS = _e.EDL, _e.CUTS
_s = importlib.import_module('script_v2' if V2 else 'script'); LINES, VOICE = _s.LINES, _s.VOICE
SUF = '-v2' if V2 else ''
VO_DIR = 'gen/v2/vo' if V2 else 'gen/vo'

TEXT = {i: (s, t) for i, s, t in LINES}
WHO = {'NAR': 'Narrator', 'ENG': 'Optical engineer (dramatized)', 'B1': 'Head of inference, AI company (dramatized)',
       'B2': 'Infrastructure lead, datacenter operator (dramatized)'}
if V2: WHO = _s.WHO
ACT = {'a': 'ACT 1 — The physical limit', 'b': 'ACT 2 — PHASER reveal', 'c': 'ACT 3 — The engineer', 'd': 'ACT 4 — The people who use it',
       'e': 'ACT 5 — The bottleneck moves outward', 'f': 'ACT 6 — Human stakes', 'g': 'ACT 7 — Resolution', 'h': 'ACT 8 — End frame'}
if V2: ACT = {'A': 'COLD OPEN (score: near silence)', 'B': 'HERO (score: hero theme)', 'C': 'MIDDLE (score: intimate piano)', 'D': 'BUILD (score: rising ostinato)',
            'E': 'HUMAN STAKES (score: strings open)', 'F': 'CLIMAX (score: hero theme returns)', 'G': 'END (score: motif alone, fade)'}

def tc(t): return f'{int(t // 60)}:{t % 60:05.2f}'
def clean(t): return t.replace('[laughs]', '(laughs)').replace('[short pause]', '').replace('  ', ' ')

def source(c):
    s = c['src']
    if s == 'black': return 'black'
    if s.startswith('png:gen/render'): return f"three.js render of the site's PHASER scene ({s.split('/')[-1]})"
    if s.startswith('png:gen/viz'): return 'numpy scientific visualization (src/viz_electrons.py)'
    if 'gen/ls/' in s: return f"image-to-video + lip-sync ({os.path.basename(s)})"
    if 'gen/video/' in s: return f"image-to-video ({os.path.basename(s)})"
    return f"stock footage ({os.path.basename(s)})"

def main():
    os.makedirs('docs', exist_ok=True)
    t = 0; shot = ['# Shot list (master)', '', 'Generated from `src/edl.py` by `src/docs.py`. Timecodes are m:ss.ff (seconds).', '']
    tr = ['# Full transcript (master)', '', 'Spoken lines with timecodes. Every on-camera person is a dramatized role played by an AI-generated character with an AI voice.', '']
    typo = ['# On-screen typography (master)', '', 'Every frame also carries the centred label **PLANNED FUTURE PRODUCT LAUNCH VIDEO**, and generated shots carry a top-right tag ("DRAMATIZATION · AI-GENERATED PEOPLE, PLACES AND VOICES", "AI-GENERATED IMAGERY" or "STOCK FOOTAGE").', '',
            '| in | out | kind | text |', '|---|---|---|---|']
    eng, biz, nar = [], [], []
    by_spk = {}
    act = None
    for c in EDL:
        if c['id'][0] != act:
            act = c['id'][0]; shot += ['', f'## {ACT[act]}', '', '| # | in | out | dur | source | grade | sound | on screen | voice |', '|---|---|---|---|---|---|---|---|---|']
        on = '; '.join(' / '.join(x for x in it[3:] if x not in ('left', 'right', 'noscrim')) for it in c.get('text', []))
        vo = '; '.join(f"{TEXT[v[1]][0]}: {clean(TEXT[v[1]][1])[:60]}…" if len(TEXT[v[1]][1]) > 60 else f"{TEXT[v[1]][0]}: {clean(TEXT[v[1]][1])}" for v in c.get('vo', []))
        snd = ', '.join([c.get('amb') or ''] + [n for _, n in c.get('sfx', [])])
        shot.append(f"| {c['id']} | {tc(t)} | {tc(t + c['dur'])} | {c['dur']:.1f} | {source(c)} | {c.get('grade', '—')} | {snd} | {on} | {vo} |")
        for vv in c.get('vo', []):
            ts, lid = vv[0], vv[1]
            s, text = TEXT[lid]
            line = f"**{tc(t + ts)}** — *{WHO[s]}*: {clean(text)}"
            tr.append(line + '  ')
            {'NAR': nar, 'ENG': eng}.get(s, biz).append(line + '  ')
            by_spk.setdefault(s, []).append(line + '  ')
        for it in c.get('text', []):
            typo.append(f"| {tc(t + it[0])} | {tc(t + it[1])} | {it[2]} | {' / '.join(x for x in it[3:] if x not in ('left', 'right', 'noscrim'))} |")
        t += c['dur']
    shot += ['', f'**Running time: {tc(t)} ({t:.1f} s).**', '']
    for k, v in CUTS.items():
        by = {c['id']: c for c in EDL}
        dur = sum(ov.get('dur', by[i]['dur']) for i, ov in v)
        shot.append(f"- `{k}` ({dur:.1f} s): " + ', '.join(i for i, _ in v))
    open(f'docs/SHOT-LIST{SUF}.md', 'w').write('\n'.join(shot) + '\n')
    open(f'docs/TRANSCRIPT{SUF}.md', 'w').write('\n'.join(tr) + '\n')
    open(f'docs/TYPOGRAPHY{SUF}.md', 'w').write('\n'.join(typo) + '\n')
    hdr = lambda title, note: [f'# {title}', '', note, '']
    if V2:
        for spk, name in (('ML', 'meilin'), ('DK', 'diane'), ('B1', 'customer')):
            open(f'docs/TRANSCRIPT-{name}-v2.md', 'w').write('\n'.join([f'# {WHO[spk]}', '', f"AI voice: ElevenLabs v3 '{VOICE[spk]}'. AI-generated likeness; on-camera lines lip-synced with sync-lipsync v2. A dramatization, not a real statement.", ''] + by_spk.get(spk, [])) + '\n')
        print('docs written; running time', tc(t)); return
    open('docs/TRANSCRIPT-engineer.md', 'w').write('\n'.join(hdr('Engineer interview (dramatized)', f"Role: optical engineer. AI-generated character (gen/char/eng.png), AI voice (ElevenLabs v3 '{VOICE['ENG']}'), lip-synced with sync-lipsync v2 on the on-camera lines. Not a real person and not a real statement.") + eng) + '\n')
    open('docs/TRANSCRIPT-business.md', 'w').write('\n'.join(hdr('Business interviews (dramatized)', f"Roles: head of inference at an AI company (voice '{VOICE['B1']}') and infrastructure lead at a datacenter operator (voice '{VOICE['B2']}'). AI-generated characters and voices. Not real people, customers or endorsements; no customer data exists behind these lines.") + biz) + '\n')
    open('docs/NARRATION.md', 'w').write('\n'.join(hdr('Narration script', f"Narrator voice: ElevenLabs v3 '{VOICE['NAR']}' (AI).") + nar) + '\n')
    print('docs written; running time', tc(t))

if __name__ == '__main__': main()
