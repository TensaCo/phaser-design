"""v4 stills and motion. "Studio" means light and framing only: a seamless white or dark background, soft key light, and
never visible stands, softboxes, lamps or an interviewer."""
import json, sys
sys.path.insert(0, 'src')
from prompts_v2 import MEILIN, ML_STUDIO, CML
from prompts_v3_cast import COLE, COLE_WARDROBE
from prompts_video import EP, NEG as VNEG
CCM, R0 = "@file:gen/v3/char/cole.png", "@file:assets/ref/phaser-ref-0.jpg"
DARK = "@file:gen/v3/stills/s3-ml-dark.png"
SEAMLESS = ("a seamless pure-white infinity background with soft even light from one large source out of frame; "
            "absolutely no visible lights, stands, softboxes, cables, cameras or crew anywhere in frame")
LOOK = ("Premium product-film portrait, cinema camera, natural skin texture with pores, real proportions and hands, subtle grain, "
        "soft highlight rolloff. No text, no logos, no readable writing.")
def E(id, prompt, refs): return dict(id=id, endpoint="fal-ai/nano-banana-pro/edit", out=f"gen/v4/stills/{id}", payload=dict(prompt=prompt, image_urls=refs, aspect_ratio="16:9", resolution="2K"))
def T(id, prompt): return dict(id=id, endpoint="fal-ai/nano-banana-pro", out=f"gen/v4/stills/{id}", payload=dict(prompt=prompt, aspect_ratio="16:9", resolution="2K"))
stills = [
 E("s4-dark-crt", f"Same dark room as the reference, but the camera is now very close to the vintage grey CRT terminal at left: the glowing green phosphor screen fills the left half of the frame with soft scanlines and curved glass; everything else falls into deep darkness; far behind and out of focus, the faint silhouette of the small optical assembly with a trace of red light, and further back a barely visible seated woman. Cinematic low light, shallow depth of field. {LOOK}", [DARK]),
 E("s4-dark-mcu", f"Same dark room as the first reference: medium close-up of {MEILIN}, {ML_STUDIO} (same face as the second reference), seated, looking into the lens, lit only by the cool green glow of the CRT from the left; the small optical assembly softly out of focus in the right foreground with a trace of red light between its plates. Deep blacks, no other light. {LOOK}", [DARK, CML]),
 E("s4-lit-mcu", f"The exact same framing, person, pose and objects as the reference image, but now brightly lit: {SEAMLESS}. The CRT at left and the optical assembly in the right foreground remain. {LOOK}", ["@file:gen/v4/stills/s4-dark-mcu.png"]),
 E("s4-ml-34", f"Medium shot, 50mm lens: {MEILIN}, {ML_STUDIO} (same face as the first reference), seated on a simple light-oak chair against {SEAMLESS}; body angled slightly left, eyes just off camera left, explaining something with one hand, amused and precise. The small optical assembly (second reference, exactly four plate cells) stands on a white plinth at frame right. {LOOK}", [CML, R0]),
 E("s4-ml-cu", f"Close-up, 85mm lens at eye level: {MEILIN}, {ML_STUDIO} (same face as the reference), looking straight into the lens with calm conviction, against {SEAMLESS}. {LOOK}", [CML]),
 E("s4-cole-34", f"Medium shot, 50mm lens: {COLE}, wearing {COLE_WARDROBE} (same face as the reference), sitting forward on a light-oak chair against {SEAMLESS}, elbows on knees, eyes just off camera right, mid-sentence, intense with a half-grin. {LOOK}", [CCM]),
 E("s4-cole-cu", f"Close-up, 85mm lens at eye level: {COLE}, wearing {COLE_WARDROBE} (same face as the reference), looking straight down the lens with gritty conviction against {SEAMLESS}. {LOOK}", [CCM]),
 T("s4-stones", "Real photograph, a prehistoric stone circle on a misty plain at dawn: the rising sun sits exactly in the gap between two giant standing stones, a single shaft of golden light running straight through the circle, long shadows, cinematic, 35mm, natural colour. No people, no text."),
]
VIDEO = {  # (still, duration, tail still or None, prompt)
 'v4-cold-move': ('s4-dark-crt', '10', 's4-dark-mcu', "Camera: one slow continuous glide on a dolly and slider: it starts on the glowing CRT screen, drifts right through the darkness past the small optical assembly glinting red, and settles into a medium close-up of the woman seated behind, who is speaking calmly to the lens. Rack focus follows. Smooth, cinematic, no cuts."),
 'v4-ml-34': ('s4-ml-34', '10', None, "Camera: on sticks, nearly still with a slow push. She explains something to someone just off camera, precise hand gestures, a quick smile."),
 'v4-ml-cu-a': ('s4-ml-cu', '10', None, "Camera: on sticks, a very slow push in. She speaks straight to the lens with calm conviction, natural blinks."),
 'v4-ml-cu-b': ('s4-ml-cu', '5', None, "Camera: on sticks, a very slow push in. She says one short sentence to the lens and holds the look, a faint smile."),
 'v4-cole-34': ('s4-cole-34', '10', None, "Camera: on sticks, nearly still. He talks with intensity and humour, leaning forward, hands cutting the air."),
 'v4-cole-cu-a': ('s4-cole-cu', '10', None, "Camera: on sticks, a slow push in. He speaks straight to the lens, certain, small nods."),
 'v4-cole-cu-b': ('s4-cole-cu', '10', None, "Camera: on sticks, a slow push in. He says something important straight to the lens, deliberate, then holds the look with a half-grin."),
 'v4-stones': ('s4-stones', '5', None, "Camera: a slow push toward the gap in the stones as the sun rises through it and the light beam brightens across the mist. Time-lapse clouds."),
}
TIMELAPSE = {  # text-to-video, the planet at speed
 'tl-intersection': "Night time-lapse from high above a huge city intersection: streams of headlights and tail lights flow in every direction, crowds pulse across crosswalks, screens and neon blur. Locked-off camera, extreme speed, 4K, real footage look.",
 'tl-railyard': "Aerial time-lapse over a vast freight rail yard at dusk: hundreds of wagons shuffle and flow along parallel tracks, locomotives streak through, floodlights come on. Real drone footage look, fast motion.",
 'tl-port': "Aerial time-lapse of an enormous container port at night: gantry cranes swing containers, trucks stream in lines, a giant ship docks, lights everywhere. Real footage, fast motion.",
 'tl-interchange': "Night drone time-lapse of a stacked highway interchange: rivers of red and white light curve through the levels at high speed. Real footage look.",
 'tl-skyline': "Time-lapse of a vast city skyline from day to night: the sun drops, thousands of windows and streets switch on in waves, the city lights up. Real footage, fast.",
 'tl-airport': "Night time-lapse of a major airport: planes taxi and take off in streaks of light, runway lights pulse, the terminal glows. Real footage look.",
 'tl-windfarm': "Aerial time-lapse flying fast over an offshore wind farm at dusk, rows of turbines spinning to the horizon, clouds racing. Real footage.",
 'tl-steel': "Time-lapse inside a steel mill: molten metal pours, sparks storm, cranes move, workers in heat gear. Fast, real footage look.",
}
if __name__ == '__main__':
    json.dump(stills[:2] + stills[3:], open('gen/v4/stills.json', 'w'), indent=1)
    json.dump([stills[2]], open('gen/v4/stills-lit.json', 'w'), indent=1)
    vj = []
    for k, (s, d, tail, p) in VIDEO.items():
        pl = dict(prompt=p, image_url=f'@file:gen/v4/stills/{s}.jpg', duration=d, negative_prompt=VNEG, cfg_scale=0.5)
        if tail: pl['tail_image_url'] = f'@file:gen/v4/stills/{tail}.jpg'
        vj.append(dict(id=k, endpoint=EP, out=f'gen/v4/video/{k}', payload=pl))
    for k, p in TIMELAPSE.items():
        vj.append(dict(id=k, endpoint='fal-ai/kling-video/v2.5-turbo/pro/text-to-video', out=f'gen/v4/video/{k}', payload=dict(prompt=p, duration='5', aspect_ratio='16:9', negative_prompt=VNEG, cfg_scale=0.5)))
    json.dump(vj, open('gen/v4/video.json', 'w'), indent=1)
