"""The spoken script. Every line is a dramatized role (fictional characters, AI voices) except the narrator."""
import json
VOICE = {'NAR': 'Brian', 'ENG': 'Jessica', 'B1': 'Eric', 'B2': 'Matilda'}
LINES = [
 # act 3 — the engineer (dramatized)
 ('e1', 'ENG', "Honestly? The math was the easy part."),
 ('e2', 'ENG', "Then you put four pieces of glass in a cavity... and a few microns is suddenly your whole afternoon."),
 ('e3', 'ENG', "The first version technically worked. And by 'worked,' I mean... if you didn't breathe near it. [laughs]"),
 ('e4', 'ENG', "Every pass through the cavity is one recurrent step. Which is beautiful, mathematically. But it also means every tiny error gets another chance to matter."),
 ('e5', 'ENG', "Before the pre-seed, half of this was 3D-printed. [short pause] Now it's, like... a third."),
 ('e6', 'ENG', "There was this night the camera image finally matched what the simulator said it should look like. And we just... stared at it for a while."),
 ('e7', 'ENG', "Getting from that to something you can turn on, calibrate, and run again tomorrow... that was most of the engineering."),
 # act 4 bridge
 ('n1', 'NAR', "Once the machine worked, the question changed. Not: can light compute? But: what happens when it does?"),
 # act 4 — business (dramatized)
 ('b1', 'B1', "I didn't care that it was optical. I cared that it was fast."),
 ('b2', 'B2', "They ran the same workload, and I honestly thought the dashboard was broken."),
 ('b3', 'B2', "I was like... [laughs] wait, that's our energy bill? That number's supposed to have another digit."),
 ('b4', 'B1', "We used to treat inference like a budget. How many times can we afford to call the model? Now the conversation is: how often do we want to?"),
 ('b5', 'B2', "After a week, waiting two hundred milliseconds felt broken."),
 # act 5
 ('n2', 'NAR', "The strange thing about computing at this scale is that, eventually, the software problem becomes a power problem."),
 ('b6', 'B2', "You start arguing about transformers."),
 ('n3', 'NAR', "If every new unit of intelligence needs its own block of electricity, the bottleneck stops being algorithms."),
 ('n4', 'NAR', "PHASER changes the slope of that curve."),
 # act 6
 ('n5', 'NAR', "Energy isn't an AI resource."),
 ('n6', 'NAR', "It's a civilization resource."),
 ('n7', 'NAR', "It runs hospitals."),
 ('n8', 'NAR', "It moves water."),
 ('n9', 'NAR', "It grows, cools and carries food."),
 ('n10', 'NAR', "It heats homes."),
 ('n11', 'NAR', "It builds things."),
 ('n12', 'NAR', "And increasingly, it runs intelligence."),
 # act 7
 ('n13', 'NAR', "The question isn't whether we want more intelligence. We do. The question is what it has to consume."),
 ('n14', 'NAR', "PHASER doesn't make energy unimportant."),
 ('n15', 'NAR', "It makes computation ask for less of it."),
 ('n16', 'NAR', "We built Phaser, so that more intelligence doesn't have to mean more heat."),
]
if __name__ == '__main__':
    jobs = [dict(id='vo-' + i, endpoint='fal-ai/elevenlabs/tts/eleven-v3', out=f'gen/vo/{i}',
                 payload=dict(text=t, voice=VOICE[s], stability=0.5)) for i, s, t in LINES]
    json.dump(jobs, open('gen/vo.json', 'w'), indent=1)
