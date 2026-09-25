"""Image-to-video motion specs for every generated still (Kling 2.5 turbo pro via fal)."""
import json
EP = 'fal-ai/kling-video/v2.5-turbo/pro/image-to-video'
NEG = ("morphing, warping hardware, extra fingers, deformed hands, face distortion, identity change, text, subtitles, logos, "
       "neon, lens flare, smoke, fast camera movement, zoom, cuts, scene change, cartoon, CGI look, oversaturated")
HAND = "Camera: handheld documentary, nearly static, only subtle 1-2 cm natural drift, no zoom. "
LOCK = "Camera: locked-off tripod, perfectly still. "
TRUCK = "Camera: very slow smooth lateral dolly move of a few centimetres, no zoom. "
V = {
 # (still, duration, prompt)
 'v-cooling': ('g-cooling', '5', TRUCK + "Faint heat shimmer rises off the copper cold plate; a single drop of condensation slides on a hose fitting. Nothing else moves."),
 'v-e1': ('g-e1-interview', '10', HAND + "The woman talks naturally to the interviewer off camera left, small head movements, occasional glance down at the optical assembly on the bench, turns the hex key in her fingers, a small smile. The optical assembly stays perfectly still and unchanged."),
 'v-e2': ('g-e2-adjuster', '5', LOCK + "The fingertips turn the knurled knob very slowly by a tiny fraction of a turn, pause, then release. The metal assembly itself does not move or change shape. Faint red glow stays constant."),
 'v-e3': ('g-e3-laugh', '10', HAND + "She laughs and talks to the interviewer, tilting the crude grey prototype slightly in her hands to show it, then lowers it a little. Natural, candid."),
 'v-e4': ('g-e4-shelf', '5', TRUCK + "Static objects on the shelf, a hand reaches in and picks up one small grey 3D-printed mount, then leaves frame."),
 'v-e5': ('g-e5-inspect', '5', HAND + "She leans a little closer to the glass plates, eyes focusing, blinks once, then eases back slightly. The optical assembly stays perfectly still and unchanged, faint red light steady."),
 'v-e6': ('g-e6-monitor', '5', HAND + "She leans toward the monitor, rests her chin on her hand, and looks between the monitor and the optical assembly. The red patterns on the screen flicker subtly. Assembly unchanged."),
 'v-e7': ('g-e7-clean', '5', LOCK + "The hands slowly draw the small glass plate across the lens tissue once with the tweezers, then lift it to the light to check it."),
 'v-e8': ('g-e8-wide', '5', "Camera: very slow push forward of a few centimetres from the doorway, handheld. The woman at the far bench works quietly, small hand movements; the rest of the garage is still."),
 'v-b1': ('g-b1-interview', '10', HAND + "The man speaks to the interviewer off camera left, relaxed, small nods and hand gestures on the table, a brief smile. Office background people move slightly out of focus."),
 'v-b2': ('g-b2-interview', '10', HAND + "The woman speaks to the interviewer off camera right with a wry smile, small hand gestures, shakes her head slightly in disbelief. Colleague in background types."),
 'v-b3': ('g-b2-laptop', '10', HAND + "She laughs in surprise looking at the laptop, lowers her hand from her mouth, and says something to the colleague beside her, still smiling."),
 'v-b4': ('g-b1-desk', '5', HAND + "The seated engineer types briefly; the standing man leans in toward the monitors. The small optical assembly on the desk stays perfectly still and unchanged."),
 'v-rack': ('g-rack', '5', "Camera: very slow smooth dolly forward down the aisle. The technician in the distance works at the rack. Cable and lights still."),
 'v-transformer': ('g-transformer', '5', LOCK + "The worker stands still, shifts weight slightly; faint heat haze above the radiator fins; overcast sky moves slowly."),
 'v-hospital': ('g-hospital', '5', HAND + "The nurse walks slowly away down the corridor. Monitor lights blink softly."),
 'v-icu': ('g-icu', '5', LOCK + "The gloved hand turns the dial slightly and withdraws. The monitor waveform moves steadily."),
 'v-water': ('g-water', '5', LOCK + "The pumps run with a slight vibration; the operator walks slowly across the far background."),
 'v-greenhouse': ('g-greenhouse', '5', TRUCK + "The worker in the distance tends a plant; faint mist drifts in the warm light."),
 'v-cold': ('g-cold', '5', LOCK + "The forklift moves slowly forward; frosty air drifts from the ceiling evaporators."),
 'v-grocery': ('g-grocery', '5', LOCK + "The adult taps the card on the payment terminal; the child's hand shifts on the counter."),
 'v-home': ('g-home', '5', LOCK + "Light snow falls slowly; a window light flickers as someone moves inside; the heat pump fan turns."),
 'v-steel': ('g-steel', '5', LOCK + "Molten steel pours steadily from the ladle with sparks; the worker in heat gear stands still at a distance."),
 'v-city': ('g-city', '5', "Camera: extremely slow smooth push forward. City lights twinkle faintly; the red aviation lights on the towers blink slowly."),
}
# second pass (edit gaps found while laying out the cut)
V.update({
 'v-e9': ('g-e9-notebook', '5', HAND + "She writes a few more numbers in the notebook, pauses, taps the pencil, glances at the optical assembly, writes again. Assembly unchanged."),
 'v-e10': ('g-e10-switch', '5', LOCK + "The hand pushes the USB-C plug into the board and withdraws; a moment later a faint red glow appears between the glass plates and stays steady. The assembly does not move or change."),
 'v-b5': ('g-b5-opsroom', '5', HAND + "The woman walks slowly between the desks with her mug; operators type. Nothing dramatic."),
 'v-b7': ('g-b7-office', '5', HAND + "The woman at her desk leans back and smiles at her screen; the man walks past behind with his laptop. Ordinary office motion."),
 'v-b8': ('g-b8-enter', '5', LOCK + "The finger presses the return key once and the hand rests. The screen softly changes brightness."),
 'v-e6b': ('g-e6-monitor', '10', HAND + "She sits very still looking at the monitor, then slowly leans back in her chair, exhales, and keeps looking; a small smile. The red patterns on the screen stay steady. Assembly unchanged."),
})
if __name__ == '__main__':
    jobs = [dict(id=k, endpoint=EP, out=f'gen/video/{k}', payload=dict(prompt=p, image_url=f'@file:gen/stills/{s}.jpg', duration=d, negative_prompt=NEG, cfg_scale=0.5)) for k, (s, d, p) in V.items()]
    json.dump(jobs, open('gen/video.json', 'w'), indent=1)
