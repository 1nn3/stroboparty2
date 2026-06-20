#!/usr/bin/env python3

import pygame
import time

# Initialisierung
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Strobo-Effekt")

# Display safety warning
print("⚠️ WARNING: This script simulates a strobe effect.")
print("Do not run if you are sensitive to flashing lights.")

# Farbenliste
colors = [
    (0, 0, 0),
    (255, 255, 255)
]

# Strobo-Parameter
strobo_speed = 0.01  # Sekunden zwischen Farbwechseln

running = True
toggle = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Farbe wechseln
    screen.fill(colors[toggle])
    pygame.display.flip()
    toggle = not toggle

    time.sleep(strobo_speed)

pygame.quit()
