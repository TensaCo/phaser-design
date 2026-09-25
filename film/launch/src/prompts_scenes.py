"""Every still-generation prompt for the film (nano-banana-pro edit with reference images). The stills become the first
frames of image-to-video shots (prompts_video.py)."""
import json
from prompts_chars import DOC, ENG, B1, B2
PH = ("EXACTLY the optical assembly in the product reference image, unchanged in design, proportions, parts and colours: "
      "a vertical stack about 8 cm tall — a black anodised kinematic mirror mount with two black knurled adjuster knobs on top, "
      "four thin black anodised plate cells holding small square glass plates on two brushed steel rods, a small copper heatsink "
      "with a silver-and-gold laser diode can and hand-twisted white wires, a black camera lens barrel below, all standing on a "
      "black dev board with gold header pins. A faint red glow between the glass plates. It is small, the size of a coffee mug")
GARAGE = ("a residential two-car garage converted into a hardware lab at night: heavy worn wooden workbench, a black optical "
          "breadboard with a grid of tapped holes, pegboard with hand tools, grey steel shelving with clear plastic parts bins "
          "labelled with blank masking tape, plain unbranded brown cardboard boxes, a small bench oscilloscope, grey 3D-printed "
          "fixtures and older mount prototypes, a whiteboard with a hand-drawn diagram of a vertical cavity with four horizontal "
          "lines (out of focus), coffee mug, hex keys, digital caliper, lens tissue, anti-static mat. Warm 3200K practical task lamp, "
          "a neutral (not blue) monitor glow, painted drywall, concrete floor")
R0, R1, R3 = "@file:assets/ref/phaser-ref-0.jpg", "@file:assets/ref/phaser-ref-1.jpg", "@file:assets/ref/phaser-ref-3.jpg"
CE, CB1, CB2 = "@file:gen/char/eng.png", "@file:gen/char/b1.png", "@file:gen/char/b2.png"
GM = "@file:gen/stills/g-garage-master.png"
NEG = " No neon, no cyberpunk, no blue or teal grading, no holograms, no smoke, no lens flares, no brand logos, no readable text."

def S(id, prompt, refs, ar="16:9"):
    return dict(id=id, endpoint="fal-ai/nano-banana-pro/edit", out=f"gen/stills/{id}",
                payload=dict(prompt=prompt + " " + DOC + NEG, image_urls=refs, aspect_ratio=ar, resolution="2K"))
def T(id, prompt, ar="16:9"):
    return dict(id=id, endpoint="fal-ai/nano-banana-pro", out=f"gen/stills/{id}",
                payload=dict(prompt=prompt + " " + DOC + NEG, aspect_ratio=ar, resolution="2K"))

first = [S("g-garage-master", f"Wide documentary photograph, 28mm lens at standing eye height, of {GARAGE}. On the breadboard in the middle of the bench sits {PH}. No people. Deep, natural depth of field, slightly messy, lived-in.", [R0])]

garage = [
 S("g-e1-interview", f"Documentary interview frame, 50mm lens at seated eye height, 1.8 m away. In the garage lab of the second reference image, {ENG} (first reference image: same face, glasses, sweater, watch) sits on a shop stool at the bench, body turned 30 degrees toward an interviewer just left of camera, mid-sentence, holding a small hex key loosely. On the breadboard at the right of frame is {PH} (third reference image). Warm task lamp from camera right lights her hands and the glass; soft neutral monitor fill from camera left. Background shelves softly out of focus.", [CE, GM, R0]),
 S("g-e2-adjuster", f"Macro photograph, 100mm macro lens, of a woman's fingertips (charcoal sweater cuff, plain steel watch visible) turning one black knurled adjuster knob on top of the kinematic mirror mount of {PH} (reference image, seen close from the side). Tiny faint red light visible between the glass plate cells below. Warm task lamp, black breadboard, shallow depth of field, fingerprints and fine wear on the anodised metal.", [R3, CE]),
 S("g-e3-laugh", f"Documentary medium close-up, 50mm lens, of {ENG} (first reference image) laughing mid-sentence while holding up an old crude prototype: a grey 3D-printed vertical frame with zip ties and hot glue holding small glass squares — clearly an earlier, rougher version of the assembly in the third reference image. Same garage lab (second reference), warm practical light, shelves out of focus behind.", [CE, GM, R0]),
 S("g-e4-shelf", f"Documentary detail shot, 50mm lens, of a grey steel shelf in the garage lab (reference image): older mount prototypes in grey and black 3D-printed plastic, a few small square glass plates in a labelled clear tray, two earlier aluminium plate cells with scratches, an alignment target card with concentric circles, blank masking-tape labels, a roll of kapton tape. Warm practical light, shallow depth of field.", [GM]),
 S("g-e5-inspect", f"Documentary close shot, 85mm lens, low at bench height: {ENG} (first reference image) leans very close to {PH} (second reference image), inspecting the glass plate cells through her glasses, one hand steadying her elbow on the bench; faint red light from the plates catches her glasses and cheek. Warm task lamp, dark background.", [CE, R3]),
 S("g-e6-monitor", f"Over-the-shoulder documentary shot, 40mm lens: {ENG} (first reference image, seen from behind her right shoulder) looks at a monitor on the garage bench showing two side-by-side square grids of red speckle interference patterns on black (out of focus, no text), while {PH} (second reference image) sits in the foreground left, slightly soft. Warm lamp, dim garage.", [CE, R0, GM]),
 S("g-e7-clean", f"Macro photograph, 100mm lens: a woman's hands (charcoal sweater cuffs, steel watch) hold a 5 mm square glass phase plate with plastic tweezers over lens tissue on a black anti-static mat; the plate's surface shows a faint fine pixel grid relief catching the warm light. Shallow depth of field, real dust and fibres.", [CE]),
 S("g-e8-wide", f"Wide documentary establishing shot, 28mm lens from the open side door of the garage lab (reference image) at night: {ENG} (second reference image) sits at the far bench in a pool of warm lamp light, small and absorbed in her work beside the assembly; the rest of the garage dim; a bicycle and a lawnmower pushed into a corner. Quiet, late.", [GM, CE]),
]

