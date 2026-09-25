"""The edit. Each clip: id, src, dur (s) and options. Sources:
  black                      nothing
  png:<dir>                  rendered frames (the site's three.js scene, or a numpy visualization); `in` = first frame (s)
  mp4:<path>                 video; `in` = in-point (s), `speed` < 1 slows it
Options: grade (studio | doc | world | viz), crop (x0, y0, x1, y1 as fractions: reframe), push (zoom at start, at end),
vx (horizontal centre for the 9:16 crop), text [(t0, t1, kind, *content)], vo [(t, line id)], sfx [(t, name)],
amb (ambience bed), music (0..1 level of the score under this clip), people (show the dramatization tag).
Line ids are in script.py. Every number on screen is labelled modeled (see docs/CLAIMS.md)."""

MOD = 'modeled'
EDL = [
    # ── ACT 1 — the physical limit ─────────────────────────────────────────────────────────────────────────────────────
    dict(id='a1', src='black', dur=1.6, amb='none', text=[(0.2, 1.7, 'slate', 'TENSACO · PHASER', '14 NOVEMBER 2026')]),
    dict(id='a2', src='png:gen/viz/electrons', dur=6.6, grade='viz', amb='elec', push=(1.0, 1.04), vx=0.5,
         text=[(1.6, 6.8, 'line', 'Intelligence runs on electrons.')]),
    dict(id='a3', src='mp4:gen/video/v-cooling.mp4', dur=1.2, **{'in': 1.0}, grade='doc', amb='fans', vx=0.45),
    dict(id='a4', src='black', dur=1.0, amb='none'),
    dict(id='a5', src='black', dur=2.5, amb='none', text=[(0.25, 2.45, 'line', 'PHASER runs it on light.')]),
    dict(id='a6', src='png:gen/render/r-firstlight', dur=4.0, grade='studio', amb='studio', sfx=[(0.35, 'optical')]),
    # ── ACT 2 — PHASER reveal ─────────────────────────────────────────────────────────────────────────────────────────
    dict(id='b1', src='png:gen/render/r-reveal', dur=6.0, grade='studio', amb='studio', music=0.5, sfx=[(0.0, 'cavity')]),
    dict(id='b2', src='png:gen/render/r-plate', dur=5.5, grade='studio', amb='studio', music=0.55,
         text=[(1.0, 5.3, 'line', 'The interference is the arithmetic.')]),
    dict(id='b3', src='png:gen/render/r-roundtrip', dur=5.5, grade='studio', amb='studio', music=0.55, sfx=[(0.1, 'cavity')],
         text=[(3.0, 5.45, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD)]),
    dict(id='b4', src='png:gen/render/r-multiplex', dur=5.5, grade='studio', amb='studio', music=0.65, sfx=[(0.1, 'cavity_fast')],
         text=[(2.2, 5.45, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)]),
    dict(id='b5', src='png:gen/render/r-energy', dur=5.5, grade='studio', amb='studio', music=0.6,
         text=[(0.5, 5.4, 'num', '≤ 0.001 pJ', 'per equivalent multiply, at a million optical modes',
                MOD + ' · today’s AI chips: ~1 pJ per multiply-accumulate')]),
    dict(id='b6', src='png:gen/render/r-hero', dur=2.6, grade='studio', amb='studio', music=0.45),
    # ── ACT 3 — the engineer (dramatized) ─────────────────────────────────────────────────────────────────────────────
    dict(id='c1', src='mp4:gen/ls/ls-e1.mp4', dur=3.4, grade='doc', amb='garage', people=True, vx=0.33,
         vo=[(0.3, 'e1')], text=[(0.4, 3.3, 'lower', 'Optical engineer', 'dramatized role · AI-generated')]),
    dict(id='c2', src='mp4:gen/video/v-e2.mp4', dur=6.9, speed=0.72, grade='doc', amb='garage', people=True, vx=0.55,
         vo=[(0.1, 'e2')], sfx=[(1.3, 'click'), (4.2, 'click')]),
    dict(id='c3', src='mp4:gen/ls/ls-e3.mp4', dur=8.2, grade='doc', amb='garage', people=True, vx=0.5, vo=[(0.3, 'e3')]),
    dict(id='c4', src='mp4:gen/video/v-e4.mp4', dur=7.2, speed=0.69, grade='doc', amb='garage', people=True, vx=0.45,
         vo=[(0.3, 'e5')]),
    dict(id='c5', src='png:gen/render/r-slope', dur=4.0, grade='studio', amb='garage', vo=[(0.3, 'e4')]),
    dict(id='c6', src='mp4:gen/video/v-e5.mp4', dur=5.0, grade='doc', amb='garage', people=True, vx=0.55),
    dict(id='c7', src='mp4:gen/video/v-e8.mp4', dur=3.4, grade='doc', amb='garage', people=True, vx=0.6, push=(1.0, 1.03)),
    dict(id='c8', src='mp4:gen/video/v-e6b.mp4', dur=9.4, grade='doc', amb='garage', people=True, vx=0.6, vo=[(0.5, 'e6')]),
    dict(id='c9', src='mp4:gen/video/v-e10.mp4', dur=2.8, grade='doc', amb='garage', people=True, vx=0.6,
         sfx=[(0.5, 'plug'), (1.7, 'optical_soft')]),
    # ── ACT 4 — the people who use it (dramatized) ────────────────────────────────────────────────────────────────────
    dict(id='d1', src='mp4:gen/video/v-b5.mp4', dur=4.4, speed=0.85, grade='doc', amb='office', people=True, vx=0.5,
         vo=[(0.3, 'n1')], music=0.35),
    dict(id='d2', src='mp4:gen/video/v-b8.mp4', dur=3.6, grade='doc', amb='office', people=True, vx=0.45, music=0.35,
         sfx=[(0.6, 'key')]),
    dict(id='d3', src='mp4:gen/ls/ls-b1.mp4', dur=3.7, grade='doc', amb='office', people=True, vx=0.55, vo=[(0.3, 'b1')],
         text=[(0.3, 3.6, 'lower', 'Head of inference, AI company', 'dramatized role · AI-generated')], music=0.3),
    dict(id='d4', src='mp4:gen/ls/ls-b2.mp4', dur=4.5, grade='doc', amb='office', people=True, vx=0.33, vo=[(0.3, 'b2')],
         text=[(0.3, 4.4, 'lower', 'Infrastructure lead, datacenter operator', 'dramatized role · AI-generated')], music=0.3),
    dict(id='d5', src='mp4:gen/ls/ls-b3.mp4', dur=6.3, grade='doc', amb='office', people=True, vx=0.66, vo=[(0.3, 'b3')],
         text=[(0.4, 6.2, 'note', 'Dramatization. PHASER energy figures are modeled.')], music=0.3),
    dict(id='d6', src='mp4:gen/video/v-b7.mp4', dur=4.6, grade='doc', amb='office', people=True, vx=0.45, vo=[(0.3, 'b4')], music=0.35),
    dict(id='d7', src='mp4:gen/video/v-b4.mp4', dur=4.4, grade='doc', amb='office', people=True, vx=0.45, music=0.35),
    dict(id='d8', src='mp4:gen/ls/ls-b5.mp4', dur=3.9, grade='doc', amb='office', people=True, vx=0.33, vo=[(0.3, 'b5')], music=0.35),
    # ── ACT 5 — the bottleneck moves outward ──────────────────────────────────────────────────────────────────────────
    dict(id='e1', src='mp4:gen/video/v-rack.mp4', dur=6.0, speed=0.83, grade='world', amb='datacenter', vx=0.5,
         vo=[(0.3, 'n2')], music=0.3),
    dict(id='e2', src='mp4:gen/video/v-transformer.mp4', dur=6.6, speed=0.75, grade='world', amb='transformer', vx=0.62,
         vo=[(1.9, 'b6')], text=[(4.0, 6.5, 'num', '128 weeks', 'to get a large power transformer', 'Wood Mackenzie, 2025')], music=0.25),
    dict(id='e3', src='mp4:assets/stock/substation-yard-orig.mp4', dur=3.8, **{'in': 1.0}, grade='world', amb='transformer', vx=0.5,
         vo=[(0.2, 'n3')], music=0.35),
    dict(id='e4', src='mp4:assets/stock/transmission-lines-orig.mp4', dur=3.6, **{'in': 8.0}, grade='world', amb='wind', vx=0.5, music=0.4),
    dict(id='e5', src='png:gen/render/r-multiplex', dur=3.0, **{'in': 3.0}, grade='studio', amb='studio', vo=[(0.2, 'n4')], music=0.45),
    # ── ACT 6 — human stakes ──────────────────────────────────────────────────────────────────────────────────────────
    dict(id='f1', src='mp4:assets/stock/substation-crew-orig.mp4', dur=3.2, **{'in': 3.0}, grade='world', amb='wind', vx=0.5,
         vo=[(0.4, 'n5')], music=0.55),
    dict(id='f2', src='mp4:assets/stock/cooling-towers-river-orig.mp4', dur=3.0, **{'in': 12.0}, grade='world', amb='wind', vx=0.5,
         vo=[(0.2, 'n6')], music=0.6),
    dict(id='f3', src='mp4:gen/video/v-hospital.mp4', dur=3.4, grade='world', amb='hospital', people=True, vx=0.4, vo=[(0.6, 'n7')], music=0.6),
    dict(id='f4', src='mp4:gen/video/v-water.mp4', dur=2.8, grade='world', amb='pumps', vx=0.35, vo=[(0.5, 'n8')], music=0.6),
    dict(id='f5', src='mp4:gen/video/v-greenhouse.mp4', dur=2.4, grade='world', amb='refrigeration', people=True, vx=0.5, vo=[(0.4, 'n9')], music=0.6),
    dict(id='f7', src='mp4:gen/video/v-grocery.mp4', dur=2.0, grade='world', amb='store', people=True, vx=0.55, music=0.6),
    dict(id='f8', src='mp4:gen/video/v-home.mp4', dur=2.6, grade='world', amb='wind', vx=0.7, vo=[(0.5, 'n10')], music=0.6),
    dict(id='f9', src='mp4:gen/video/v-steel.mp4', dur=2.6, grade='world', amb='steel', people=True, vx=0.45, vo=[(0.4, 'n11')], music=0.65),
    dict(id='f10', src='mp4:assets/stock/datacenter-supermuc.mp4', dur=4.3, grade='world', amb='datacenter', people=True, vx=0.5,
         vo=[(0.5, 'n12')], music=0.55),
    dict(id='f11', src='black', dur=0.8, amb='none', music=0.0),
    # ── ACT 7 — resolution ────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='g1', src='png:gen/render/r-resolve', dur=7.4, grade='studio', amb='studio', vo=[(0.4, 'n13')], music=0.55, sfx=[(0.3, 'optical_soft')]),
    dict(id='g2', src='png:gen/render/r-thesis', dur=6.4, grade='studio', amb='studio', vo=[(0.2, 'n14'), (3.3, 'n15')], music=0.7),
    dict(id='g3', src='mp4:gen/video/v-city.mp4', dur=7.1, speed=0.7, grade='world', amb='city', vx=0.5, vo=[(2.2, 'n16')], music=0.75,
         text=[(0.2, 3.9, 'num', '200–3,000×', 'less energy per step than an equally capable dense recurrent network',
                MOD + ' at a million optical modes')]),
    # ── ACT 8 — end frame ─────────────────────────────────────────────────────────────────────────────────────────────
    dict(id='h1', src='png:gen/render/r-end', dur=10.4, grade='studio', amb='studio', music=0.3, sfx=[(0.5, 'optical'), (9.6, 'optical_soft')],
         text=[(4.0, 10.4, 'end', 'PHASER', 'A neural accelerator that runs at the speed of light.', 'Now live  ·  phaser.tensaco.ai')], fadeout=1.2),
    dict(id='h2', src='black', dur=4.2, amb='none', text=[(0.3, 4.1, 'credits',
         'Planned future product launch video, set on 14 November 2026. Dramatization: people, places and voices are AI-generated.',
         'PHASER performance figures are modeled in simulation, not measured. Sources: phaser.tensaco.ai/notes',
         'SuperMUC footage: IBM Research, CC BY 3.0, via Wikimedia Commons. Stock footage: Pexels.')]),
]

