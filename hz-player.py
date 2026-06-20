#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sounddevice as sd
import soundfile as sf
import numpy as np
import pygame, asyncio, imageio
from multiprocessing import Process, Value, Event
import time, ctypes, random, argparse, sys, math
import colorsys
#from matplotlib import font_manager

# ============================================
# ⚠️ Sicherheitshinweis
# ============================================

print("⚠️ WARNING: This script simulates a strobe effect.")
print("Do not run if you are sensitive to flashing lights.")

# ============================================
# Kommandozeilenargumente
# ============================================

# Parser erstellen
parser = argparse.ArgumentParser(description="Stroboparty 🎶🎉: Argumente übergeben")
# Argument für eine Datei hinzufügen
parser.add_argument("-s", "--scale", type=int, default=100, help="Scale e.g. 10")
parser.add_argument("-d", "--device", type=int, help="Device")
parser.add_argument("-e", "--effect", type=str, help="Effect e.g. konfetti, lametta, bricks")
parser.add_argument("-i", "--inputfile", type=str, help="Pfad zur Eingabedatei (z. B. input.wav) – not implemented yet")
parser.add_argument("-r", "--record", type=str, help="Als AVI speichern – not implemented yet")
parser.add_argument("-a", "--auto-mode", type=str, help="Enable and set auto mode.")
parser.add_argument("--strobo-mode", type=str, help="Set strobo mode.")
parser.add_argument("--color-mode", type=str, help="Set color mode.")
parser.add_argument("--colors", type=str, help="Set colors.")
parser.add_argument("--hint", type=str, help="Set hint text.")
parser.add_argument("--height", type=int, default=600, help="Set window height.")
parser.add_argument("--width", type=int, default=800, help="Set window width.")
parser.add_argument("--font", type=str, default="Arial", help="Set the font.")
parser.add_argument("--no-subtext", type=bool, help="Do not print the subtext.")
parser.add_argument("--blocksize", type=int, default=512, help="The blocksize e.g. 512 (default), 1024, 2048 and so on… (Je kleiner desto genauer, aber auch Performace intensiver)")
parser.add_argument("--image", type=str, default="image.png", help="Set an image.")
# Python 3.9+
parser.add_argument("-f", "--fullscreen", action=argparse.BooleanOptionalAction, help="Enable fullscreen mode -f/--no-f")
parser.add_argument("-S", "--smoothed", action=argparse.BooleanOptionalAction, default=False, help="Enable smoothed mode -S/--no-smoothed")
parser.add_argument("-T", "--no-text", action=argparse.BooleanOptionalAction, default=False, help="Disable text -T/--no-text")
# Argumente parse
args = parser.parse_args()

# ============================================
# Devices
# ============================================

devices = sd.query_devices()
print("Alle verfügbaren Audio-Geräte:")
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']}, Eingänge: {dev['max_input_channels']}, Ausgänge: {dev['max_output_channels']}")

default_input = sd.default.device[0]
default_output = sd.default.device[1]
print(f"Standard-Eingabe: {default_input}")
print(f"Standard-Ausgabe: {default_output}")

# ============================================
# Hilfsfunktionen
# ============================================

def delay_from_freq(freq=10.0, min_delay=0, max_delay=1):
    """Berechnet den Delay (Sekunden) basierend auf der Frequenz."""
    if freq <= 0:
        freq = 10.0
    delay = 1.0 / freq
    delay = limit(delay, min_delay, max_delay)
    #print(f"〰️ Dominante Frequenz: {freq:8.2f} Hz ({delay:1.5f} s) – Band: {current_band} Amp: {current_amp}", end="\r")
    print(f"〰️ Dominante Frequenz: {freq:8.2f} Hz ({delay:1.5f} s)", end="\r")
    return delay

def limit(val, lo, hi):
    """Limit"""
    return max(lo, min(val, hi))

def random_color_rgb(r=None, g=None, b=None, min_brightness=1, max_brightness=55):
    brightness = random.randint(min_brightness, max_brightness)
    r = r or random.randint(brightness, 255)
    g = g or random.randint(brightness, 255)
    b = b or random.randint(brightness, 255)
    return (r, g, b)

def complement_color_rgb(color):
    r, g, b = color
    return (255 - r, 255 - g, 255 - b)

def complement_color_hsv(color):
    r, g, b = [c / 255 for c in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + 0.5) % 1.0   # 180° drehen
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255))

def random_color_hsv():
    h = random.random()  # Hue: 0..1
    s = random.uniform(0.5, 1)  # Sättigung
    v = random.uniform(0.7, 1)  # Helligkeit
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255))

def classify_band(freq):
    if freq < 250: return "low"
    if freq < 4000: return "mid"
    return "high"

def classify_band2(freq):
    if freq < 60: return "sub"
    if freq < 250: return "bass"
    if freq < 500: return "low-mid"
    if freq < 2000: return "mid"
    if freq < 4000: return "high-mid"
    return "high"

# ============================================
# Prozess 1: Audio-Frequenzanalyse
# ============================================

