"""v2 edit: cut to the composed score (gen/v2/music/score-1.mp3, 3:28, seven sections), then a disclosure card.
Sections: cold open 0–17 · hero 17–60 · intimate middle 60–120 · build 120–150 · human 150–174 · climax 174–196 · end 196–208.
Clip options as in edl.py, plus: camera (handheld | breath | dolly), dof {focus, strength}, rack, ink (dark type on the
white studio), labels (exploded-view annotations projected from the render's camera). VO entries marked 'sync' are
on-camera (lip-synced); the rest are voice-over. Every PHASER figure carries 'modeled'."""
from script_v2 import LINES

MOD = 'modeled'
ML_TAG = ('Mei-Lin Zhou', 'Chief Scientist, PHASER', 'AI agent persona · dramatization · AI-generated')
DK_TAG = ('Diane Kowalski', 'CEO, TensaCo', 'AI agent persona · dramatization · AI-generated')
END = lambda t0, t1: [(t0, t1, 'end', 'PHASER', 'A neural accelerator that runs at the speed of light.', 'Now live  ·  phaser.tensaco.ai')]
CREDITS = ('Planned future product launch video, set on 14 November 2026. Dramatization: people, places and voices are AI-generated; '
           'Mei-Lin Zhou and Diane Kowalski are TensaCo AI-agent personas.',
           'PHASER performance figures are modeled in simulation, not measured. Sources: phaser.tensaco.ai/notes',
           'Score: ElevenLabs Music. SuperMUC footage: IBM Research, CC BY 3.0, via Wikimedia Commons. Stock footage: Pexels.')
V, G = 'mp4:gen/v2/video/', 'mp4:gen/v2/ls/'
DOF = dict(focus=1.0, strength=3.0)