# cut-downs: (clip id, overrides). Their VO placements come with the clip.
END = lambda t0, t1: [(t0, t1, 'end', 'PHASER', 'A neural accelerator that runs at the speed of light.', 'Now live  ·  phaser.tensaco.ai')]
SHORT_CREDITS = [(0.15, 2.0, 'credits', 'Planned future product launch video. Figures are modeled in simulation, not measured.')]
CUTS = {
    'cut60': [('a2', dict(dur=4.0, text=[(0.6, 3.9, 'line', 'Intelligence runs on electrons.')])), ('a5', {}), ('a6', dict(dur=3.2)),
              ('b2', dict(dur=4.0, text=[(0.5, 3.9, 'line', 'The interference is the arithmetic.')])), ('b4', {}), ('c1', {}), ('c2', {}),
              ('d5', {}), ('f1', {}), ('f2', {}), ('g2', {}), ('h1', dict(dur=9.0, **{'in': 2.0}, text=END(2.2, 9.0))), ('h2', dict(dur=3.6))],
    'cut30': [('a5', dict(dur=2.4, text=[(0.2, 2.3, 'line', 'PHASER runs it on light.')])), ('a6', dict(dur=2.8)),
              ('b3', dict(dur=4.2, **{'in': 1.8}, text=[(1.5, 4.15, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD)])),
              ('b4', dict(dur=4.8, **{'in': 1.2}, text=[(1.2, 4.75, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)])),
              ('g2', {}), ('h1', dict(dur=6.5, **{'in': 4.5}, text=END(0.3, 6.5))), ('h2', dict(dur=3.0))],
    'cut15': [('a6', dict(dur=2.4)), ('b3', dict(dur=3.6, **{'in': 2.4}, text=[(0.9, 3.55, 'num', '0.26 ns', 'per input step: one round trip up the stack and back', MOD)])),
              ('b4', dict(dur=3.4, **{'in': 2.6}, text=[(0.2, 3.35, 'num', '10 billion', 'input steps per second, with light pulses in flight', MOD)])),
              ('h1', dict(dur=4.4, **{'in': 6.2}, text=END(0.2, 4.4))), ('h2', dict(dur=2.1, text=SHORT_CREDITS))],
}