def worker_audio(freq, amp, phase, running_event, device):

    #blocksize = args.blocksize # 512 # 1024 # 2048 # Je kleiner desto genauer aber auch Performace intensiver

    def smoothed (dominant_freq=10.0,alpha=0.25):
        """Glättung"""
        if args.smoothed is False:
            return dominant_freq
        global previous_freq
        if dominant_freq <= 0:
            dominant_freq = 10.0
        smoothed = previous_freq * (1 - alpha) + dominant_freq * alpha
        previous_freq = smoothed
        return smoothed

    def audio_analyzer(device):
        """Analysiert Audio-Eingang und aktualisiert globale freq."""
        global previous_freq
        previous_freq = freq.value
        samplerate = int(sd.query_devices(device)['default_samplerate'])
        def audio_callback(indata, frames, time_info, status):
            global previous_freq
            if status:
                print("\n", status)
            chunk = indata[:, 0]
            yf = np.abs(np.fft.rfft(chunk)) # Berechnet das Amplituden-Spektrum
            xf = np.fft.rfftfreq(len(chunk), 1 / samplerate) # Entsprechende Frequenzen
            dominant_freq = xf[np.argmax(yf)] # Frequenz mit der höchsten Amplitude
            freq.value = smoothed(dominant_freq / args.scale) # Skalierung
            amp.value = np.argmax(yf) # Nur die Amplitude
            phase.value = np.argmax(np.angle(yf)) # Nur die Phase
        with sd.InputStream(channels=1,callback=audio_callback,blocksize=args.blocksize,samplerate=samplerate,device=device):
            print("\n", "🎧 Systemsound wird analysiert ... (Strg+C zum Beenden/ESC-Taste im Vollbild)")
            while running_event.is_set():
                sd.sleep(100) # 0.01

    def audio_analyzer_file(filename):
        global previous_freq
        previous_freq = freq.value
        # Datei laden
        data, samplerate = sf.read(filename)
        # Stereo -> Mono
        if len(data.shape) > 1:
            data = data[:, 0]
        # Callback für die Wiedergabe
        def audio_callback(outdata, frames, time_info, status):
            try:
                global previous_freq
                if status:
                    print("\n", status)
                start = audio_callback.frame
                stop = start + frames
                chunk = data[start:stop]
                # Ende der Datei
                if len(chunk) < frames:
                    outdata[:len(chunk), 0] = chunk
                    outdata[len(chunk):, 0] = 0
                    print("\n", "🎵 End of audio reached. Stopping playback.")
                    raise sd.CallbackStop() # Stop the callback (end playback)
                else:
                    outdata[:, 0] = chunk
                yf = np.abs(np.fft.rfft(chunk))
                xf = np.fft.rfftfreq(len(chunk), 1 / samplerate)
                dominant_freq = xf[np.argmax(yf)]        
                freq.value = smoothed(dominant_freq / args.scale) # Skalierung
                amp.value = np.argmax(yf) # Nur die Amplitude
                phase.value = np.argmax(np.angle(yf)) # Nur die Phase
                # Frame-Zähler erhöhen
                audio_callback.frame += frames
            except sd.PortAudioError as e:
                print("\n", f"PortAudio error occurred: {e}")
            except sd.CallbackStop:
                print("\n", "Callback was stopped")
                print("\n", "Audio playback finished or stopped manually.")
                running_event.clear() # stoppt die Schleife
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        audio_callback.frame = 0
        # OutputStream verwenden, um die Datei abzuspielen
        with sd.OutputStream(channels=1, callback=audio_callback,samplerate=samplerate, blocksize=args.blocksize):
            print("\n", "🎵 Audio wird abgespielt und analysiert ...")
            while running_event.is_set():
                sd.sleep(int(len(data)/samplerate))
    # Wenn Audiodatei vorhanden ist → abspielen
    if args.inputfile:
        print("\n", "WAV-Datei lesen...")
        audio_analyzer_file(args.inputfile)
    else:
        audio_analyzer(device)

# ============================================
# Prozess 2: Pygame Visualisierung
# ============================================

