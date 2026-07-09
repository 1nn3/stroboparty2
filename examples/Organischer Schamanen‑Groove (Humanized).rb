# Welcome to Sonic Pi
# Organischer Schamanen‑Groove (Humanized)

# Weißt du zu ritzen?
# Weißt du zu raten?
# Weißt du zu färben?
# Weißt du zu fragen?
# Weißt du zu wünschen?
# Weißt du zu weihen?
# Weißt du zu schicken?
# Weißt du zu schlachten?
# (Nach Felix Genzmer, Die Edda)

use_debug false
use_synth_defaults debug: false
set :scopes, false

set :bpm, 60 # use_bpm 60

with_fx :reverb, room: 0.6, mix: 0.4 do
  live_loop :shaman_drum do
    use_bpm get(:bpm)
    sample :bd_tek, amp: rrand(0.9, 1.3), cutoff: rrand(60, 80)
    sleep 0.45 + rrand(-0.03, 0.03) # leichte Schwankung
  end
end

# Sphere
with_fx :slicer, phase: 16, mix: 0.15 do
  with_fx :wobble, phase: 8, mix: 0.3 do
    live_loop :sphere do
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
  ziel  = rrand(30, 90)
  steps = [16,32,64].choose # orig: 64
  dauer = [128].choose # orig: 128
  steps.times do |i|
    t = i.to_f / (steps - 1)
    curve = t ** 2 # quadratische Kurve
    bpm = start + (ziel - start) * curve
    set :bpm, bpm
    sleep dauer.to_f / steps
  end
  sleep rrand(0, 256)
end
