#!/usr/bin/env python3

import pygame
import time
import random

# Initialisierung
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Strobo-Effekt Rainbow")

# Display safety warning
print("⚠️ WARNING: This script simulates a strobe effect.")
print("Do not run if you are sensitive to flashing lights.")

# Strobo-Parameter
strobo_speed = 0.025  # Sekunden zwischen Farbwechseln

# Regenbogenfarben
colors = [
    (255, 0, 0),     # Rot
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Gelb
    (0, 255, 0),     # Grün
    (0, 0, 255),     # Blau
    (75, 0, 130),    # Indigo
    (148, 0, 211)    # Violett
]

running = True
color_index = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Farbe wechseln
    screen.fill(colors[color_index])
    pygame.display.flip()
    color_index = (color_index + 1) % len(colors)

    time.sleep(strobo_speed)

pygame.quit()
