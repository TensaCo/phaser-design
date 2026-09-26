"""v2 cast, white studio and garage re-shoots. Mei-Lin Zhou (Chief Scientist, PHASER) and Diane Kowalski (CEO) are
TensaCo's AI-agent personas (tensaco.ai/company/leadership); their faces come from their site headshots."""
import json, sys
sys.path.insert(0, 'src')
from prompts_scenes import PH, GARAGE, R0, R3, GM, NEG, DOC

MEILIN = ("Mei-Lin Zhou, a 23-year-old Chinese-American woman, the young research lead of a deep-tech startup: chin-length black bob, "
          "thin silver wire-rim round glasses, clear skin with natural texture and a few faint freckles, bright curious eyes, quick amused smile")
ML_STUDIO = "wearing a plain black fitted crewneck T-shirt"
ML_GARAGE = "wearing a charcoal crewneck sweater with the sleeves pushed up to the forearms and a plain steel wristwatch on her left wrist"
DIANE = ("Diane Kowalski, a 28-year-old Korean-American woman, CEO of a deep-tech startup, strikingly attractive and composed: long straight "
         "black hair tucked behind one ear, small gold hoop earrings, natural makeup, warm confident expression")
DK_STUDIO = "wearing an ivory ribbed knit sweater"
B1 = ("a Black man in his mid forties, head of inference at an AI company, close-cropped hair with some grey, short neat beard, "
      "navy cotton overshirt over a grey T-shirt")
STUDIO = ("a white cyclorama interview studio: seamless soft white walls and floor curving into each other, one large diffused key light "
          "from camera left, gentle white bounce fill, subtle natural falloff to light grey behind the subject, a simple light-oak chair; "
          "at the edge of frame, a white matte plinth with the small PHASER optical assembly on it, softly out of focus")
LOOK = ("Premium product-film interview still, shot on ARRI Alexa 35 with a Cooke S7 prime, natural skin texture with pores, real "
        "human proportions and hands, subtle film grain, soft highlight rolloff, calm expensive minimalism like a top industrial "
        "design company's launch film. No text, no logos, no readable writing.")
CML, CDK, CB1 = "@file:gen/v2/char/meilin.png", "@file:gen/v2/char/diane.png", "@file:gen/char/b1.png"
SM = "@file:gen/v2/stills/s-studio-master.png"

def E(id, prompt, refs, ar="16:9"):
    return dict(id=id, endpoint="fal-ai/nano-banana-pro/edit", out=f"gen/v2/stills/{id}",
                payload=dict(prompt=prompt, image_urls=refs, aspect_ratio=ar, resolution="2K"))

