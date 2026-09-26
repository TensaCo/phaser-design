"""v3 edit — faster, one-shot cold open, one continuous product fly-through, customers then the CEO, a planet-scale pull-back,
a fast fluid gallery, a real climax and an iPhone-style signature. Cut to gen/v3/music/score-1.mp3 (2:56, eight sections):
darkness 0–12.5 · lights on/hero 12.5–48 · making it 48–84 · customers + CEO 84–110 · planet 110–134 · gallery 134–146 ·
climax 146–168 · signature 168–176; then a disclosure card.
Options as in edl_v2, plus xfade (frames of dissolve from the previous shot's last frame) and the 'sig' end frame."""
from script_v3 import LINES

MOD = 'modeled'
ML = ('Mei-Lin Zhou', 'Chief Scientist, PHASER', 'AI agent persona · dramatization · AI-generated')
CM = ('Cole Mercer', 'CEO, TensaCo', 'AI agent persona · dramatization · AI-generated')
V3, L3, V2, L2 = 'mp4:gen/v3/video/', 'mp4:gen/v3/ls/', 'mp4:gen/v2/video/', 'mp4:gen/v2/ls/'
FLY = 'png:gen/render/r3-fly'
DOF = dict(focus=1.0, strength=3.0)
CREDITS = ('Planned future product launch video, set on 14 November 2026. Dramatization: people, places and voices are AI-generated; '
           'Mei-Lin Zhou and Cole Mercer are TensaCo AI-agent personas; customers are fictional.',
           'PHASER performance figures are modeled in simulation, not measured. Sources: phaser.tensaco.ai/notes',
           'Score: ElevenLabs Music · Earth at night: NASA Black Marble · Stock footage: Pexels.')
G = dict(grade='world', amb='none', people=True, xfade=5, push=(1.0, 1.09), music=1.0)  # gallery shot defaults

