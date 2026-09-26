"""v3 spoken script. Mei-Lin Zhou (Chief Scientist, PHASER) and Cole Mercer (CEO) are TensaCo AI-agent personas; two
dramatized customers. All AI-generated voices. Lines marked (v2) reuse the v2 recordings."""
import json
VOICE = {'ML': 'Jessica', 'CM': 'Liam', 'B1': 'Eric', 'C2': 'Laura'}
WHO = {'ML': 'Mei-Lin Zhou, Chief Scientist, PHASER (AI agent persona, dramatized)',
       'CM': 'Cole Mercer, CEO, TensaCo (AI agent persona, dramatized)',
       'B1': 'Head of inference, AI company (dramatized customer)',
       'C2': 'Head of platform, AI startup (dramatized customer)'}
LINES = [
    ('m1', 'ML', "Every computer you've ever used works the same way. It pushes electrons through metal... and most of that energy just turns into heat."),  # (v2)
    ('m2', 'ML', "So we built one that computes with light."),  # (v2)
    ('m3', 'ML', "Honestly? The math was the easy part."),  # (v2)
    ('m4', 'ML', "Then you put four pieces of glass in a cavity... and a few microns is suddenly your whole afternoon."),  # (v2)
    ('m5', 'ML', "The first version technically worked. And by 'worked,' I mean... if you didn't breathe near it. [laughs]"),  # (v2)
    ('m6', 'ML', "Before the pre-seed, half of this was 3D-printed. [short pause] Now it's, like... a third."),  # (v2)
    ('m8', 'ML', "There was this night the camera image finally matched what the simulator said it should look like. And we just... stared at it."),  # (v2)
    ('c1', 'C2', "They ran the same workload, and I honestly thought the dashboard was broken."),
    ('b1', 'B1', "I didn't care that it was optical. I cared that it was fast."),  # (v1)
    ('c2', 'C2', "I was like... [laughs] wait, that's our energy bill? That number's supposed to have another digit."),
    ('k1', 'CM', "Here's the thing. Most of the energy in a chip goes into pushing charge through wire... and then pulling the heat back out of the room. Light crossing glass barely loses anything. That's the whole trick."),
    ('k2', 'CM', "The strange thing about AI at this scale is that, eventually, the software problem becomes a power problem."),
    ('k3', 'CM', "If every new unit of intelligence needs its own block of electricity, the bottleneck stops being algorithms."),
    ('m9', 'ML', "PHASER changes the slope of that curve."),  # (v2)
    ('k4', 'CM', "Energy isn't an AI resource. [short pause] It's a civilization resource."),
    ('k5', 'CM', "The question isn't whether we want more intelligence. We do. The question is what it has to consume."),
    ('m10', 'ML', "PHASER doesn't make energy unimportant."),  # (v2)
    ('m11', 'ML', "It makes computation ask for less of it."),  # (v2)
    ('m12', 'ML', "We taught light to compute."),  # (v2)
]
REUSE = {'m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm8', 'm9', 'm10', 'm11', 'm12', 'b1'}
if __name__ == '__main__':
    import shutil, os
    for i in REUSE: shutil.copy(f'gen/v2/vo/{i}.mp3', f'gen/v3/vo/{i}.mp3')
    jobs = [dict(id='vo3-' + i, endpoint='fal-ai/elevenlabs/tts/eleven-v3', out=f'gen/v3/vo/{i}', payload=dict(text=t, voice=VOICE[s], stability=0.5))
            for i, s, t in LINES if i not in REUSE]
    json.dump(jobs, open('gen/v3/vo.json', 'w'), indent=1)
