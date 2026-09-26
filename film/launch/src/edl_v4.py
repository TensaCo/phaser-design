"""v4 edit. Three people (Mei-Lin, one customer, Cole). No text on screen except what is being said at that moment
("0.26 ns", "700×", "1,200×", "PHASER") and name + title lower thirds. Every disclosure lives in the centre overlay
(PLANNED FUTURE PRODUCT LAUNCH VIDEO · AI-GENERATED · FIGURES MODELED) and in the small print at the end.
Music is assembled in audio_v4.py from three composed cues (hero / tech / end) against the clip ids below."""
from script_v4 import LINES

V4, L4, R4 = 'mp4:gen/v4/video/', 'mp4:gen/v4/ls/', 'png:gen/v4/render/'
FLY = 'png:gen/render/r3-fly'
DOF = dict(focus=1.0, strength=3.0)
ML = ('Mei-Lin Zhou', 'Chief Scientist, PHASER')
CM = ('Cole Mercer', 'CEO, TensaCo')
SMALL_PRINT = ('PLANNED FUTURE PRODUCT LAUNCH VIDEO, SET ON 14 NOVEMBER 2026. DRAMATIZATION: ALL PEOPLE, PLACES AND VOICES ARE AI-GENERATED. '
               'MEI-LIN ZHOU AND COLE MERCER ARE TENSACO AI-AGENT PERSONAS; THE CUSTOMER IS FICTIONAL. PHASER HAS NOT YET BEEN BUILT OR MEASURED.',
               'PERFORMANCE FIGURES ARE MODELED IN SIMULATION: 0.26 NS PER ROUND TRIP; ≤ 0.001 PJ PER EQUIVALENT MULTIPLY, EXTRAPOLATED TO 10⁶ OPTICAL MODES, '
               'VS NVIDIA H100 INT8 ≈ 0.71 PJ AND GOOGLE TPU V4 ≈ 1.24 PJ PER MULTIPLY-ACCUMULATE AT CHIP LEVEL. NVIDIA, H100, GOOGLE AND TPU ARE TRADEMARKS OF THEIR OWNERS.',
               'SOURCES: PHASER.TENSACO.AI/NOTES · MUSIC: ELEVENLABS MUSIC · EARTH AT NIGHT: NASA BLACK MARBLE.')
TL = dict(grade='world', amb='none', xfade=3, push=(1.0, 1.06), vx=0.5)  # time-lapse montage shots
BIG = lambda t0, t1, s: (t0, t1, 'big', s)