EDL = [
    # ── DARKNESS → LIGHTS ON, one continuous shot 0:00–0:16 ─────────────────────────────────────────────────────────
    dict(id='A1', src=L3 + 'ls3-m1.mp4', dur=9.33, grade='doc', amb='crt', people=True, camera='breath', vx=0.5, lens=True,
         vo=[(0.3, 'm1', 'sync')], text=[(0.4, 3.2, 'slate', 'TENSACO · PHASER', '14 NOVEMBER 2026'), (3.6, 8.6, 'lower3', *ML)]),
    dict(id='A2', src=V3 + 'v3-ml-dark.mp4', dur=0.71, **{'in': 9.33}, grade='doc', amb='crt', people=True, camera='breath', vx=0.5),
    dict(id='A3', src=L3 + 'ls3-m2.mp4', dur=3.25, grade='doc', amb='crt', people=True, camera='breath', vx=0.5, vo=[(0.3, 'm2', 'sync')],
         sfx=[(0.3, 'riser'), (2.35, 'impact')]),
    dict(id='A4', src=V3 + 'v3-ml-lights.mp4', dur=1.8, **{'in': 3.25}, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True),
    # ── HERO: one fly-through 0:16–0:48 ─────────────────────────────────────────────────────────────────────────────
    dict(id='B1', src=FLY, dur=19.3, grade='studio', amb='studio', dof=DOF, sfx=[(0.2, 'optical'), (6.0, 'cavity'), (10.5, 'cavity_fast')],
         text=[(1.0, 4.6, 'line', 'The interference is the arithmetic.'),
               (5.4, 9.2, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD),
               (10.4, 14.2, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD),
               (15.2, 19.0, 'num', '≤ 0.001 pJ', 'per equivalent multiply, at a million optical modes', MOD + ' · today’s AI chips: ~1 pJ per multiply-accumulate')]),
    dict(id='B1b', src=FLY, dur=10.7, **{'in': 19.3}, grade='white', amb='studio_room', dof=DOF, labels=True, ink=True),
    dict(id='B2', src='png:gen/render/r2-studio-hero', dur=2.1, **{'in': 2.0}, grade='white', amb='studio_room', dof=dict(focus=1.0, strength=2.2), ink=True,
         text=[(0.1, 2.1, 'name', 'PHASER', 'left')]),
    # ── MAKING IT 0:48–1:24 ─────────────────────────────────────────────────────────────────────────────────────────
    dict(id='C1', src=L2 + 'ls-m3.mp4', dur=3.8, grade='white', amb='studio_room', people=True, camera='breath', vx=0.6, ink=True, vo=[(0.3, 'm3', 'sync')]),
    dict(id='C2', src='mp4:gen/video/v-e2.mp4', dur=7.2, speed=0.69, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55,
         vo=[(0.1, 'm4')], sfx=[(1.3, 'click'), (4.2, 'click')], rack=True),
    dict(id='C3', src=L2 + 'ls-m5.mp4', dur=8.4, grade='doc', amb='garage', people=True, camera='handheld', vx=0.6, vo=[(0.3, 'm5', 'sync')]),
    dict(id='C4', src='mp4:gen/video/v-e4.mp4', dur=7.1, speed=0.69, grade='doc', amb='garage', people=True, camera='handheld', vx=0.45, vo=[(0.2, 'm6')]),
    dict(id='C5', src=V2 + 'v2-monitor.mp4', dur=9.5, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55, vo=[(0.4, 'm8')]),
    # ── CUSTOMERS, THEN THE CEO 1:24–1:52 ──────────────────────────────────────────────────────────────────────────
    dict(id='D1', src=L3 + 'ls3-c1.mp4', dur=4.8, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True, vo=[(0.3, 'c1', 'sync')],
         text=[(0.3, 4.7, 'lower3', 'Head of platform, AI startup', 'Customer', 'dramatization · AI-generated')]),
    dict(id='D2', src=L2 + 'ls-b1.mp4', dur=3.6, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True, vo=[(0.3, 'b1', 'sync')],
         text=[(0.2, 3.5, 'lower3', 'Head of inference, AI company', 'Customer', 'dramatization · AI-generated', 'top')]),
    dict(id='D3', src=L3 + 'ls3-c2.mp4', dur=6.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True, vo=[(0.3, 'c2', 'sync')],
         text=[(0.4, 5.9, 'note', 'Dramatization. PHASER energy figures are modeled.')]),
    dict(id='D4', src=L3 + 'ls3-k1a.mp4', dur=9.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.35, ink=True, vo=[(0.3, 'k1a', 'sync')],
         text=[(0.4, 5.0, 'lower3', *CM, 'top')]),
    dict(id='D5', src=L3 + 'ls3-k1b.mp4', dur=4.6, grade='white', amb='studio_room', people=True, camera='breath', vx=0.45, ink=True, vo=[(0.3, 'k1b', 'sync')]),
    # ── PLANET 1:52–2:14 ────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='E1', src='png:gen/render/r3-globe', dur=10.0, grade='space', amb='space', vo=[(0.4, 'k2')],
         text=[(5.6, 9.9, 'num', '~945 TWh', 'data-centre electricity use by 2030: more than Japan uses today', 'IEA, Energy and AI (2025) · projection')]),
    dict(id='E2', src=V3 + 'v3-dc-campus.mp4', dur=3.6, grade='world', amb='wind', camera='dolly', vx=0.5, vo=[(0.2, 'k3')], xfade=4),
    dict(id='E3', src=V3 + 'v3-grid.mp4', dur=3.0, grade='world', amb='wind', camera='dolly', vx=0.5, xfade=4),
    dict(id='E4', src=V3 + 'v3-plant.mp4', dur=2.4, grade='world', amb='wind', camera='dolly', vx=0.5, xfade=4),
    dict(id='E5', src='png:gen/render/r-multiplex', dur=3.0, **{'in': 2.8}, grade='studio', amb='studio', vo=[(0.0, 'm9')]),
    # ── GALLERY 2:14–2:26: fast and fluid ──────────────────────────────────────────────────────────────────────────
    dict(id='F1', src='mp4:gen/video/v-hospital.mp4', dur=1.35, **{'in': 0.5}, vo=[(0.3, 'k4')], vx=0.4, **G),
    dict(id='F2', src='mp4:gen/video/v-water.mp4', dur=1.15, **{'in': 1.0}, vx=0.35, **G),
    dict(id='F3', src='mp4:gen/video/v-greenhouse.mp4', dur=1.15, **{'in': 1.0}, vx=0.5, **G),
    dict(id='F4', src='mp4:gen/video/v-cold.mp4', dur=1.1, **{'in': 1.0}, vx=0.6, **G),
    dict(id='F5', src='mp4:gen/video/v-grocery.mp4', dur=1.1, **{'in': 1.2}, vx=0.55, **G),
    dict(id='F6', src='mp4:gen/video/v-home.mp4', dur=1.15, **{'in': 1.0}, vx=0.7, **G),
    dict(id='F7', src='mp4:gen/video/v-steel.mp4', dur=1.15, **{'in': 0.8}, vx=0.45, **G),
    dict(id='F8', src='mp4:gen/video/v-icu.mp4', dur=1.05, **{'in': 1.0}, vx=0.6, **G),
    dict(id='F9', src=V3 + 'v3-city.mp4', dur=1.2, **{'in': 1.5}, vx=0.5, **dict(G, people=False)),
    dict(id='F10', src='mp4:gen/video/v-rack.mp4', dur=1.5, **{'in': 1.0}, vx=0.5, **dict(G, people=False)),
    # ── CLIMAX 2:26–2:48 ────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='G1', src=L3 + 'ls3-k5.mp4', dur=7.6, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True,
         vo=[(0.3, 'k5', 'sync')], sfx=[(0.0, 'impact')]),
    dict(id='G2', src=FLY, dur=1.4, **{'in': 13.6}, grade='studio', amb='studio', dof=DOF),
    dict(id='G3', src=L2 + 'ls-m10.mp4', dur=3.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.48, ink=True, vo=[(0.3, 'm10', 'sync')]),
    dict(id='G4', src='png:gen/render/r-thesis', dur=4.2, grade='studio', amb='studio', vo=[(0.2, 'm11')],
         text=[(1.0, 4.1, 'num', '200–3,000×', 'less energy per step than an equally capable dense recurrent network', MOD + ' at a million optical modes')]),
    dict(id='G5', src=FLY, dur=1.2, **{'in': 24.0}, grade='white', amb='studio_room', dof=DOF, ink=True),
    dict(id='G6', src='png:gen/render/r3-globe', dur=1.0, **{'in': 7.5}, grade='space', amb='space'),
    dict(id='G7', src=L2 + 'ls-m12.mp4', dur=2.6, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.4, 'm12', 'sync')]),
    dict(id='G8', src='black', dur=1.0, amb='none', lens=False, sfx=[(0.0, 'impact')]),
    # ── SIGNATURE 2:48–2:56, then the disclosure card ─────────────────────────────────────────────────────────────
    dict(id='H1', src='sig', dur=8.0, amb='none', lens=False, sfx=[(0.5, 'optical')]),
    dict(id='H2', src='black', dur=3.6, amb='none', lens=False, text=[(0.2, 3.5, 'credits', *CREDITS)]),
]

