import json
DOC = ("Documentary film still, shot on a cinema camera, natural skin texture with pores and small imperfections, realistic "
       "proportions and hands, subtle film grain, natural colour, no text, no logos, no brand names, no readable writing anywhere.")
ENG = ("an optical engineer, a South Asian woman in her early thirties, dark hair tied back loosely with a few loose strands, "
       "thin black-framed glasses, charcoal crewneck sweater with sleeves pushed to the forearms, a plain steel wristwatch on her left wrist, "
       "no makeup look, tired but amused eyes")
B1 = ("a Black man in his mid forties, head of inference at an AI company, close-cropped hair with some grey, short neat beard, "
      "navy cotton overshirt over a grey t-shirt, no tie")
B2 = ("a white woman in her mid fifties who runs datacenter infrastructure, grey chin-length bob, reading glasses pushed up on her head, "
      "dark green quarter-zip fleece over a light blue button-down shirt")
jobs = [
 dict(id="char-eng", endpoint="fal-ai/nano-banana-pro", out="gen/char/eng",
      payload=dict(prompt=f"Character reference: three views side by side (front, three-quarter, profile) of {ENG}. Neutral grey background, soft even light. {DOC}", aspect_ratio="16:9", resolution="2K")),
 dict(id="char-b1", endpoint="fal-ai/nano-banana-pro", out="gen/char/b1",
      payload=dict(prompt=f"Character reference: three views side by side (front, three-quarter, profile) of {B1}. Neutral grey background, soft even light. {DOC}", aspect_ratio="16:9", resolution="2K")),
 dict(id="char-b2", endpoint="fal-ai/nano-banana-pro", out="gen/char/b2",
      payload=dict(prompt=f"Character reference: three views side by side (front, three-quarter, profile) of {B2}. Neutral grey background, soft even light. {DOC}", aspect_ratio="16:9", resolution="2K")),
]
if __name__ == '__main__': json.dump(jobs, open('gen/chars.json', 'w'), indent=1)