def worker_video(freq, amp, phase, running_event):

    # ============================================
    # Async Tasks
    # ============================================

    async def strobo_updater(state):
        """Wechselt Strobo-Farbe abhängig von Audio-Frequenz."""
        colors = [(0, 0, 0), (255, 255, 255)]
        color_index = 0
        while running_event.is_set():
            delay = delay_from_freq(freq.value)
            state["color"] = colors[color_index]
            state["delay"] = delay
            state["flip"] = random.randint(0,1)
            color_index = (color_index + 1) % 2
            await asyncio.sleep(delay)

    async def konfetti_updater(state,min_freq=0, max_freq=1):
        """Kleiner Kreis, der auf Frequenz reagiert."""
        while running_event.is_set():
            state["konfetti_freq"] = freq.value
            state["flip"] = random.randint(0,1)
            await asyncio.sleep(limit(freq.value, min_freq, max_freq))

    # ============================================
    # Hauptloop (einziger Zeichenort!)
    # ============================================

    async def main():
        global num_konfetti_previous
        pygame.init()
        WIDTH, HEIGHT = args.width or 800, args.height or 600
        if args.fullscreen is True:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            time.sleep(3)
            WIDTH, HEIGHT = screen.get_size()
        else:
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()

        #if args.font:
        #    passa
        #else:
        #    font_names = sorted({font_manager.FontProperties(fname=f).get_name() for f in font_manager.findSystemFonts()})
        #    args.font = random.choice(font_names)
        font = pygame.font.SysFont(args.font, 60, bold=True)
        font_sub = pygame.font.SysFont(args.font, 30, bold=False)
        
        pygame.display.set_caption("Stroboparty 🎶🎉")

        # Farben
        rgb_colors = [
            (255, 0, 0),     # rot
            (0, 255, 0),     # grün
            (0, 0, 255),     # blau
        ]
        bw_colors = [
            (255, 255, 255),
            (0, 0, 0),
        ]
        konfetti_colors = [
            (255, 0, 0),     # rot
            (0, 255, 0),     # grün
            (0, 0, 255),     # blau
            (255, 255, 0),   # gelb
            (255, 0, 255),   # magenta
            (0, 255, 255),   # cyan
            #(255, 255, 255), # weiß
            #(0, 0, 0),       # schwarz
        ]
        pastel_colors = [
            (255, 179, 186),
            (255, 223, 186),
            (255, 255, 186),
            (186, 255, 201),
            (186, 225, 255),
        ]
        traffic_lights_colors = [
            (255, 0, 0),     # rot
            (255, 255, 0),   # gelb
            (0, 255, 0),     # grün
        ]
        disco_colors = [
            (255, 0, 0),     # rot
            (255, 255, 0),   # gelb
            (0, 255, 0),     # grün
            (0, 0, 255),     # manchmal auch blau (DO NOT DRINK AND DRIVE!)
        ]
        # police?
        siren_colors = [
            (255, 0, 0),     # red
            (0, 0, 255),     # blue
        ]
        grayscale_colors = [(i, i, i) for i in range(256)]
        blue_colors      = [random_color_rgb(0, 0, 255) for i in range(256)]
        red_colors       = [random_color_rgb(255, 0, 0) for i in range(256)]
        green_colors     = [random_color_rgb(0, 255, 0) for i in range(256)]
        cyan_colors      = [random_color_rgb(0, 255, 255) for i in range(256)]
        magenta_colors   = [random_color_rgb(255, 0, 255) for i in range(256)]
        yellow_colors    = [random_color_rgb(255, 255, 0) for i in range(256)]

        all_colors = (konfetti_colors, bw_colors, rgb_colors, pastel_colors, grayscale_colors, blue_colors, red_colors, green_colors, cyan_colors, magenta_colors, yellow_colors,disco_colors, traffic_lights_colors)
        # arg to array/list: colorss are arrays for more performace
        match args.colors:
            case "konfetti_colors":
                colors = konfetti_colors
            case "bw_colors":
                colors = bw_colors
            case "rgb_colors":
                colors = rgb_colors
            case "pastel_colors":
                colors = pastel_colors
            case "grayscale_colors":
                colors = grayscale_colors
            case "blue_colors":
                colors = blue_colors
            case "red_colors":
                colors = red_colors
            case "cyan_colors":
                colors = cyan_colors
            case "cyan_colors":
                colors = cyan_colors
            case "magenta_colors":
                colors = magenta_colors
            case "yellow_colors":
                colors = yellow_colors
            case "traffic_lights_colors":
                colors = traffic_lights_colors
            case "disco_colors":
                colors = disco_colors
            case _:
                colors = random.choice(all_colors)

        all_color_modes = (konfetti_colors, bw_colors, rgb_colors, pastel_colors, grayscale_colors, traffic_lights_colors, disco_colors)
        # arg to array/list: color_modes are arrays for more performace
        match args.color_mode:
            case "konfetti_colors":
                color_mode = konfetti_colors
            case "bw_colors":
                color_mode = bw_colors
            case "rgb_colors":
                color_mode = rgb_colors
            case "pastel_colors":
                color_mode = pastel_colors
            case "grayscale_colors":
                color_mode = grayscale_colors
            case "traffic_lights_colors":
                color_mode = traffic_lights_colors
            case "disco_colors":
                color_mode = disco_colors
            case _:
                color_mode = random.choice(all_color_modes)

        # Let it an abstract string value for more effect in the future
        all_strobo_modes = ("konfetti_colors", "bw_colors", "rgb_colors", "grayscale_colors", "solid_r", "solid_g", "solid_b", "solid_m", "solid_c", "solid_y", "solid_white",  "solid_black","traffic_lights_colors","disco_colors")

        state = {
            "color": (0, 0, 0),
            "delay": 0.1,
            "konfetti_freq":10.0,
            "flip":random.randint(0,1),
            "strobo_mode": args.strobo_mode or "bw_colors",
        }

        num_konfetti_previous=0

        # Starte Tasks
        tasks = [
            asyncio.create_task(strobo_updater(state)),
            asyncio.create_task(konfetti_updater(state)),
        ]

        bricks = []

        all_effects = ("konfetti", "lametta", "bricks") # "colorstrobo"
        args.effect = args.effect or random.choice(all_effects)

        current_band = ""
        band_prev = ""

        current_amp = ""
        amp_prev = ""

        current_phase = ""
        phase_prev = ""

        all_auto_modes = ("flower", "flower2", "dots", "bricks", "wall", "konfetti", "konfetti_wall", "triangle", "triangle_colorstrobe", "dope")
        args.auto_mode = args.auto_mode or "" # random.choice(all_auto_modes)

        def smoothed (dominant_freq=10.0, alpha=0.25):
            """Glättung"""
            if args.smoothed is False:
                return dominant_freq
            global num_konfetti_previous
            if dominant_freq <= 0:
                dominant_freq = 10.0
            smoothed = num_konfetti_previous * (1 - alpha) + dominant_freq * alpha
            num_konfetti_previous = smoothed
            return dominant_freq # smoothed

        def random_color():
            nonlocal colors
            #print ("\n", f"Eine zufällige Farbe aus RGB + Yellow, Magent, Cyan")
            choices = [a for a in (red_colors, green_colors, blue_colors, yellow_colors, cyan_colors, magenta_colors) if a != colors]
            colors = random.choice(choices)
            return colors

        def random_color_mode():
            nonlocal color_mode, colors
            choices = [a for a in all_color_modes if a != color_mode ]
            color_mode = random.choice(choices)
            colors = color_mode
            return colors

        CENTER = (WIDTH // 2, HEIGHT // 2)
        # -------- ANIMATION --------
        rotation = 0
        time = 0  # für Pulsieren
        
        # Klassifizierung
        skip_classyfying = False # this is the default

        if args.record is not None:
            # --- Video Setup ---
            writer = imageio.get_writer(args.record, fps=30)  # AVI-Datei, 30 FPS
        while running_event.is_set():
            hint = None
            #skip_classyfying = False # reset: this is the default
            current_band = classify_band(freq.value*args.scale)
            current_amp = classify_band2(amp.value*args.scale)
            if args.auto_mode == "":
                #TODO: reset (what the defaults?)
                all_color_modes = (konfetti_colors, bw_colors, rgb_colors, pastel_colors, grayscale_colors)
                all_effects = ("konfetti", "lametta", "bricks") # "colorstrobo"
            else:
                match args.auto_mode:
                    case "triangle":
                        hint = hint or "Triangle"
                        all_effects = ("triangle", "triangle_dummy")
                        color_mode = grayscale_colors
                        state["strobo_mode"] = "bw_colors"
                    case "triangle_konfetti_wall"|"triangle_colorstrobe":
                        """Dancehall/Disco approved"""
                        hint = hint or "Triangle Colorstrobe"
                        all_effects = ("triangle", "triangle_dummy")
                        color_mode = grayscale_colors
                        state["strobo_mode"] = "konfetti_colors"
                    case "come_in"|"triangle_come_in":
                        hint = hint or "Come In!"
                        all_effects = ("triangle", "triangle_dummy")
                        color_mode = pastel_colors
                        colors = grayscale_colors
                        state["strobo_mode"] = None
                        #skip_classyfying = True
                    case "bricks":
                        hint = hint or "Bricks aka. Wall"
                        all_effects = ("wall", "wall_dummy")
                        state["strobo_mode"] = "bw_colors"
                    case "wall":
                        hint = hint or "Wall"
                        all_effects = ("lametta", "bricks", "colorstrobo")
                        state["strobo_mode"] = "bw_colors"
                    case "dope":
                        """Rave approved"""
                        hint = hint or "Dope"
                        all_effects = ("lametta", "colorstrobo")
                        state["strobo_mode"] = "bw_colors"
                        colors = bw_colors
                        #skip_classyfying = True
                    case "konfetti":
                        hint = hint or "Konfetti"
                        all_effects = ("konfetti", "konfetti_dummy")
                        state["strobo_mode"] = "bw_colors"
                    case "flower":
                        hint = hint or "Flower"
                        all_effects = ("flower", "flower_dummy")
                        colors = konfetti_colors
                        state["strobo_mode"] = "solid_black"
                        color_mode = grayscale_colors
                        #skip_classyfying = False
                    case "flower2":
                        hint = hint or "Flower 2"
                        all_effects = ("flower2", "flower2_dummy")
                        colors = bw_colors
                        state["strobo_mode"] = "solid_black"
                        #skip_classyfying = True
                    case "flowermix":
                        hint = hint or "Flower Mix"
                        all_effects = ("flower", "flower2")
                        colors = bw_colors
                        state["strobo_mode"] = "solid_black"
                        #skip_classyfying = True
                    case "dots":
                        hint = hint or "Dots"
                        all_effects = ("dots", "dots_dummy")
                        colors = red_colors
                        state["strobo_mode"] = "solid_black"
                        #skip_classyfying = True
                if skip_classyfying:
                    pass
                else:
                    # Klassifizierung
                    if current_amp != amp_prev:
                        amp_prev = current_amp
                        match current_amp:
                            case "sub"|"bass"|"low-mid":
                                colors = rgb_colors
                            case "mid":
                                colors = konfetti_colors
                            case "high"|"high-mid":
                                colors = random_color()
                            case _:
                                pass
                    if current_band != band_prev:
                        band_prev = current_band
                        #TODO random effect?
                        #event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a})
                        #pygame.event.post(event)
                        match current_band:
                            case _:
                                pass

                # VERY IMPORTENT!
                event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
                pygame.event.post(event)
                                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Fenster schließen
                    running_event.clear()  # <- this stops the worker thread
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # ESC-Taste
                        running_event.clear()  # <- this stops the worker thread
                    if event.key == pygame.K_SPACE:
                        # tab often to switch
                        # DONT SET args.auto_mode="" HERE!
                        choices = [a for a in all_effects if a != args.effect]
                        args.effect = random.choice(choices) # "random"
                    if event.key == pygame.K_0:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "strobo" # "none"
                    if event.key == pygame.K_k:
                        skip_classyfying = not skip_classyfying
                    if event.key == pygame.K_1:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "konfetti"
                    if event.key == pygame.K_2:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "lametta"
                    if event.key == pygame.K_3:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "bricks" # "wall"
                    if event.key == pygame.K_4:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "colorstrobo"
                    if event.key == pygame.K_5:
                        args.auto_mode = ""
                        state["strobo_mode"] = None
                        args.effect = "triangle"
                    if event.key == pygame.K_6:
                        args.auto_mode = ""
                        args.effect = "flower"
                        state["strobo_mode"] = "grayscale_colors"
                        color_mode = konfetti_colors
                    if event.key == pygame.K_8:
                        # tab often to switch color mode
                        args.auto_mode = ""
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            color_mode = grayscale_colors #TODO: reset (whats the default, grayscale_colors?)
                        else:
                            choices = [a for a in all_color_modes if a != color_mode ]
                            color_mode = random.choice(choices)
                            print ("\n", f"Random color mode")
                    if event.key == pygame.K_9:
                        # tab often to switch strobe mode (the colors)
                        args.auto_mode = ""
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            state["strobo_mode"] = None
                        else:
                            choices = [a for a in all_strobo_modes if a != args.strobo_mode ]
                            args.strobo_mode = random.choice(choices)
                            state["strobo_mode"] = args.strobo_mode
                            print ("\n", f"Random strobe mode: {state["strobo_mode"].upper()}")
                    if event.key == pygame.K_t:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            args.no_subtext = not args.no_subtext
                        else:
                            args.no_text = not args.no_text
                            print ("\n", f"No text: {args.no_text}")
                    if event.key == pygame.K_a:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            args.auto_mode = ""
                        else:
                            choices = [a for a in all_auto_modes if a != args.auto_mode]
                            choice = random.choice(choices)
                            args.auto_mode = choice
                    if event.key == pygame.K_s:
                        args.smoothed = not args.smoothed
                        print ("\n", f"Smoothed: {args.smoothed}")
                    if event.key == pygame.K_PLUS:
                        args.scale += 10
                        print ("\n", f"Scale: {args.scale}")
                    if event.key == pygame.K_MINUS:
                        args.scale -= 10
                        print ("\n", f"Scale: {args.scale}")
                    if event.key == pygame.K_n:
                        args.scale = parser.get_default("scale")
                        print ("\n", f"Scale: {args.scale} (default)")
                    if event.key == pygame.K_i:
                        print ("\n", "ℹ️ Current settings (Info):")
                        print (f"➡️ Smoothed: {args.smoothed}")
                        print (f"➡️ Scale: {args.scale}")
                        if args.auto_mode:
                            print (f"🤖 Auto mode: {args.auto_mode.upper()}")
                        else:
                            print (f"🎨 Effect: {args.effect.upper()}")
                    if event.key == pygame.K_b:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Blue")
                            colors = blue_colors
                        else:
                            print ("\n", f"S/W")
                            colors = bw_colors
                    if event.key == pygame.K_y:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Yellow")
                            colors = yellow_colors
                        else:
                            pass
                    if event.key == pygame.K_m:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Magenta")
                            colors = magenta_colors
                        else:
                            pass
                    if event.key == pygame.K_f:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            colors = random_color()
                        else:
                            print ("\n", f"Farbmodus konfetti")
                            colors = konfetti_colors
                    if event.key == pygame.K_q:
                        print ("\n", f"Come In!")
                        args.auto_mode = "come_in"
                    if event.key == pygame.K_r:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Red")
                            colors = red_colors
                        else:
                            colors = rgb_colors
                    if event.key == pygame.K_g:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Green")
                            colors = green_colors
                        else:
                            colors = grayscale_colors
                    if event.key == pygame.K_c:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            print ("\n", f"Cyan")
                            colors = cyan_colors
                        else:
                            colors = random_color_mode()
                    if event.key == pygame.K_x:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            color_mode = random.choice(all_color_modes)
                            print ("\n", f"🎨 Eine zufälliger Farbmodus")
                        else:
                            color = (
                                random.randint(0, 255), # red
                                random.randint(0, 255), # green
                                random.randint(0, 255)) # blue
                            r, g, b = color
                            print ("\n", f"🎨 Eine zufällige Farbe: R={r} G={g} B={b}")
                            colors = [(color)]

            # --- Zeichnen
            strobo_color=None
            # Let state["strobo_mode"] an abstract string value for more effect in the future
            match state["strobo_mode"]: # same values as color_mode
                case "konfetti_colors":
                    strobo_color=random.choice(konfetti_colors)
                case "bw_colors":
                    strobo_color=random.choice(bw_colors)
                case "rgb_colors":
                    strobo_color=random.choice(rgb_colors)
                case "pastel_colors":
                    strobo_color=random.choice(pastel_colors)
                case "grayscale_colors":
                    strobo_color=random.choice(grayscale_colors)
                case "traffic_lights_colors":
                    strobo_color=random.choice(traffic_lights_colors)
                case "disco_colors":
                    strobo_color=random.choice(disco_colors)
                case "r": # "red"
                    strobo_color=random.choice(red_colors)
                case "g": # "green"
                    strobo_color=random.choice(green_colors)
                case "b": # "blue"
                    strobo_color=random.choice(blue_colors)
                case "y": # "yellow"
                    strobo_color=random.choice(red_colors)
                case "c": # "cyan"
                    strobo_color=random.choice(cyan_colors)
                case "m": # "magenta"
                    strobo_color=random.choice(magenta_colors)
                case "solid_r":
                    strobo_color=(255,0,0)
                case "solid_g":
                    strobo_color=(0,255,0)
                case "solid_b":
                    strobo_color=(0,0,255)
                case "solid_y":
                    strobo_color=(255,255,0)
                case "solid_c":
                    strobo_color=(0,255,255)
                case "solid_m":
                    strobo_color=(255,0,255)
                case "solid_black":
                    strobo_color=(0,0,0)
                case "solid_white":
                    strobo_color=(255,255,255)
                case _:
                    strobo_color=state["color"]
            screen.fill(strobo_color)

            match args.effect:
                case "konfetti"|"konfetti_dummy":
                    hint= hint or f"Konfetti"
                    # Glättung 
                    num_konfetti = state["konfetti_freq"] / 5
                    num_konfetti = int(limit(num_konfetti,smoothed(num_konfetti * args.scale),num_konfetti))
                    for _ in range( num_konfetti):
                        x = random.randint(0, WIDTH)
                        y = random.randint(0, HEIGHT)
                        r = random.randint(1, 9)
                        pygame.draw.circle(screen, random.choice(colors), (x, y), r)
                case "lametta":
                    hint= hint or f"Lametta"
                    # Glättung
                    num_konfetti = state["konfetti_freq"] / 3
                    num_konfetti = int(limit(smoothed(num_konfetti),num_konfetti/args.scale,num_konfetti*args.scale)) or 1
                    if state["flip"]:
                        x=0; y=0; w=int(WIDTH/num_konfetti)+1; randcolor=1
                        for _ in range( num_konfetti):
                            rect = pygame.Rect(x, y, w, HEIGHT)
                            if randcolor == 1:
                                pygame.draw.rect(screen, random.choice(colors), rect)
                                randcolor = 0
                            else:
                                randcolor = 1
                            x+=w
                    else:
                        x=0; y=0; h=int(HEIGHT/num_konfetti)+1; randcolor=1
                        for _ in range( num_konfetti):
                            rect = pygame.Rect(x, y, WIDTH, h)
                            if randcolor == 1:
                                pygame.draw.rect(screen, random.choice(colors), rect)
                                randcolor = 0
                            else:
                                randcolor = 1
                            y+=h
                case "bricks"|"wall"|"wall_dummy":
                    hint= hint or f"Bricks aka. Wall"
                    # Glättung
                    num_konfetti = state["konfetti_freq"] / 3
                    num_konfetti = int(limit(smoothed(num_konfetti),num_konfetti/args.scale,num_konfetti*args.scale)) or 1
                    y=0
                    w=int(WIDTH/num_konfetti)+1
                    h=int(HEIGHT/num_konfetti)+1
                    if state["flip"]:
                        bricks = []
                        for col in range(num_konfetti):
                            x=0
                            bricks.append([])
                            for row in range( num_konfetti):
                                if random.randint(0,1):
                                    bricks[col].append((random.choice(colors), pygame.Rect(x, y, w, h)))
                                x+=w
                            y+=h
                    for col in bricks:
                        for row in col:
                            color, rect = row
                            pygame.draw.rect(screen, color, rect)
                case "none"|"strobe":
                    hint= hint or f"Pure Strobe"
                    pass
                case "colorstrobo":
                    hint= hint or f"Colorstrobe"
                    screen.fill(random.choice(colors))
                case "triangle"|"triangle_dummy"|"polygon":
                    hint= hint or f"Triangle"
                    # Mittelpunkt und Größe
                    minimum=int(HEIGHT/10)
                    stop=int(limit(HEIGHT/.1*state["delay"],0,HEIGHT/5)) # s
                    start=stop+int(limit(HEIGHT/100*state["konfetti_freq"],0,HEIGHT+HEIGHT/3)) # Hz
                    #smoothed(start)
                    for i in range(start,stop,-10):
                        size = i  # Höhe des Dreiecks
                        cx, cy = CENTER # Triangle points (x, y)
                        # Eckpunkte berechnen
                        triangle_points = [
                            (cx, cy - size),            # oben
                            (cx - size, cy + size),     # links unten
                            (cx + size, cy + size)      # rechts unten
                        ]
                        # Draw filled triangle
                        pygame.draw.polygon(screen, random.choice(colors), triangle_points)
                    size = stop  # Höhe des Dreiecks
                    cx, cy = CENTER # Triangle points (x, y)
                    # Eckpunkte berechne
                    triangle_points = [ 
                        (cx, cy - size),            # oben
                        (cx - size, cy + size),     # links unten
                        (cx + size, cy + size)      # rechts unten
                    ]
                    # Draw filled triangle
                    pygame.draw.polygon(screen, random.choice(color_mode), triangle_points)
                case "flower"|"flower_dummy":
                    hint= hint or f"Flower"
                    PETAL_RADIUS = int(HEIGHT/2)
                    flower_size=HEIGHT
                    x = -1 + amp.value % 5
                    for i in range(int(x)):
                        PETALS = 31
                        PETAL_SIZE = 15
                        PETAL_RADIUS += PETAL_SIZE * 7
                        flower_size += PETAL_SIZE * 25
                        flower = pygame.Surface((flower_size, flower_size), pygame.SRCALPHA)
                        fc = flower_size // 2
                        # Blume zeichnen
                        for i in range(PETALS):
                             angle = 2 * math.pi / PETALS * i
                             x = fc + math.cos(angle) * PETAL_RADIUS
                             y = fc + math.sin(angle) * PETAL_RADIUS
                             pygame.draw.circle(flower, random.choice(colors), (int(x), int(y)), PETAL_SIZE)
                        #pygame.draw.circle(flower, random.choice(color_mode), (fc, fc), 123)
                        # Größe im Wechsel (Sinus)
                        scale = 1.0 + 0.2 * math.sin(time)
                        # Skalieren
                        new_size = PETAL_RADIUS # int(PETAL_RADIUS * scale)
                        scaled = pygame.transform.smoothscale(flower, (new_size, new_size))
                        # Rotieren
                        rotated = pygame.transform.rotate(scaled, rotation)
                        rect = rotated.get_rect(center=CENTER)
                        screen.blit(rotated, rect)
                        # Animation updaten
                        rotation += smoothed(freq.value) # 1.5
                        rotation %= 360
                        time += smoothed(amp.value) # 0.05
                        if state["flip"]:
                            #time *= -1
                            rotation *= -1
                    # Blume
                    PETALS = 15
                    PETAL_RADIUS = 110
                    PETAL_SIZE = 18
                    flower_size = 350
                    flower = pygame.Surface((flower_size, flower_size), pygame.SRCALPHA)
                    fc = flower_size // 2
                    # Blume einmal zeichnen
                    for i in range(PETALS):
                        angle = 2 * math.pi / PETALS * i
                        x = fc + math.cos(angle) * PETAL_RADIUS
                        y = fc + math.sin(angle) * PETAL_RADIUS
                        pygame.draw.circle(flower, complement_color_rgb(strobo_color), (int(x), int(y)), PETAL_SIZE)
                    pygame.draw.circle(flower, random.choice(color_mode), (fc, fc), 28)
                    # Größe im Wechsel (Sinus)
                    scale = 1.0 + 0.2 * math.sin(time)
                    # Skalieren
                    new_size = int(flower_size * scale)
                    scaled = pygame.transform.smoothscale(flower, (new_size, new_size))
                    # Rotieren
                    rotated = pygame.transform.rotate(scaled, rotation)
                    rect = rotated.get_rect(center=CENTER)
                    screen.blit(rotated, rect)
                    # Animation updaten
                    rotation += smoothed(amp.value) # 1.5
                    rotation %= 360
                    time += smoothed(freq.value) # 0.05
                    if state["flip"]:
                        time *= -1
                        rotation *= -1
                case "flower2"|"flower2_dummy":
                    hint= hint or f"Flower 2"

                    PETAL_RADIUS = int(HEIGHT/2)
                    flower_size=HEIGHT
                    a=int(freq.value)
                    b=int(amp.value)
                    if a>b:
                        t=b
                        b=a
                        a=t
                    x = limit(random.randint(a,b)%8,3,5)
                    for i in range(int(x)):
                        PETALS = random.randint(a,b)
                        PETAL_SIZE = 15
                        PETAL_RADIUS += PETAL_SIZE * 7
                        flower_size += PETAL_SIZE * 25
                        flower = pygame.Surface((flower_size, flower_size), pygame.SRCALPHA)
                        fc = flower_size // 2
                        # Blume zeichnen
                        maximal = int((flower_size*3.14159)/((PETAL_SIZE*2)+13))
                        minimum = int(((amp.value + freq.value) % 1 ) * 50)
                        PETALS = limit(random.randint(a,b),minimum,maximal)
                        for i in range(PETALS):
                            angle = 2 * math.pi / PETALS * i
                            x = fc + math.cos(angle) * PETAL_RADIUS
                            y = fc + math.sin(angle) * PETAL_RADIUS
                            if random.randint(0,1):
                                pygame.draw.circle(flower, random.choice(colors), (int(x), int(y)), PETAL_SIZE)
                        #pygame.draw.circle(flower, random.choice(color_mode), (fc, fc), 123)
                        # Größe im Wechsel (Sinus)
                        scale = 1.0 + 0.2 * math.sin(time)
                        # Skalieren
                        new_size = PETAL_RADIUS # int(PETAL_RADIUS * scale)
                        scaled = pygame.transform.smoothscale(flower, (new_size, new_size))
                        # Rotieren
                        if random.randint(0,1):
                            rotated = pygame.transform.rotate(scaled, rotation)
                            rect = rotated.get_rect(center=CENTER)
                            screen.blit(rotated, rect)
                        else:
                            rect = scaled.get_rect(center=CENTER)
                            screen.blit(scaled, rect)
                        # Animation updaten
                        rotation += smoothed(freq.value) # 1.5
                        rotation %= 360
                        time += smoothed(amp.value) # 0.05
                        if state["flip"]:
                            time *= -1
                            rotation *= -1
                    # Blume
                    PETALS = 15
                    PETAL_RADIUS = 110
                    PETAL_SIZE = 18
                    flower_size = 350
                    flower = pygame.Surface((flower_size, flower_size), pygame.SRCALPHA)
                    fc = flower_size // 2
                    # Blume einmal zeichnen
                    for i in range(PETALS):
                        angle = 2 * math.pi / PETALS * i
                        x = fc + math.cos(angle) * PETAL_RADIUS
                        y = fc + math.sin(angle) * PETAL_RADIUS
                        pygame.draw.circle(flower, complement_color_rgb(strobo_color), (int(x), int(y)), PETAL_SIZE)
                    pygame.draw.circle(flower, random.choice(color_mode), (fc, fc), 28)
                    # Größe im Wechsel (Sinus)
                    scale = 1.0 + 0.2 * math.sin(time)
                    # Skalieren
                    new_size = int(flower_size * scale)
                    scaled = pygame.transform.smoothscale(flower, (new_size, new_size))
                    # Rotieren
                    rotated = pygame.transform.rotate(scaled, rotation)
                    rect = rotated.get_rect(center=CENTER)
                    screen.blit(rotated, rect)
                    # Animation updaten
                    rotation += smoothed(amp.value) # 1.5
                    rotation %= 360
                    time += smoothed(freq.value) # 0.05
                    if state["flip"]:
                        time *= -1
                        rotation *= -1
                case "dots"|"dots_dummy":
                    hint= hint or f"Dots"
                    a=int(freq.value)
                    b=int(amp.value)
                    if a>b:
                        t=b
                        b=a
                        a=t
                    PETAL_RADIUS = int(HEIGHT/2)
                    flower_size=HEIGHT
                    x = limit(random.randint(a,b)%8,1,5)
                    for i in range(int(x)):
                        PETAL_SIZE = 15
                        maximal = int((flower_size*3.14159)/((PETAL_SIZE*2)+13))
                        minimum = int(((amp.value + freq.value) % 1 ) * 50)
                        PETALS = limit(random.randint(a,b),minimum,maximal)
                        PETAL_RADIUS += PETAL_SIZE * 7
                        flower_size += PETAL_SIZE * 25
                        flower = pygame.Surface((flower_size, flower_size), pygame.SRCALPHA)
                        fc = flower_size // 2
                        # Blume zeichnen
                        for i in range(PETALS):
                            angle = 2 * math.pi / PETALS * i
                            x = fc + math.cos(angle) * PETAL_RADIUS
                            y = fc + math.sin(angle) * PETAL_RADIUS
                            if random.randint(0,1):
                                pygame.draw.circle(flower, random.choice(colors), (int(x), int(y)), PETAL_SIZE)
                        #pygame.draw.circle(flower, random.choice(color_mode), (fc, fc), 123)
                        # Größe im Wechsel (Sinus)
                        scale = (1.0 + 0.2 * math.sin(time))
                        # Skalieren
                        new_size = int(random.randint(int(PETAL_RADIUS-freq.value),PETAL_RADIUS) * scale)
                        new_size = limit(new_size,0,HEIGHT)
                        scaled = pygame.transform.smoothscale(flower, (new_size, new_size))
                        # Rotieren
                        if random.randint(0,1):
                            rotated = pygame.transform.rotate(scaled, rotation)
                            rect = rotated.get_rect(center=CENTER)
                            screen.blit(rotated, rect)
                        else:
                            rect = scaled.get_rect(center=CENTER)
                            screen.blit(scaled, rect)
                        # Animation updaten
                        rotation += smoothed(freq.value) # 1.5
                        rotation %= 360
                        time += smoothed(amp.value) # 0.05
                        if state["flip"]:
                            #time *= -1
                            rotation *= -1
                            pass
                case _:
                    pass

            # Text (Frequenz)
            if args.no_text is False:
                text_color = complement_color_rgb(strobo_color)
                text = font.render(f"{freq.value:6.2f} Hz ({state['delay']:.3f} s)", True, text_color)
                rect = text.get_rect(center=CENTER)
                screen.blit(text, rect)
                if args.no_subtext:
                    pass
                else:
                    #text_sub = font_sub.render(f"Band: {current_band} Amp: {current_amp}", True, text_color)
                    text_sub = font_sub.render(current_amp or current_band , True, text_color)
                    rect = text_sub.get_rect(center=(WIDTH / 2, HEIGHT / 2 + text.get_height()))
                    screen.blit(text_sub, rect)
                if args.no_subtext:
                    hint = ""
                if args.hint:
                    hint = args.hint
                if hint:
                    text_hint = font_sub.render(hint, True, text_color)
                    rect = text_hint.get_rect(center=(WIDTH / 2, HEIGHT / 2 - text.get_height()))
                    screen.blit(text_hint, rect)
            pygame.display.flip()
            if args.record is not None:
                # --- Video Setup ---
                # --- Frame aufnehmen ---
                frame = pygame.surfarray.array3d(screen)  # (width, height, 3)
                frame = np.transpose(frame, (1, 0, 2))   # für imageio muss die Achse getauscht werden
                writer.append_data(frame)

            # 10 Sekunden bei 30 FPS
            clock.tick(30)
            await asyncio.sleep(0.01) # 100

        pygame.quit()
        if args.record is not None:
            # --- Video Setup ---
            writer.close()
            print(f"✅ Video gespeichert als {args.record}")

        for t in tasks:
            t.cancel()

    asyncio.run(main())

# ============================================
# Hauptprogramm
# ============================================

if __name__ == "__main__":

    freq = Value(ctypes.c_double, args.scale)  # globale Variable
    amp = Value(ctypes.c_double, args.scale)   # Nur die Amplitude
    phase = Value(ctypes.c_double, args.scale) # Nur die Phase
    running_event = Event()
    running_event.set()

    p_audio = Process(target=worker_audio, args=(freq, amp, phase, running_event, args.device or default_input))
    p_video = Process(target=worker_video, args=(freq, amp, phase, running_event))

    try:
        p_audio.start()
        p_video.start() 
        while running_event.is_set():
            time.sleep(1)
            pass # time.sleep(0)
        running_event.clear()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n", "👏 Benutzer!")
        running_event.clear()
        sys.exit(1)
    finally:
        print("\n", "🛑 Beende Prozesse…")
        p_audio.join()
        p_video.join()
        print("✅ Fertig!")