EDL = [
    # ── COLD OPEN 0:00–0:17 ──────────────────────────────────────────────────────────────────────────────────────────
    dict(id='A1', src='black', dur=1.6, amb='none', lens=False, text=[(0.2, 1.5, 'slate', 'TENSACO · PHASER', '14 NOVEMBER 2026')]),
    dict(id='A2', src='png:gen/viz/electrons', dur=6.6, grade='viz', amb='elec', push=(1.0, 1.04), vo=[(0.4, 'm1')],
         text=[(2.2, 6.4, 'line', 'Intelligence runs on electrons.')]),
    dict(id='A3', src='mp4:gen/video/v-cooling.mp4', dur=1.2, **{'in': 1.0}, grade='doc', amb='fans', camera='handheld', vx=0.45),
    dict(id='A4', src='black', dur=1.2, amb='none', lens=False),
    dict(id='A5', src=G + 'ls-m2.mp4', dur=3.4, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True,
         vo=[(0.3, 'm2', 'sync')], text=[(0.4, 3.3, 'lower3', *ML_TAG)]),
    dict(id='A6', src='black', dur=3.0, amb='none', lens=False, text=[(0.3, 2.8, 'line', 'PHASER runs it on light.')]),
    # ── HERO 0:17–1:00 ──────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='B1', src='png:gen/render/r-firstlight', dur=3.5, grade='studio', amb='studio', sfx=[(0.0, 'optical')]),
    dict(id='B2', src='png:gen/render/r2-assemble', dur=6.5, grade='studio', amb='studio', dof=DOF, sfx=[(5.6, 'click')]),
    dict(id='B3', src='png:gen/render/r-plate', dur=4.5, grade='studio', amb='studio', text=[(0.6, 4.4, 'line', 'The interference is the arithmetic.')]),
    dict(id='B4', src='png:gen/render/r-roundtrip', dur=5.0, grade='studio', amb='studio', sfx=[(0.1, 'cavity')],
         text=[(2.6, 4.95, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD)]),
    dict(id='B5', src='png:gen/render/r-multiplex', dur=5.0, grade='studio', amb='studio', sfx=[(0.1, 'cavity_fast')],
         text=[(1.8, 4.95, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)]),
    dict(id='B6', src='png:gen/render/r-energy', dur=5.0, grade='studio', amb='studio',
         text=[(0.4, 4.9, 'num', '≤ 0.001 pJ', 'per equivalent multiply, at a million optical modes', MOD + ' · today’s AI chips: ~1 pJ per multiply-accumulate')]),
    dict(id='B7', src='png:gen/render/r2-studio-hero', dur=5.5, grade='white', amb='studio_room', dof=dict(focus=1.0, strength=2.2), ink=True,
         text=[(1.4, 5.4, 'name', 'PHASER', 'left')]),
    dict(id='B8', src='png:gen/render/r2-studio-explode', dur=8.0, grade='white', amb='studio_room', dof=dict(focus=1.0, strength=3.0), ink=True, labels=True),
    # ── INTIMATE MIDDLE 1:00–2:00 ───────────────────────────────────────────────────────────────────────────────────
    dict(id='C1', src=V + 'v2-studio-wide.mp4', dur=2.0, grade='white', amb='studio_room', camera='dolly', vx=0.55),
    dict(id='C2', src=G + 'ls-m3.mp4', dur=3.8, grade='white', amb='studio_room', people=True, camera='breath', vx=0.6, ink=True, vo=[(0.3, 'm3', 'sync')]),
    dict(id='C3', src='mp4:gen/video/v-e2.mp4', dur=7.2, speed=0.69, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55,
         vo=[(0.1, 'm4')], sfx=[(1.3, 'click'), (4.2, 'click')], rack=True),
    dict(id='C4', src=G + 'ls-m5.mp4', dur=8.4, grade='doc', amb='garage', people=True, camera='handheld', vx=0.6, vo=[(0.3, 'm5', 'sync')]),
    dict(id='C5', src='mp4:gen/video/v-e4.mp4', dur=7.1, speed=0.69, grade='doc', amb='garage', people=True, camera='handheld', vx=0.45, vo=[(0.2, 'm6')]),
    dict(id='C6', src=V + 'v2-wide.mp4', dur=1.3, grade='doc', amb='garage', people=True, camera='handheld', vx=0.65),
    dict(id='C7', src=V + 'v2-monitor.mp4', dur=9.5, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55, vo=[(0.4, 'm8')]),
    dict(id='C8', src=V + 'v2-bench-night.mp4', dur=3.0, grade='doc', amb='garage', people=True, camera='handheld', vx=0.4),
    dict(id='C9', src=G + 'ls-d1.mp4', dur=6.8, grade='white', amb='studio_room', people=True, camera='breath', vx=0.35, ink=True,
         vo=[(0.3, 'd1', 'sync')], text=[(0.3, 6.3, 'lower3', *DK_TAG)]),
    dict(id='C10', src=G + 'ls-d2.mp4', dur=5.6, grade='white', amb='studio_room', people=True, camera='breath', vx=0.45, ink=True,
         vo=[(0.3, 'd2', 'sync')], text=[(0.4, 5.9, 'note', 'Dramatization. PHASER energy figures are modeled.')]),
    dict(id='C11', src=G + 'ls-b1.mp4', dur=5.3, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True,
         vo=[(0.3, 'b1', 'sync')], text=[(0.3, 4.9, 'lower3', 'Head of inference, AI company', 'Customer', 'dramatization · AI-generated', 'top')]),
    # ── BUILD 2:00–2:30 ─────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='D1', src='mp4:gen/video/v-b7.mp4', dur=6.8, speed=0.73, grade='doc', amb='office', people=True, camera='handheld', vx=0.45, vo=[(0.2, 'd3')]),
    dict(id='D2', src='mp4:gen/video/v-rack.mp4', dur=6.0, speed=0.83, grade='world', amb='datacenter', camera='dolly', vx=0.5, vo=[(0.2, 'd4')]),
    dict(id='D3', src='mp4:gen/video/v-transformer.mp4', dur=6.0, speed=0.83, grade='world', amb='transformer', vx=0.62, vo=[(1.8, 'd5')],
         text=[(3.2, 5.9, 'num', '128 weeks', 'to get a large power transformer', 'Wood Mackenzie, 2025')]),
    dict(id='D4', src='mp4:assets/stock/substation-yard-orig.mp4', dur=3.8, **{'in': 1.0}, grade='world', amb='transformer', vx=0.5, vo=[(0.2, 'd6')]),
    dict(id='D5', src='mp4:assets/stock/transmission-lines-orig.mp4', dur=3.2, **{'in': 8.0}, grade='world', amb='wind', vx=0.5),
    dict(id='D6', src='png:gen/render/r-multiplex', dur=4.2, **{'in': 2.0}, grade='studio', amb='studio', vo=[(0.3, 'm9')]),
    # ── HUMAN STAKES 2:30–2:54 ──────────────────────────────────────────────────────────────────────────────────────
    dict(id='E1', src='mp4:assets/stock/substation-crew-orig.mp4', dur=3.0, **{'in': 3.0}, grade='world', amb='wind', vx=0.5, vo=[(0.3, 'd7')]),
    dict(id='E2', src='mp4:assets/stock/cooling-towers-river-orig.mp4', dur=2.8, **{'in': 12.0}, grade='world', amb='wind', vx=0.5),
    dict(id='E3', src='mp4:gen/video/v-hospital.mp4', dur=3.2, grade='world', amb='hospital', people=True, vx=0.4, vo=[(0.5, 'd7a')]),
    dict(id='E4', src='mp4:gen/video/v-water.mp4', dur=2.6, grade='world', amb='pumps', vx=0.35, vo=[(0.4, 'd7b')]),
    dict(id='E5', src='mp4:gen/video/v-greenhouse.mp4', dur=2.2, grade='world', amb='refrigeration', people=True, vx=0.5, vo=[(0.3, 'd7c')]),
    dict(id='E6', src='mp4:gen/video/v-grocery.mp4', dur=2.0, grade='world', amb='store', people=True, vx=0.55),
    dict(id='E7', src='mp4:gen/video/v-home.mp4', dur=2.4, grade='world', amb='wind', vx=0.7, vo=[(0.4, 'd7d')]),
    dict(id='E8', src='mp4:gen/video/v-steel.mp4', dur=2.4, grade='world', amb='steel', people=True, vx=0.45, vo=[(0.3, 'd7e')]),
    dict(id='E9', src='mp4:assets/stock/datacenter-supermuc.mp4', dur=3.4, grade='world', amb='datacenter', people=True, vx=0.5, vo=[(0.3, 'd7f')]),
    # ── CLIMAX 2:54–3:16 ────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='F1', src=G + 'ls-d8.mp4', dur=7.5, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.3, 'd8', 'sync')]),
    dict(id='F2', src=G + 'ls-m10.mp4', dur=3.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.48, ink=True, vo=[(0.3, 'm10', 'sync')]),
    dict(id='F3', src='png:gen/render/r-thesis', dur=5.0, grade='studio', amb='studio', vo=[(0.2, 'm11')],
         text=[(1.5, 4.9, 'num', '200–3,000×', 'less energy per step than an equally capable dense recurrent network', MOD + ' at a million optical modes')]),
    dict(id='F4', src='mp4:gen/video/v-city.mp4', dur=3.0, speed=0.8, grade='world', amb='city', vx=0.5),
    dict(id='F5', src=G + 'ls-m12.mp4', dur=3.5, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.4, 'm12', 'sync')]),
    # ── END 3:16–3:28, then the disclosure card ─────────────────────────────────────────────────────────────────────
    dict(id='G1', src='png:gen/render/r-end', dur=12.0, grade='studio', amb='studio', sfx=[(0.5, 'optical'), (10.4, 'optical_soft')], text=END(4.0, 12.0), fadeout=1.2),
    dict(id='G2', src='black', dur=4.4, amb='none', lens=False, text=[(0.3, 4.3, 'credits', *CREDITS)]),
]

