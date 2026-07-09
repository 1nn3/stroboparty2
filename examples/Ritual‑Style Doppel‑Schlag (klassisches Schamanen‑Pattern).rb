# Welcome to Sonic Pi
# Ritual‑Style Doppel‑Schlag (klassisches Schamanen‑Pattern)

# Vorsicht: Trommeln in Trance,
# ist mitunter Vagusnerv stimulierend (VNS)!

# Wer, wenn ich schriee, hörte mich denn aus der Engel
# Ordnungen? und gesetzt selbst, es nähme
# einer mich plötzlich ans Herz: ich verginge von seinem
# stärkeren Dasein. Denn das Schöne ist nichts
# als des Schrecklichen Anfang, den wir noch grade ertragen,
# und wir bewundern es so, weil es gelassen verschmäht,
# uns zu zerstören. Ein jeder Engel ist schrecklich.
# (Rainer Maria Rilke in Duineser Elegien)

use_debug false
use_synth_defaults debug: false
set :scopes, false

set :bpm, 60 # use_bpm 60

with_fx :lpf do # low pass filter: only keep the bass
  live_loop :shaman_drum do
    use_bpm get(:bpm)
    with_fx :reverb, room: 0.7, mix: 0.5 do
      2.times do
        sample :bd_tek, amp: rrand(1.0, 1.4), cutoff: 70
        sleep 0.12 + rrand(-0.01, 0.01)
      end
    end
    sleep 0.55 + rrand(-0.02, 0.02)
  end
end

# Sphere
with_fx :slicer, phase: 16, mix: 0.15 do
  with_fx :wobble, phase: 8, mix: 0.3 do
    live_loop :sphere do
      #sync :shaman_drum
      use_synth :dark_ambience
      # weiche Lautstärkewelle
      amp_wave = (range 0.1, 0.3, step: 0.01).mirror.tick
      play :e2, sustain: 8, release: 4, amp: amp_wave, cutoff: rrand(60, 90)
      sleep [8].choose # orig: 8
    end
  end
end

# BPM-Fade
live_loop :bpm_fade, sync: :shaman_drum do
  start = get(:bpm)
  stop  = rrand(30, 90)
  steps = [16,32,64].choose # orig: 64
  duration = [128].choose # orig: 128
  steps.times do |i|
    t = i.to_f / (steps - 1)
    curve = t ** 2 # quadratische Kurve
    bpm = start + (stop - start) * curve
    set :bpm, bpm
    sleep duration.to_f / steps
  end
  sleep rrand(0, 256)
end