chars = [
 E("char-meilin", f"Character reference sheet: three views side by side (front, three-quarter, profile) of the woman in the reference photo, same face exactly: {MEILIN}, {ML_STUDIO}. Neutral light-grey background, soft even light. {LOOK}", ["@file:gen/v2/heads/meilin-final.png"]),
 E("char-diane", f"Character reference sheet: three views side by side (front, three-quarter, profile) of the woman in the reference photo, same face exactly: {DIANE}, {DK_STUDIO}. Neutral light-grey background, soft even light. {LOOK}", ["@file:gen/v2/heads/diane-final.png"]),
 E("s-studio-master", f"Wide establishing frame, 35mm lens, of {STUDIO}. The chair is empty. The optical assembly on the plinth is EXACTLY the one in the reference image (keep its design: black kinematic mirror mount with two knurled knobs, exactly four thin plate cells on two steel rods, copper heatsink, dev board), small, about 8 cm tall. Film lights on stands just visible at the frame edges. {LOOK}", [R0]),
]
stills = [
 # Mei-Lin, direct address (founder energy)
 E("s-ml-direct-cu", f"Tight close-up, 85mm lens at eye level, of {MEILIN}, {ML_STUDIO} (same face as the first reference), seated in the white studio (second reference), looking straight into the lens with calm, intense conviction, mid-sentence, a hint of a smile. Background soft white. {LOOK}", [CML, SM]),
 E("s-ml-direct-mcu", f"Medium close-up, 65mm lens at eye level, of {MEILIN}, {ML_STUDIO} (same face as the first reference), seated on the oak chair in the white studio (second reference), leaning slightly forward, forearms on knees, looking straight into the lens, confident and warm. The optical assembly on its plinth is softly out of focus at frame right. {LOOK}", [CML, SM]),
 # Mei-Lin, interview 3/4
 E("s-ml-34", f"Interview frame, 50mm lens, subject placed on the right third: {MEILIN}, {ML_STUDIO} (same face as the first reference) sits on the oak chair in the white studio (second reference), body angled toward an interviewer just left of camera, eyes to the interviewer (not the lens), mid-sentence and amused, one hand gesturing. The PHASER assembly on its white plinth softly out of focus at frame left. {LOOK}", [CML, SM]),
 # Diane
 E("s-dk-34", f"Interview frame, 50mm lens, subject on the left third: {DIANE}, {DK_STUDIO} (same face as the first reference) sits on the oak chair in the white studio (second reference), angled toward an interviewer just right of camera, eyes to the interviewer, telling a story with a small knowing smile, hands relaxed. {LOOK}", [CDK, SM]),
 E("s-dk-cu", f"Close-up from a second camera at a 45-degree angle, 100mm lens: {DIANE}, {DK_STUDIO} (same face as the first reference) in the white studio, laughing softly while telling a story, eyes toward the interviewer off-camera. Background soft white. {LOOK}", [CDK, SM]),
 E("s-dk-direct", f"Medium close-up, 65mm lens at eye level: {DIANE}, {DK_STUDIO} (same face as the first reference), seated in the white studio (second reference), looking straight into the lens, calm and certain. {LOOK}", [CDK, SM]),
 # customer
 E("s-b1-34", f"Interview frame, 50mm lens, subject on the right third: {B1} (same face and clothes as the first reference) sits on the oak chair in the white studio (second reference), angled toward an interviewer left of camera, relaxed, mid-sentence, a small grin. {LOOK}", [CB1, SM]),
 # garage re-shoots with Mei-Lin
 E("g2-laugh", f"Documentary medium close-up, 50mm lens, handheld: {MEILIN}, {ML_GARAGE} (same face as the first reference) laughing mid-sentence while holding up an old crude prototype: a grey 3D-printed vertical frame with zip ties and hot glue holding small glass squares. Same garage lab as the second reference, warm practical light, shelves soft behind. " + DOC + NEG, [CML, GM]),
 E("g2-monitor", f"Over-the-shoulder documentary shot, 40mm lens: {MEILIN}, {ML_GARAGE} (first reference; seen from behind her right shoulder, black bob visible) looks at a monitor on the garage bench showing two side-by-side square grids of red speckle interference patterns on black (soft, no text), the optical assembly (second reference) in the foreground left, slightly soft. Warm lamp, late night. " + DOC + NEG, [CML, R0, GM]),
 E("g2-wide", f"Wide documentary establishing shot, 28mm lens, from the side door of the garage lab (first reference) at night: {MEILIN}, {ML_GARAGE} (second reference) sits at the far bench in a pool of warm lamp light, small in frame, absorbed in her work beside the assembly; a bicycle in the corner. Quiet, late. " + DOC + NEG, [GM, CML]),
 E("g2-bench-night", f"Documentary medium shot, 35mm lens, handheld: {MEILIN}, {ML_GARAGE} (first reference) at the garage bench at 2 a.m., hands behind her head, leaning back on a shop stool, looking at the small optical assembly glowing faint red on the breadboard (second reference, exactly four plate cells), a slow satisfied smile. Empty coffee mugs, notebook, hex keys. Warm lamp. " + DOC + NEG, [CML, R0, GM]),
]
# motion (Kling 2.5 turbo pro image-to-video); lip-sync is applied afterwards to the talking takes
from prompts_video import EP, NEG as VNEG, HAND, LOCK, TRUCK
STICKS = "Camera: on sticks, nearly static, only the faintest drift, no zoom. "
VIDEO = {
 'v2-ml-cu-a': ('s-ml-direct-cu', '5', STICKS + "She speaks to the lens with calm conviction, small natural head movements, one blink, a slight smile at the end. Background stays soft white."),
 'v2-ml-cu-b': ('s-ml-direct-cu', '5', STICKS + "She pauses, then says something short and certain to the lens, a hint of a smile; natural breathing."),
 'v2-ml-mcu': ('s-ml-direct-mcu', '5', STICKS + "She leans forward slightly and speaks directly to the lens, forearms on her knees, calm and certain. The optical assembly behind stays perfectly still and unchanged."),
 'v2-ml-34': ('s-ml-34', '5', STICKS + "She talks to the interviewer off camera left with an amused expression, a small hand gesture, natural."),
 'v2-dk-34': ('s-dk-34', '10', STICKS + "She tells a story to the interviewer off camera right, relaxed, small hand movements, a knowing smile."),
 'v2-dk-cu': ('s-dk-cu', '10', STICKS + "She laughs softly while telling the story, glances down, then back to the interviewer, still smiling."),
 'v2-dk-direct': ('s-dk-direct', '10', STICKS + "She speaks straight to the lens, composed and certain, small nods, natural blinking."),
 'v2-b1': ('s-b1-34', '5', STICKS + "He speaks to the interviewer off camera left, relaxed, a small grin and a shrug."),
 'v2-laugh': ('g2-laugh', '10', HAND + "She laughs and talks to the interviewer, tilting the crude grey prototype slightly to show it, then lowers it a little. Natural, candid."),
 'v2-monitor': ('g2-monitor', '10', HAND + "She sits very still looking at the monitor, then slowly leans back, exhales and keeps looking, a small smile. The red patterns stay steady. Assembly unchanged."),
 'v2-wide': ('g2-wide', '5', "Camera: very slow handheld push from the doorway. She works quietly at the far bench; the garage is still."),
 'v2-bench-night': ('g2-bench-night', '5', HAND + "She leans back on the stool with her hands behind her head and smiles at the glowing assembly; nothing else moves. Assembly unchanged."),
 'v2-studio-wide': ('s-studio-master', '5', "Camera: very slow smooth dolly forward. The empty white studio; nothing moves except faint light flicker on the lamp."),
}

if __name__ == '__main__':
    vjobs = [dict(id=k, endpoint=EP, out=f'gen/v2/video/{k}', payload=dict(prompt=p, image_url=f'@file:gen/v2/stills/{s}.jpg', duration=d, negative_prompt=VNEG, cfg_scale=0.5)) for k, (s, d, p) in VIDEO.items()]
    json.dump(vjobs, open('gen/v2/video.json', 'w'), indent=1)
    json.dump(chars, open('gen/v2/chars.json', 'w'), indent=1)
    json.dump(stills, open('gen/v2/stills.json', 'w'), indent=1)
