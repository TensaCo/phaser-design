"""Lip-sync jobs for v3 (0.3 s head pad, 0.5 s tail pad)."""
import json, os, subprocess
FF = 'src/ffmpeg'
PAIRS = {'ls3-m1': ('v3-ml-dark', 'm1'), 'ls3-m2': ('v3-ml-lights', 'm2'), 'ls3-c1': ('v3-cust2', 'c1'), 'ls3-c2': ('v3-cust2-b', 'c2'),
         'ls3-k1a': ('v3-cole-34', 'k1a'), 'ls3-k1b': ('v3-cole-direct-a', 'k1b'), 'ls3-k5': ('v3-cole-direct-b', 'k5')}
os.makedirs('gen/v3/ls', exist_ok=True); jobs = []
for out, (vid, line) in PAIRS.items():
    v, a = f'gen/v3/ls/{vid}-small.mp4', f'gen/v3/ls/{line}.wav'
    if not os.path.exists(v): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v3/video/{vid}.mp4', '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '18', '-an', v], check=True)
    if not os.path.exists(a): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v3/vo/{line}.mp3', '-af', 'adelay=300|300,apad=pad_dur=0.5', a], check=True)
    jobs.append(dict(id=out, endpoint='fal-ai/sync-lipsync/v2', out=f'gen/v3/ls/{out}', payload=dict(video_url='@upload:' + v, audio_url='@upload:' + a, sync_mode='cut_off')))
json.dump(jobs, open('gen/v3/ls.json', 'w'), indent=1)
