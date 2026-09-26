"""v4 spoken script. Three people: Mei-Lin Zhou (Chief Scientist, PHASER; AI-agent persona), Cole Mercer (CEO; AI-agent
persona) and one fictional customer. Mei-Lin's voice is a designed MiniMax voice; Cole and the customer use ElevenLabs v3.
Claims stay inside docs/CLAIMS.md: 0.26 ns per step and ~1/1000 of a chip's energy per multiply are modeled (the centre
overlay says so); no superlatives ("world's fastest"), no invented comparisons, valuations or awards."""
import json

MEILIN_VOICE = 'ttv-voice-2026092612350126-4CGv9LxO'  # fal-ai/minimax/voice-design, see gen/v4/voicedesign.json
VOICE = {'ML': 'minimax:' + MEILIN_VOICE, 'CM': 'Liam', 'C2': 'Laura'}
WHO = {'ML': 'Mei-Lin Zhou, Chief Scientist, PHASER (AI agent persona, dramatized)',
       'CM': 'Cole Mercer, CEO, TensaCo (AI agent persona, dramatized)',
       'C2': 'Head of platform, AI startup (fictional customer)'}
LINES = [
    # cold open: VO while the camera travels, then on camera
    ('m1', 'ML', "Every computer you've ever used works the same way. It pushes electrons through metal... and most of that energy just turns into heat."),
    ('m2', 'ML', "So we built one that computes with light."),
    # hero (the product-film register)
    ('h1', 'ML', "A singular idea. Four plates of etched glass. One beam of light."),
    ('h2', 'ML', "Each plate is fused silica, etched with four thousand and ninety-six pixels of phase. Each one, twenty microns across."),
    ('h3', 'ML', "Light crosses the stack, interferes with itself... and that interference is the arithmetic."),
    ('h4', 'ML', "One round trip is one step of the network. Two hundred and sixty picoseconds."),
    # energy per multiply, modeled at 10^6 optical modes: PHASER <= 0.001 pJ (0.06-1 fJ) vs H100 INT8 0.71 pJ and TPU v4 1.24 pJ
    # at chip level (phaser.tensaco.ai footnote 2) -> >= 710x and >= 1,240x; the film uses the conservative ends
    ('h5', 'ML', "And every multiply takes seven hundred times less energy than NVIDIA's H100. Twelve hundred times less than Google's TPU v4."),
    ('h6', 'ML', "All of it, in something smaller than a coffee cup. This is PHASER."),
    # the customer, then the CEO
    ('c1', 'C2', "They ran the same workload, and I honestly thought the dashboard was broken."),  # (v3)
    ('c2', 'C2', "I was like... [laughs] wait, that's our energy bill? That number's supposed to have another digit."),  # (v3)
    ('k1a', 'CM', "Here's the thing. Most of the energy in a chip goes into pushing charge through wire... and then pulling the heat back out of the room."),  # (v3, split)
    ('k1b', 'CM', "Light crossing glass barely loses anything. That's the whole trick."),  # (v3, split)
    # the explainer
    ('t1', 'ML', "Okay. Here's what's actually happening."),
    ('t2', 'ML', "Light is a wave. Every point in the beam has a brightness... and a phase: where it is in its cycle."),
    ('t3', 'ML', "Each pixel of the glass is etched a little deeper, or a little shallower. Deeper glass delays the light, and twists its phase."),
    ('t4', 'ML', "Downstream, all those twisted waves meet. Where they agree, they add. Where they don't, they cancel. That's a multiply and a sum, at every point, all at once."),
    ('t5', 'ML', "Four plates, one mirror, and back again. One step of a recurrent neural network, done by physics."),
    # planet
    ('k2', 'CM', "The strange thing about AI at this scale is that, eventually, the software problem becomes a power problem."),  # (v3)
    ('k4', 'CM', "Energy isn't an AI resource. [short pause] It's a civilization resource."),  # (v3)
    ('a1', 'CM', "Every era gets one shot at changing what the essential thing costs. Steam did it for muscle. Electricity did it for the night."),
    ('a2', 'CM', "PHASER isn't about light. It isn't even about chips. It's about what happens when thinking stops costing the Earth."),
    # ignition
    ('g1', 'ML', "For months it was a 3D-printed thing that only worked if you didn't breathe near it."),
    ('g2', 'ML', "Then one night, we were about to go home... and everything lined up. Every mirror. Every plate. Every micron."),
    ('g3', 'ML', "And the cavity ignited."),
    ('g4', 'ML', "It's the oldest trick there is. Line the stones up with the sun... and the light does the work."),
    ('g5', 'ML', "And for the first time, the light talked back."),
    # close
    ('k7', 'CM', "And now it's here. We're sharing it with the world, so more intelligence never has to mean more heat."),
    ('m12', 'ML', "We taught light to compute."),
]
REUSE = {'c1', 'c2', 'k1a', 'k1b', 'k2', 'k4'}  # recorded for v3 (gen/v3/vo)

if __name__ == '__main__':
    import shutil
    for i in REUSE: shutil.copy(f'gen/v3/vo/{i}.mp3', f'gen/v4/vo/{i}.mp3')
    jobs = []
    for i, s, t in LINES:
        if i in REUSE: continue
        if VOICE[s].startswith('minimax:'):
            jobs.append(dict(id='vo4-' + i, endpoint='fal-ai/minimax/speech-02-hd', out=f'gen/v4/vo/{i}',
                             payload=dict(text=t.replace('[laughs]', '(laughs)').replace('[short pause]', ''), output_format='url',
                                          voice_setting=dict(voice_id=VOICE[s][8:], speed=1.0, vol=1.0, pitch=0))))
        else:
            jobs.append(dict(id='vo4-' + i, endpoint='fal-ai/elevenlabs/tts/eleven-v3', out=f'gen/v4/vo/{i}', payload=dict(text=t, voice=VOICE[s], stability=0.5)))
    json.dump(jobs, open('gen/v4/vo.json', 'w'), indent=1)
