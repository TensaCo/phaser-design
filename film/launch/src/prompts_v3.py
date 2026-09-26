"""v3 stills and motion: the one-shot cold open (dark CRT studio → lights on), Cole Mercer, the second customer, and
planetary-scale infrastructure aerials."""
import json, sys
sys.path.insert(0, 'src')
from prompts_v2 import MEILIN, ML_STUDIO, STUDIO, LOOK, CML, SM
from prompts_v3_cast import COLE, COLE_WARDROBE, CUST2
from prompts_video import EP, NEG as VNEG
CCM, CC2, R0 = "@file:gen/v3/char/cole.png", "@file:gen/v3/char/cust2.png", "@file:assets/ref/phaser-ref-0.jpg"
def E(id, prompt, refs): return dict(id=id, endpoint="fal-ai/nano-banana-pro/edit", out=f"gen/v3/stills/{id}", payload=dict(prompt=prompt, image_urls=refs, aspect_ratio="16:9", resolution="2K"))
def T(id, prompt): return dict(id=id, endpoint="fal-ai/nano-banana-pro", out=f"gen/v3/stills/{id}", payload=dict(prompt=prompt, aspect_ratio="16:9", resolution="2K"))
AERIAL = ("Real aerial cinematography still from a high drone or helicopter at night, wide 24mm lens, photographic, natural colour, "
          "sodium and white lights, deep blacks, subtle haze. No text, no logos, no labels.")
chars = [E("char-cole", f"Character reference sheet: three views side by side (front, three-quarter, profile) of the man in the reference photo, same face exactly: {COLE}, wearing {COLE_WARDROBE}. Neutral light-grey background, soft even light. {LOOK}", ["@file:gen/v3/heads/cole-final.png"])]
stills = [
 # the one-shot cold open: lit frame first, then the same frame with the lights off
 E("s3-ml-lit", f"Medium close-up, 50mm lens at eye level, symmetrical and still: {MEILIN}, {ML_STUDIO} (same face as the first reference), seated on the oak chair in the white studio (second reference), facing the lens. On a small low table at the left edge of frame sits a vintage beige CRT computer monitor, switched on, its screen a soft glowing phosphor. At the right edge of frame, on a white plinth, the small optical assembly (third reference, exactly four thin plate cells, faint red light between the plates). Bright soft studio light. {LOOK}", [CML, SM, R0]),
]
stills_dark = [
 E("s3-ml-dark", f"The exact same photograph, identical framing, pose, person and objects, but the studio lights are OFF: the room is almost pitch black; the only light is the glow of the CRT monitor screen at left, a cool soft phosphor light falling across the left side of her face and glasses, with faint scanline texture; the optical assembly at right is only a faint silhouette with the smallest trace of red between its plates. Moody, cinematic, deep blacks, realistic low-light noise. {LOOK}", ["@file:gen/v3/stills/s3-ml-lit.png"]),
]
stills2 = [
 E("s3-cole-34", f"Interview frame, 50mm lens, subject on the left third: {COLE}, wearing {COLE_WARDROBE} (same face as the first reference), sits forward on the oak chair in the white studio (second reference), elbows on knees, angled toward an interviewer just right of camera, mid-sentence, intense and amused, one hand cutting the air. {LOOK}", [CCM, SM]),
 E("s3-cole-direct", f"Close-up, 85mm lens at eye level: {COLE}, wearing {COLE_WARDROBE} (same face as the first reference), in the white studio (second reference), looking straight down the lens with gritty conviction, jaw set, a hint of a grin. Background soft white. {LOOK}", [CCM, SM]),
 E("s3-cust2-34", f"Interview frame, 50mm lens, subject on the right third: {CUST2} (same face and clothes as the first reference) sits on the oak chair in the white studio (second reference), angled toward an interviewer left of camera, mid-laugh while telling a story, hands animated. {LOOK}", [CC2, SM]),
 T("s3-dc-campus", f"{AERIAL} A vast hyperscale AI datacenter campus in a desert at night seen from high above: rows of enormous windowless halls, cooling units on the roofs, an on-site electrical substation, transmission lines running away to the horizon, a distant city glow."),
 T("s3-grid", f"{AERIAL} Dusk-to-night aerial over a continental plain: high-voltage transmission lines on lattice towers march in parallel toward the horizon, small towns glowing, the last blue light in the sky, red aviation lights on the tallest towers."),
 T("s3-plant", f"{AERIAL} Night aerial of a large power station beside a river: cooling towers releasing lit steam plumes, the switchyard glowing, transmission lines fanning out into darkness."),
 T("s3-city", f"{AERIAL} Night aerial over a dense city grid: glowing avenues converge toward a large electrical substation and a cluster of datacenter buildings at the city edge."),
]
VIDEO = {
 'v3-ml-dark': ('s3-ml-dark', '10', None, "Camera: locked-off tripod, perfectly still. In the dark, she speaks calmly and directly to the lens, lit only by the flickering CRT glow; small natural head movements and blinks. The room stays dark. The optical assembly stays unchanged."),
 'v3-cole-34': ('s3-cole-34', '10', None, "Camera: on sticks, nearly static. He talks to the interviewer with intensity and humour, leaning forward, hands moving, a quick grin."),
 'v3-cole-direct-a': ('s3-cole-direct', '10', None, "Camera: on sticks, nearly static. He speaks straight to the lens with conviction, small nods, natural blinking."),
 'v3-cust2': ('s3-cust2-34', '10', None, "Camera: on sticks, nearly static. She tells the story laughing, hands animated, then shakes her head in disbelief."),
 'v3-dc-campus': ('s3-dc-campus', '5', None, "Camera: a fast, smooth drone flight forward and descending over the datacenter campus, revealing its scale; lights steady; no cuts."),
 'v3-grid': ('s3-grid', '5', None, "Camera: a sweeping drone flight low along the transmission lines toward the horizon, towers passing below; smooth and fast."),
 'v3-plant': ('s3-plant', '5', None, "Camera: a slow powerful drone orbit around the power station; steam plumes drift and glow."),
 'v3-city': ('s3-city', '5', None, "Camera: a fast smooth drone push over the city grid toward the substation and datacenters at the edge; lights twinkle."),
}
if __name__ == '__main__':
    json.dump(chars, open('gen/v3/chars.json', 'w'), indent=1)
    json.dump(stills, open('gen/v3/stills1.json', 'w'), indent=1)
    json.dump(stills_dark, open('gen/v3/stills-dark.json', 'w'), indent=1)
    json.dump(stills2, open('gen/v3/stills2.json', 'w'), indent=1)
    vj = []
    for k, (s, d, tail, p) in VIDEO.items():
        pl = dict(prompt=p, image_url=f'@file:gen/v3/stills/{s}.jpg', duration=d, negative_prompt=VNEG, cfg_scale=0.5)
        if tail: pl['tail_image_url'] = f'@file:gen/v3/stills/{tail}.jpg'
        vj.append(dict(id=k, endpoint=EP, out=f'gen/v3/video/{k}', payload=pl))
    json.dump(vj, open('gen/v3/video.json', 'w'), indent=1)