SHORT = [(0.15, 2.0, 'credits', 'Planned future product launch video. Dramatization, AI-generated. Figures are modeled in simulation, not measured.')]
CUTS = {
    'cut60': [('A1', {}), ('A2', {}), ('A3', {}), ('A4', {}), ('B1', dict(dur=16.0, **{'in': 4.0}, text=[(1.4, 5.2, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD), (6.4, 10.2, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)])),
              ('D3', {}), ('D5', {}), ('G3', {}), ('G4', {}), ('G7', {}), ('G8', {}), ('H1', {}), ('H2', dict(dur=2.6, text=SHORT))],
    'cut30': [('A3', {}), ('A4', {}), ('B1', dict(dur=11.3, **{'in': 8.0}, text=[(2.0, 6.0, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)])), ('G7', {}), ('G8', {}), ('H1', dict(dur=6.0)), ('H2', dict(dur=2.3, text=SHORT))],
    'cut15': [('B1b', dict(dur=6.0, **{'in': 21.0})), ('G7', {}), ('H1', dict(dur=4.8)), ('H2', dict(dur=1.8, text=SHORT))],
}

META = dict(vo_dir='gen/v3/vo', speakers={**{i: s for i, s, _ in LINES}, 'k1a': 'CM', 'k1b': 'CM'}, score='gen/v3/music/score-1.mp3', score_db=-3.0,
            score_automation=[(0, -14), (10.8, -12), (12.3, 0), (48, -1.5), (84, -1.5), (110, 0), (176, 0)],
            stems_dir='out/stems-v3', tag='v3-')
CUTS['cuttest'] = [('B1', dict(dur=2.0, **{'in': 17.3}, text=[])), ('B1b', {}), ('H1', {})]
