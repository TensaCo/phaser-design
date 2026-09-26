"""Lip-sync jobs for v2: each talking take gets one voice line (0.3 s head pad, 0.5 s tail pad)."""
import json, os, subprocess
FF = 'src/ffmpeg'
PAIRS = {'ls-m2': ('v2-ml-cu-a', 'm2'), 'ls-m12': ('v2-ml-cu-b', 'm12'), 'ls-m10': ('v2-ml-mcu', 'm10'), 'ls-m3': ('v2-ml-34', 'm3'),
         'ls-m5': ('v2-laugh', 'm5'), 'ls-d1': ('v2-dk-34', 'd1'), 'ls-d2': ('v2-dk-cu', 'd2'), 'ls-d8': ('v2-dk-direct', 'd8'),
         'ls-b1': ('v2-b1', 'b1')}
os.makedirs('gen/v2/ls', exist_ok=True); jobs = []
for out, (vid, line) in PAIRS.items():
    v, a = f'gen/v2/ls/{vid}-small.mp4', f'gen/v2/ls/{line}.wav'
    if not os.path.exists(v): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v2/video/{vid}.mp4', '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '20', '-an', v], check=True)
    if not os.path.exists(a): subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f'gen/v2/vo/{line}.mp3', '-af', 'adelay=300|300,apad=pad_dur=0.5', a], check=True)
    jobs.append(dict(id=out, endpoint='fal-ai/sync-lipsync/v2', out=f'gen/v2/ls/{out}', payload=dict(video_url='@upload:' + v, audio_url='@upload:' + a, sync_mode='cut_off')))
json.dump(jobs, open('gen/v2/ls.json', 'w'), indent=1)
