import sounddevice as sd
import numpy as np
import pygame
import asyncio
import random
import argparse

parser = argparse.ArgumentParser()
args = parser.parse_args()

# ============================================
# ⚠️ Sicherheitshinweis
# ============================================
print("⚠️ WARNING: This script simulates a strobe effect.")
print("Do not run if you are sensitive to flashing lights.")

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Audio-Reaktives Strobo")
clock = pygame.time.Clock()
running = True
freq = 10.0  # globale Variable

# ---------------------------
# Audio Setup
# ---------------------------
devices = sd.query_devices()
print("Alle verfügbaren Audio-Geräte:")
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']}, Eingänge: {dev['max_input_channels']}, Ausgänge: {dev['max_output_channels']}")

default_input = sd.default.device[0]
device = default_input
samplerate = int(sd.query_devices(device)['default_samplerate'])
blocksize = 2048

# ============================================
# Hilfsfunktion
# ============================================
def strobo_delay_from_freq(freq, min_delay=0.02, max_delay=0.5):
    """Berechnet Delay (Sekunden) basierend auf Frequenz."""
    if freq <= 0:
        freq = 1
    delay = 1.0 / freq
    delay = max(min_delay, min(delay, max_delay))
    print(f"Dominante Frequenz: {freq:8.2f} Hz Delay: {delay:1.5f} s", end="\r")
    return delay

# ============================================
# Async Tasks
# ============================================
async def strobo_state_updater(state):
    """Wechselt Strobo-Farbe abhängig von Audio-Frequenz."""
    global freq
    while running:
        delay = strobo_delay_from_freq(freq)
        # dynamische Farbe (nicht nur schwarz/weiß)
        brightness = int(min(255, max(0, freq * 20)))
        color = (brightness, brightness, brightness)
        text_color = (255 - brightness, 255 - brightness, 255 - brightness)
        state["color"] = color
        state["text_color"] = text_color
        state["delay"] = delay
        await asyncio.sleep(delay)

async def konfetti_updater(state):
    """Erzeugt & aktualisiert Konfetti-Partikel."""
    global freq
    konfetti = []

    while running:
        # Anzahl Partikel skaliert mit Frequenz
        target_count = int(min(500, freq * 80))

        # neue Partikel hinzufügen
        for _ in range(target_count // 10):
            konfetti.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(0.5, 2),
                "color": random.choice([
                    (255, 50, 50), (50, 255, 50), (50, 50, 255),
                    (255, 255, 50), (255, 50, 255), (50, 255, 255)
                ]),
                "radius": random.randint(1, 3),
                "life": random.uniform(1.0, 3.0)
            })

        # alte Partikel updaten & löschen
        new_konfetti = []
        for k in konfetti:
            k["x"] += k["vx"]
            k["y"] += k["vy"]
            k["life"] -= 0.05
            if 0 <= k["x"] <= WIDTH and 0 <= k["y"] <= HEIGHT and k["life"] > 0:
                new_konfetti.append(k)
        konfetti = new_konfetti

        state["konfetti"] = konfetti
        await asyncio.sleep(0.03)

async def audio_analyzer(samplerate, blocksize, device):
    """Analysiert Audio-Eingang und aktualisiert globale freq."""
    global freq
    previous_freq = 10.0
    alpha = 0.25

    def audio_callback(indata, frames, time_info, status):
        nonlocal previous_freq
        global freq
        if status:
            print(status)
        chunk = indata[:, 0]
        yf = np.abs(np.fft.rfft(chunk))
        xf = np.fft.rfftfreq(len(chunk), 1 / samplerate)
        dominant_freq = xf[np.argmax(yf)]
        smoothed = previous_freq * (1 - alpha) + dominant_freq * alpha
        previous_freq = smoothed
        freq = smoothed / 123.0  # Skalierung

    with sd.InputStream(
        channels=1,
        callback=audio_callback,
        blocksize=blocksize,
        samplerate=samplerate,
        device=device
    ):
        print("🎧 Systemsound wird analysiert ... (Strg+C zum Beenden)")
        while running:
            await asyncio.sleep(0.1)

# ============================================
# Hauptloop (einziger Zeichenort!)
# ============================================
async def main():
    global running
    state = {
        "color": (0, 0, 0),
        "text_color": (255, 255, 255),
        "delay": 0.1,
        "konfetti": []
    }

    font = pygame.font.SysFont("Arial", 60, bold=True)

    # Starte Tasks
    tasks = [
        asyncio.create_task(strobo_state_updater(state)),
        asyncio.create_task(konfetti_updater(state)),
        asyncio.create_task(audio_analyzer(samplerate, blocksize, device))
    ]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Zeichnen ---
        screen.fill(state["color"])

        # Konfetti
        for k in state["konfetti"]:
            pygame.draw.circle(screen, k["color"], (int(k["x"]), int(k["y"])), k["radius"])

        # Text (Frequenz)
        text = font.render(f"{freq:6.2f} Hz", True, state["text_color"])
        rect = text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        screen.blit(text, rect)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    for t in tasks:
        t.cancel()

# ============================================
# Start
# ============================================
try:
    asyncio.run(main())
except KeyboardInterrupt:
    running = False
    print("\n👋 Beendet durch Benutzer")