EDL = [
    # ── COLD OPEN: one camera move, CRT → PHASER → Mei-Lin; lights on at "light" ──────────────────────────────────
    dict(id='A1', src=V4 + 'v4-cold-move.mp4', dur=10.04, grade='doc', amb='crt', people=True, camera='dolly', vx=0.5, vo=[(0.6, 'm1')]),
    dict(id='A2', src=L4 + 'ls4-m2.mp4', dur=3.8, grade='doc', amb='crt', people=True, camera='breath', vx=0.5, vo=[(0.3, 'm2', 'sync')],
         text=[(0.2, 2.2, 'lower3', *ML)]),
    dict(id='A3', src=V4 + 'v4-lights.mp4', dur=0.9, **{'in': 4.1}, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True),
    # ── HERO ───────────────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='B1', src='png:gen/render/r-firstlight', dur=2.8, **{'in': 0.8}, grade='studio', amb='studio', vo=[(0.3, 'h1')]),
    dict(id='B2', src=R4 + 'r4-board-blur', dur=3.0, grade='studio', amb='studio', dof=DOF),
    dict(id='B3', src=R4 + 'r4-canyon-blur', dur=2.0, grade='studio', amb='studio', dof=DOF),
    dict(id='B4', src=R4 + 'r4-plate-blur', dur=1.6, grade='studio', amb='studio', vo=[(0.2, 'h2')]),
    dict(id='B5', src=FLY, dur=3.0, **{'in': 1.0}, grade='studio', amb='studio', dof=DOF),
    dict(id='B6', src=FLY, dur=2.4, **{'in': 13.2}, grade='studio', amb='studio', dof=DOF),
    dict(id='B7', src=FLY, dur=1.6, **{'in': 6.0}, grade='studio', amb='studio', dof=DOF),
    dict(id='B8', src=R4 + 'f4-field', dur=3.0, **{'in': 25.0}, grade='studio', amb='studio', vo=[(0.0, 'h3')]),
    dict(id='B9', src=FLY, dur=4.7, **{'in': 7.7}, grade='studio', amb='studio', dof=DOF),
    dict(id='B10', src=R4 + 'r4-trip-blur', dur=2.6, grade='studio', amb='studio', vo=[(0.4, 'h4')]),
    dict(id='B11', src=FLY, dur=2.9, **{'in': 11.0}, grade='studio', amb='studio', dof=DOF, text=[BIG(0.8, 2.85, '0.26 ns')]),
    dict(id='B12', src=R4 + 'b4-bars', dur=10.5, grade='studio', amb='studio', vo=[(0.6, 'h5')],
         text=[BIG(2.3, 5.6, '700×'), BIG(6.3, 10.4, '1,200×')]),
    dict(id='B13', src=R4 + 'r4-expand-blur', dur=5.0, grade='white', amb='studio_room', dof=DOF, ink=True, vo=[(0.3, 'h6')]),
    dict(id='B14', src='png:gen/render/r2-studio-hero', dur=2.2, **{'in': 2.0}, grade='white', amb='studio_room', dof=dict(focus=1.0, strength=2.2), ink=True,
         text=[(0.05, 2.2, 'name', 'PHASER', 'left')]),
    # ── THE CUSTOMER, THEN THE CEO ────────────────────────────────────────────────────────────────────────────────
    dict(id='C1', src='mp4:gen/v3/ls/ls3-c1.mp4', dur=4.8, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True,
         vo=[(0.3, 'c1', 'sync')], text=[(0.3, 3.8, 'lower3', 'Head of Platform', 'AI startup')]),
    dict(id='C2', src='mp4:gen/v3/ls/ls3-c2.mp4', dur=6.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.62, ink=True, vo=[(0.3, 'c2', 'sync')]),
    dict(id='C3', src=L4 + 'ls4-k1a.mp4', dur=9.0, grade='white', amb='studio_room', people=True, camera='breath', vx=0.45, ink=True,
         vo=[(0.3, 'k1a', 'sync')], text=[(0.4, 4.0, 'lower3', *CM)]),
    dict(id='C4', src=L4 + 'ls4-k1b.mp4', dur=4.7, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.3, 'k1b', 'sync')]),
    # ── HOW IT WORKS ──────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='D1', src=L4 + 'ls4-t1.mp4', dur=4.1, grade='white', amb='studio_room', people=True, camera='breath', vx=0.4, ink=True, vo=[(0.3, 't1', 'sync')]),
    dict(id='D2', src=R4 + 'f4-field', dur=8.0, **{'in': 0.3}, grade='studio', amb='field', vo=[(0.2, 't2')]),
    dict(id='D3', src=R4 + 'f4-field', dur=9.6, **{'in': 8.0}, grade='studio', amb='field', vo=[(0.2, 't3')]),
    dict(id='D4', src=R4 + 'f4-field', dur=11.5, **{'in': 17.5}, grade='studio', amb='field', vo=[(0.1, 't4')]),
    dict(id='D5', src=R4 + 'f4-field', dur=2.6, **{'in': 29.2}, grade='studio', amb='field'),
    dict(id='D6', src=L4 + 'ls4-t5.mp4', dur=8.1, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.3, 't5', 'sync')]),
    # ── THE PLANET ────────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='E1', src='png:gen/render/r3-globe', dur=6.0, **{'in': 1.5}, grade='space', amb='space', vo=[(0.3, 'k2')]),
    dict(id='E2', src=V4 + 'tl-intersection.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E3', src=V4 + 'tl-railyard.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, vo=[(0.2, 'k4')], **TL),
    dict(id='E4', src='mp4:gen/v3/video/v3-dc-campus.mp4', dur=0.95, **{'in': 1.5}, speed=2.0, **TL),
    dict(id='E5', src=V4 + 'tl-port.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E6', src=V4 + 'tl-interchange.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E7', src='mp4:gen/v3/video/v3-grid.mp4', dur=0.95, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E8', src=V4 + 'tl-airport.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E9', src=V4 + 'tl-steel.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E10', src=V4 + 'tl-windfarm.mp4', dur=0.85, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E11', src='mp4:gen/v3/video/v3-plant.mp4', dur=0.95, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E12', src=V4 + 'tl-skyline.mp4', dur=1.4, **{'in': 1.0}, speed=2.0, **TL),
    dict(id='E13', src='png:gen/render/r3-globe', dur=3.2, **{'in': 6.8}, grade='space', amb='space', vo=[(0.1, 'a1')]),
    dict(id='E14', src=V4 + 'tl-interchange.mp4', dur=1.0, **{'in': 3.0}, speed=2.0, **TL),
    dict(id='E15', src=V4 + 'tl-port.mp4', dur=1.0, **{'in': 3.0}, speed=2.0, **TL),
    dict(id='E16', src=V4 + 'tl-intersection.mp4', dur=1.0, **{'in': 3.0}, speed=2.0, **TL),
    dict(id='E17', src='mp4:gen/v3/video/v3-city.mp4', dur=1.6, **{'in': 1.0}, speed=1.6, **TL),
    dict(id='E18', src=V4 + 'tl-skyline.mp4', dur=1.4, **{'in': 3.2}, speed=1.4, **TL),
    dict(id='E19', src='png:gen/render/r3-globe', dur=4.4, **{'in': 0.0}, grade='space', amb='space', vo=[(0.4, 'a2')]),
    dict(id='E20', src='png:gen/render/r-thesis', dur=4.4, **{'in': 1.0}, grade='studio', amb='studio'),
    # ── IGNITION ──────────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='F1', src='mp4:gen/video/v-e4.mp4', dur=3.0, **{'in': 0.5}, grade='doc', amb='garage', people=True, camera='handheld', vx=0.45, vo=[(0.3, 'g1')]),
    dict(id='F2', src='mp4:gen/v2/ls/ls-m5.mp4', dur=3.4, **{'in': 0.6}, grade='doc', amb='garage', people=True, camera='handheld', vx=0.6),
    dict(id='F3', src='mp4:gen/v2/video/v2-wide.mp4', dur=2.6, grade='doc', amb='garage', people=True, camera='handheld', vx=0.65, vo=[(0.2, 'g2')]),
    dict(id='F4', src='mp4:gen/video/v-e2.mp4', dur=3.2, speed=0.8, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55, sfx=[(0.8, 'click'), (2.2, 'click')]),
    dict(id='F5', src='png:gen/render/r2-assemble', dur=5.0, **{'in': 0.5}, grade='studio', amb='studio', dof=DOF),
    dict(id='F6', src=R4 + 'r4-ignite-blur', dur=4.2, **{'in': 1.3}, grade='studio', amb='studio', vo=[(0.0, 'g3')], sfx=[(1.7, 'ignite')]),
    dict(id='F7', src=V4 + 'v4-stones.mp4', dur=5.0, grade='world', amb='wind', vx=0.5, vo=[(0.2, 'g4')]),
    dict(id='F8', src='png:gen/render/r-firstlight', dur=2.0, **{'in': 1.2}, grade='studio', amb='studio'),
    dict(id='F9', src='mp4:gen/v2/video/v2-monitor.mp4', dur=3.6, **{'in': 2.0}, grade='doc', amb='garage', people=True, camera='handheld', vx=0.55, vo=[(0.1, 'g5')]),
    # ── CLOSE ─────────────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='G1', src=L4 + 'ls4-k7.mp4', dur=6.1, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.3, 'k7', 'sync')]),
    dict(id='G2', src=L4 + 'ls4-m12.mp4', dur=3.1, grade='white', amb='studio_room', people=True, camera='breath', vx=0.5, ink=True, vo=[(0.3, 'm12', 'sync')]),
    dict(id='G3', src='black', dur=0.7, amb='none', lens=False),
    dict(id='H1', src='sig', dur=6.6, amb='none', lens=False),
    dict(id='H2', src='black', dur=5.0, amb='none', lens=False, text=[(0.2, 4.9, 'smallprint', *SMALL_PRINT)]),
]

SHORT = [(0.1, 2.6, 'smallprint', 'PLANNED FUTURE PRODUCT LAUNCH VIDEO. DRAMATIZATION, AI-GENERATED. FIGURES MODELED IN SIMULATION, NOT MEASURED. SOURCES: PHASER.TENSACO.AI/NOTES')]
CUTS = {
    'cut60': [('A1', {}), ('A2', {}), ('A3', {}), ('B2', {}), ('B3', {}), ('B10', {}), ('B11', {}), ('B12', {}), ('B13', {}), ('B14', {}),
              ('C2', {}), ('F6', {}), ('F7', dict(dur=3.5)), ('G2', {}), ('G3', {}), ('H1', {}), ('H2', dict(dur=2.8, text=SHORT))],
    'cut30': [('A2', {}), ('A3', {}), ('B2', {}), ('B3', {}), ('B11', {}), ('B13', {}), ('B14', {}), ('F6', {}), ('G2', {}), ('H1', dict(dur=4.6)), ('H2', dict(dur=2.8, text=SHORT))],
    'cut15': [('B2', {}), ('B3', {}), ('B11', {}), ('B14', {}), ('H1', dict(dur=3.6)), ('H2', dict(dur=2.6, text=SHORT))],
}

META = dict(vo_dir='gen/v4/vo', speakers={i: s for i, s, _ in LINES}, mixer='v4', stems_dir='out/stems-v4', tag='v4-',
            overlay=('PLANNED FUTURE PRODUCT LAUNCH VIDEO', 'AI-GENERATED · FIGURES MODELED'), tags=False)

CUTS['cuttest'] = [(k, {}) for k in ('A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'B12', 'B13', 'B14', 'E1', 'E2', 'E3', 'E4', 'E5', 'F5', 'F6', 'G2', 'G3', 'H1', 'H2')]
