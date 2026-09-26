"""Lip-sync jobs for v4 (0.3 s head pad, 0.5 s tail pad)."""
import json, os, subprocess
FF = 'src/ffmpeg'
PAIRS = {'ls4-m2': ('v4-lights', 'm2'), 'ls4-t1': ('v4-ml-34', 't1'), 'ls4-t5': ('v4-ml-cu-a', 't5'), 'ls4-m12': ('v4-ml-cu-b', 'm12'),
         'ls4-k1a': ('v4-cole-34', 'k1a'), 'ls4-k1b': ('v4-cole-cu-a', 'k1b'), 'ls4-k7': ('v4-cole-cu-b', 'k7')}
os.makedirs('gen/v4/ls', exist_ok=True); jobs = []
for out, (vid, line) in PAIRS.items():
    v, a = f'gen/v4/ls/{vid}-small.mp4', f'gen/v4/ls/{line}.wav'
    if not os.path.exists(v): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v4/video/{vid}.mp4', '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '18', '-an', v], check=True)
    if not os.path.exists(a): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v4/vo/{line}.mp3', '-af', 'adelay=300|300,apad=pad_dur=0.5', a], check=True)
    jobs.append(dict(id=out, endpoint='fal-ai/sync-lipsync/v2', out=f'gen/v4/ls/{out}', payload=dict(video_url='@upload:' + v, audio_url='@upload:' + a, sync_mode='cut_off')))
json.dump(jobs, open('gen/v4/ls.json', 'w'), indent=1)
