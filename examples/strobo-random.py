#!/usr/bin/env python3

import pygame
import time
import random

# Initialisierung
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Strobo-Effekt Random Colors")

# Display safety warning
print("⚠️ WARNING: This script simulates a strobe effect.")
print("Do not run if you are sensitive to flashing lights.")


# Strobo-Parameter
strobo_speed = 0.05  # Sekunden zwischen Farbwechseln

running = True

# Generate a random RGB color
def get_random_color():
    return (
        random.randint(0, 255),  # Red
        random.randint(0, 255),  # Green
        random.randint(0, 255)   # Blue
    )

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Farbe wechseln
    screen.fill(get_random_color())
    pygame.display.flip()

    time.sleep(strobo_speed)

pygame.quit()
