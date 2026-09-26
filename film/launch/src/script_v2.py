"""v2 spoken script. No anonymous narrator: TensaCo's Mei-Lin Zhou (Chief Scientist, PHASER) and Diane Kowalski (CEO)
carry the film, plus one dramatized customer. All three are AI-generated dramatizations (Mei-Lin and Diane are TensaCo's
AI-agent personas; see tensaco.ai/company/leadership). Every line is voiced by an AI voice."""
import json

VOICE = {'ML': 'Jessica', 'DK': 'Sarah', 'B1': 'Eric'}
WHO = {'ML': 'Mei-Lin Zhou, Chief Scientist, PHASER (AI agent persona, dramatized)',
       'DK': 'Diane Kowalski, CEO, TensaCo (AI agent persona, dramatized)',
       'B1': 'Head of inference, AI company (dramatized customer)'}
LINES = [
    # cold open (VO over black and the lattice)
    ('m1', 'ML', "Every computer you've ever used works the same way. It pushes electrons through metal... and most of that energy just turns into heat."),
    # to camera, white studio
    ('m2', 'ML', "So we built one that computes with light."),
    # middle: the build
    ('m3', 'ML', "Honestly? The math was the easy part."),
    ('m4', 'ML', "Then you put four pieces of glass in a cavity... and a few microns is suddenly your whole afternoon."),
    ('m5', 'ML', "The first version technically worked. And by 'worked,' I mean... if you didn't breathe near it. [laughs]"),
    ('m6', 'ML', "Before the pre-seed, half of this was 3D-printed. [short pause] Now it's, like... a third."),
    ('m8', 'ML', "There was this night the camera image finally matched what the simulator said it should look like. And we just... stared at it."),
    # the people who use it
    ('d1', 'DK', "The first time a customer ran their real workload on it, their head of infrastructure thought the dashboard was broken."),
    ('d2', 'DK', "She made us run it again. [laughs] Then she asked if that was really the energy number."),
    ('b1', 'B1', "I didn't care that it was optical. I cared that it was fast."),
    # the bottleneck moves outward
    ('d3', 'DK', "That's when the question changes. Not: can light compute? But: what happens when it does?"),
    ('d4', 'DK', "The strange thing about AI at this scale is that, eventually, the software problem becomes a power problem."),
    ('d5', 'DK', "You end up arguing about transformers."),
    ('d6', 'DK', "If every new unit of intelligence needs its own block of electricity, the bottleneck stops being algorithms."),
    ('m9', 'ML', "PHASER changes the slope of that curve."),
    # human stakes
    ('d7', 'DK', "Energy isn't an AI resource. [short pause] It's a civilization resource."),
    ('d7a', 'DK', "It runs hospitals."),
    ('d7b', 'DK', "It moves water."),
    ('d7c', 'DK', "It grows, cools and carries food."),
    ('d7d', 'DK', "It heats homes."),
    ('d7e', 'DK', "It builds things."),
    ('d7f', 'DK', "And increasingly, it runs intelligence."),
    # climax
    ('d8', 'DK', "The question isn't whether we want more intelligence. We do. The question is what it has to consume."),
    ('m10', 'ML', "PHASER doesn't make energy unimportant."),
    ('m11', 'ML', "It makes computation ask for less of it."),
    ('m12', 'ML', "We taught light to compute."),
]

if __name__ == '__main__':
    jobs = [dict(id='vo2-' + i, endpoint='fal-ai/elevenlabs/tts/eleven-v3', out=f'gen/v2/vo/{i}',
                 payload=dict(text=t, voice=VOICE[s], stability=0.5)) for i, s, t in LINES if not (i == 'b1')]
    json.dump(jobs, open('gen/v2/vo.json', 'w'), indent=1)