business = [
 S("g-b1-interview", f"Documentary interview frame, 65mm lens at seated eye height: {B1} (reference image: same face and clothes) sits in a plain glass-walled meeting room of an AI company, body angled toward an interviewer left of camera, mid-sentence, relaxed, one forearm on the table. Behind him out of focus: an ordinary open-plan office with desks and people working. Soft overcast daylight from windows, realistic, no posing.", [CB1]),
 S("g-b2-interview", f"Documentary interview frame, 65mm lens at seated eye height: {B2} (reference image: same face, clothes, glasses on head) sits in a datacenter operations room, angled toward an interviewer right of camera, mid-sentence with a slight wry smile. Behind her out of focus: desks with monitors and one colleague; fluorescent and monitor light, neutral colour, ordinary room.", [CB2]),
 S("g-b2-laptop", f"Documentary medium shot, 50mm lens: {B2} (reference image) at her desk in the same operations room, leaning back from a laptop with a surprised half-laugh, hand at her mouth, looking at the screen (screen not visible to camera). A colleague's arm at the frame edge. Natural office light.", [CB2]),
 S("g-b1-desk", f"Documentary medium-wide shot, 35mm lens: {B1} (first reference image) stands behind a seated engineer at a desk in the AI company office, both looking at two monitors whose content is out of focus soft charts. On the desk beside the monitors, connected by a USB-C cable to a small black enclosure, sits {PH} (second reference image), small in frame. Overcast daylight.", [CB1, R0]),
]

world = [
 T("g-cooling", "Extreme macro photograph, 100mm lens, of a GPU server's liquid cooling cold plate with copper microfins, braided coolant hoses and quick-disconnect fittings inside a dark server chassis, faint heat shimmer, a single warm white work light raking across the metal. Industrial, real, dusty."),
 T("g-hospital", "Documentary photograph, 35mm lens, of a quiet hospital corridor at night: a nurse in navy scrubs walking away from camera past an intensive-care room doorway, a ventilator and patient monitor visible inside softly out of focus, no patient visible. Fluorescent light, ordinary, calm."),
 T("g-icu", "Documentary close detail, 85mm lens: the side of a hospital ventilator and a bedside monitor in a dim intensive care room, power cables running to a wall outlet panel, a nurse's gloved hand adjusting a dial at the edge of frame. No patient visible, no faces."),
 T("g-water", "Documentary photograph, 28mm lens, of the interior of a municipal water pumping station: a row of large blue-grey centrifugal pumps and motors on a concrete floor, painted pipes, an operator walking past in the far background. Flat industrial light, Bernd and Hilla Becher sobriety."),
 T("g-greenhouse", "Documentary photograph, 35mm lens, of a commercial vegetable greenhouse at dusk, rows of tomato plants under warm sodium grow lights, irrigation lines along the floor, one worker in the distance. Natural, unglamorous."),
 T("g-cold", "Documentary photograph, 28mm lens, of a cold-chain food warehouse: tall racks of palletised produce, frosty air, refrigeration evaporator units on the ceiling, a forklift operator in a thermal jacket. Cool but neutral white light."),
 T("g-grocery", "Documentary close shot, 50mm lens, of hands at a supermarket checkout: a parent paying with a card while a child's hand rests on the counter, groceries (bread, vegetables, milk) on the belt, no faces visible. Ordinary store lighting."),
 T("g-home", "Documentary photograph, 35mm lens, of a row of modest houses at winter dusk, warm lights in windows, a heat pump unit and an electricity meter on a side wall, overhead power lines, light snow. Quiet."),
 T("g-steel", "Documentary photograph, 50mm lens, of an electric arc furnace steel mill: molten steel pouring from a ladle with bright orange sparks, a worker in silver heat-protective gear at a safe distance, dark industrial hall. Real, not stylised."),
 T("g-rack", "Documentary photograph, 35mm lens, looking down a hot aisle of dense AI accelerator server racks with thick power cables and overhead busways, white LED lighting, a technician kneeling at a rack in the distance. Real, unglamorous, no blue tint."),
 T("g-transformer", "Documentary photograph, 35mm lens, frontal and flat, of a single large high-voltage power transformer in a substation on an overcast day: grey tank, radiator fins, porcelain bushings, a person in a hard hat and hi-vis standing beside it for scale. Becher-style sobriety."),
 T("g-city", "Aerial night photograph, 35mm lens from a high hillside, of a large city grid at night: streets of warm sodium and white lights, a dark river, a transmission line crossing the foreground with small red aviation warning lights on the towers. Restrained, real, no teal-orange."),
]

if __name__ == '__main__':
    json.dump(first, open('gen/stills-first.json', 'w'), indent=1)
    json.dump(garage + business + world, open('gen/stills.json', 'w'), indent=1)