SHORT = [(0.15, 2.0, 'credits', 'Planned future product launch video. Dramatization, AI-generated. Figures are modeled in simulation, not measured.')]
CUTS = {
    'cut60': [('A5', {}), ('A6', dict(dur=2.4, text=[(0.2, 2.3, 'line', 'PHASER runs it on light.')])), ('B1', dict(dur=2.8)), ('B2', {}),
              ('B5', {}), ('B7', {}), ('C2', {}), ('C3', {}), ('C10', {}), ('F2', {}), ('F3', {}), ('F5', {}), ('G1', dict(dur=7.5, **{'in': 3.0}, text=END(1.0, 7.5))), ('G2', dict(dur=3.6))],
    'cut30': [('B1', dict(dur=2.6)), ('B2', {}), ('B4', {}), ('B5', {}), ('B7', {}), ('F5', {}), ('G1', dict(dur=5.0, **{'in': 6.0}, text=END(0.2, 5.0))), ('G2', dict(dur=2.6, text=SHORT))],
    'cut15': [('B2', dict(dur=5.0, **{'in': 1.5})), ('B5', dict(dur=3.4, **{'in': 1.6}, text=[(0.2, 3.35, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)])),
              ('G1', dict(dur=4.6, **{'in': 6.4}, text=END(0.2, 4.6))), ('G2', dict(dur=2.0, text=SHORT))],
}

META = dict(vo_dir='gen/v2/vo', speakers={i: s for i, s, _ in LINES}, score='gen/v2/music/score-1.mp3', score_db=-3.0,
            stems_dir='out/stems-v2', tag='v2-')

CUTS['cuttest'] = [('B2', {}), ('B7', {}), ('B8', {})]
