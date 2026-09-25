# Sound design specification

All non-voice sound is synthesized in `src/audio.py` (no library music, no samples), so there is nothing to license.
Voices: ElevenLabs v3 via fal (AI). The mix is loudness-normalised to −16 LUFS integrated, −1.5 dBTP.

## By act

| Act | Bed | Events | Score |
|---|---|---|---|
| 1 Physical limit | near silence → electrical texture (60 Hz hum + harmonics, low brown noise, crackle that rises with the lattice heat); fan roar on the cooling cut; hard silence on black | — | none |
| 2 Reveal | studio air (−66 dB) | **optical transient**: clean glassy partials 1760/2640/3520/5280 Hz, 4 ms attack, 0.9 s decay, long bright reverb, a soft 55 Hz body; **cavity ticks** (3.5 kHz) once per displayed round trip, accelerating into a tone on the multiplexing shot | pad enters at 50–65 % |
| 3 Engineer | garage room tone (pink noise 60–1800 Hz, faint 60 Hz fridge hum, rare ticks); voices get a short room reverb | knurled-adjuster clicks, USB-C plug, soft optical tone at switch-on | none (music drops out under the engineer) |
| 4 Business | office HVAC + sporadic keyboard | a return-key click | low pad (30–35 %) ducked under speech |
| 5 Outward | datacenter fans + 120 Hz; **transformer hum** (120 Hz with harmonics, slow beat); wind on the transmission lines | — | low |
| 6 Human stakes | hospital ventilation and a soft monitor beep; pump drone; refrigeration hum; store; mill roar | — | pad opens to 55–65 %, never piano, never percussion |
| 7 Resolution | studio air; city rumble | soft optical tone | pad up to 75 %; the **PHASER tone** (a clean A5 with slow shimmer) grows over the last ~50 s |
| 8 End frame | near silence | one optical transient, a final soft one | falls away; the last 1.2 s fade to silence |

## Score
Additive pad: each chord voice is a sine with ±0.3 % detuned copies and a quiet octave, 2.5 s attack, 2 s release,
band-limited 60–2200 Hz; chords D–B♭–F–C (open voicings), 8 s each. The score is ducked 45 % under any voice.

## Stems (master)
`out/stems/dialogue.wav`, `narration.wav`, `music.wav`, `effects-ambience.wav` (48 kHz stereo float, pre-loudnorm; they sum
to the master mix before normalisation).
