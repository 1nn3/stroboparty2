#!/usr/bin/env python3

import pygame
import math

# -------- INIT --------
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rotierende, pulsierende Blume")
clock = pygame.time.Clock()

CENTER = (WIDTH // 2, HEIGHT // 2)

# -------- BLUME --------
PETALS = 16
PETAL_RADIUS = 110
PETAL_SIZE = 18

FLOWER_SIZE = 350
flower = pygame.Surface((FLOWER_SIZE, FLOWER_SIZE), pygame.SRCALPHA)
fc = FLOWER_SIZE // 2

# Blume einmal zeichnen
for i in range(PETALS):
    angle = 2 * math.pi / PETALS * i
    x = fc + math.cos(angle) * PETAL_RADIUS
    y = fc + math.sin(angle) * PETAL_RADIUS
    pygame.draw.circle(flower, (255, 120, 160), (int(x), int(y)), PETAL_SIZE)

pygame.draw.circle(flower, (255, 210, 90), (fc, fc), 28)

# -------- ANIMATION --------
rotation = 0
time = 0  # für Pulsieren

running = True
while running:
    clock.tick(60)
    screen.fill((20, 20, 25))

    # Größe im Wechsel (Sinus)
    scale = 1.0 + 0.2 * math.sin(time)

    # Skalieren
    new_size = int(FLOWER_SIZE * scale)
    scaled = pygame.transform.smoothscale(flower, (new_size, new_size))

    # Rotieren
    rotated = pygame.transform.rotate(scaled, rotation)

    rect = rotated.get_rect(center=CENTER)
    screen.blit(rotated, rect)

    # Animation updaten
    rotation += 1.5
    rotation %= 360
    time += 0.05

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()

