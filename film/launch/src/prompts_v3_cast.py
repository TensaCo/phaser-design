"""v3 cast additions: Cole Mercer (CEO, TensaCo AI-agent persona) and a second dramatized customer."""
import json
COLE = ("Cole Mercer, a 31-year-old startup CEO, Silicon Valley founder archetype with grit: lean and tall, sun-browned skin, "
        "messy dark-blond hair pushed back, three-day stubble, sharp grey-blue eyes with squint lines, a small scar through his left "
        "eyebrow, restless intense energy and a knowing half-smile")
COLE_WARDROBE = "faded black crewneck T-shirt under a worn olive-green canvas field jacket, a scuffed steel diver's watch"
CUST2 = ("a Latina woman in her early thirties, head of platform at an AI startup: curly dark hair in a low bun, small gold nose stud, "
         "black blazer over a grey hoodie, quick expressive face")
LOOK = ("Natural skin texture with pores, real human proportions and hands, subtle film grain, soft highlight rolloff. "
        "No text, no logos, no readable writing.")
jobs = [
 dict(id='head-cole', endpoint='fal-ai/nano-banana-pro', out='gen/v3/heads/cole', payload=dict(aspect_ratio='4:5', resolution='2K', num_images=2,
      prompt=f"Casual phone snapshot taken by a friend on a rooftop in SoMa, San Francisco at golden hour, slightly off-center, wind in his hair. Subject: {COLE}, wearing {COLE_WARDROBE}, looking at the camera mid-laugh. Real iPhone photo look: natural colours, slight noise, not retouched, not a studio portrait. {LOOK}")),
 dict(id='char-cust2', endpoint='fal-ai/nano-banana-pro', out='gen/v3/char/cust2', payload=dict(aspect_ratio='16:9', resolution='2K',
      prompt=f"Character reference sheet: three views side by side (front, three-quarter, profile) of {CUST2}. Neutral light-grey background, soft even light. Premium documentary portrait. {LOOK}")),
]
if __name__ == '__main__': json.dump(jobs, open('gen/v3/cast.json', 'w'), indent=1)
