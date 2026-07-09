# Welcome to Sonic Pi
# Vagusnerv-Stimulation (VNS): von 4 bis 7 Hz und zurück
# 4 bis 7 Hz bedeutet 4 bis 7 Impulse in der Minute

use_debug false
use_synth_defaults debug: false
set :scopes, false

set :bpm, 60 # use_bpm 60

# Vagusnerv-Stimulation (VNS)
with_fx :reverb, room: 0.7, mix: 0.5 do
  live_loop :vagus_drum do
    
    # wir steuern die Zeit direkt über sleep (realtime)
    use_arg_bpm_scaling false
    
    # von 4 bis 7 Hz
    (4.0..7.0).step(0.1).each do |i|
      play choose([:c2, :d2, :g1]), release: 0.15, cutoff: rrand(70, 120), amp: 1
      sleep rt(1.0) / i
    end
    
    # von 7 bis 4 Hz
    (7.0..4.0).step(-0.1).each do |i|
      play choose([:c2, :d2, :g1]), release: 0.15, cutoff: rrand(70, 120), amp: 1
      sleep rt(1.0) / i
    end
    
  end
end

# Sphere
with_fx :slicer, phase: 16, mix: 0.15 do
  with_fx :wobble, phase: 8, mix: 0.3 do
    live_loop :sphere do
      #sync :vagus
      use_synth :dark_ambience
      # weiche Lautstärkewelle
      amp_wave = (range 0.1, 0.3, step: 0.01).mirror.tick
      play :e2, sustain: 8, release: 4, amp: amp_wave, cutoff: rrand(60, 90)
      sleep [8].choose # orig: 8
    end
  end
end
