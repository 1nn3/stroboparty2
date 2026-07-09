# Welcome to Sonic Pi
# Letz make a solid Psytrance 140‑BPM‑Acid‑Kick‑Loop
# https://de.wikipedia.org/wiki/Psytrance
# Die Musik setzt sich aus 4/4-Takten zwischen ursprünglich 130 bis 150 BPM zusammen,
# mittlerweile werden auch Geschwindigkeiten bis zu 180 BPM und mehr erreicht
# Beliebt sind Acid-Trance-Linien; ursprünglich durch den TB303-Synthesizer
# und andere organisch klingende synthetische Geräusche

use_debug false
use_synth_defaults debug: false
set :scopes, false

set :bpm, 140 # use_bpm 140

with_fx :lpf do # low pass filter: only keep the bass
  live_loop :psy_line do
    use_bpm get(:bpm)
    use_synth :tb303
    # Simpler 4‑Noten‑Loop
    sample :bd_tek, amp: 1.0, cutoff: 70
    # Das ist ein eingebauter Drum‑Sample in Sonic Pi – konkret ein House‑Kickdrum‑Sound
    # Andere sind z.B. :bd_tek typisch für Techno
    # amp: Lautstärke. Lauter als 1.0 verschlechtert die Soundqualität
    sleep 0.25
    # pauses the current thread for a given number of beats
    # because Sonic Pi is beat‑based, not time‑based,
    # the duration depends on the current BPM
    
    sample :bd_tek, amp: 0.25
    sleep 0.25
    
    sample :bd_tek, amp: 0.75 # bass line
    sleep 0.25
    
    sample :bd_tek, amp: 0.5, cutoff: 110
    sleep 0.25
  end
end

# BPM-Wave (Fade)
live_loop :bpm_wave do
  sync :psy_line
  start = get(:bpm) || 140
  stop  = rrand(130, 150)
  steps = [16,32,64].choose # orig: 64
  duration = [128].choose # orig: 128
  steps.times do |i|
    t = i.to_f / (steps - 1)
    curve = t ** 2 # quadratische Kurve
    bpm = start + (stop - start) * curve
    set :bpm, bpm
    sleep duration.to_f / steps
  end
  sleep rrand(0, [16,32,64,128,256].choose)
end

live_loop :bpm_logger do
  puts "Current BPM: #{get(:bpm)}"
  sleep 1
end
