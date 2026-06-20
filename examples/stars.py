import pygame
import random

# Pygame initialisieren
pygame.init()

# Fenstergröße
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sternenhimmel")

def stars(pygame):
    # Farben
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    # Hintergrund schwarz füllen
    screen.fill(BLACK)
    # Liste mit Sternpositionen
    stars = []
    for _ in range(200):  # 200 Sterne
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        radius = random.randint(1, 3)
        stars.append((x, y, radius))
    # Sterne zeichnen
    for (x, y, r) in stars:
        pygame.draw.circle(screen, WHITE, (x, y), r)

# Hauptschleife
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    stars(pygame)

    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

