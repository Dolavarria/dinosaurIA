"""Configuración global del juego Chrome Dinosaur.

Centraliza todas las constantes de pantalla, fuentes y carga de assets
(imágenes de sprites) utilizados por los demás módulos del paquete ``game``.

Este módulo debe importarse antes de usar cualquier otro módulo del paquete,
ya que inicializa Pygame y carga los recursos gráficos en memoria.
"""

import os

import pygame

# ---------------------------------------------------------------------------
# Inicialización de Pygame
# ---------------------------------------------------------------------------
pygame.init()

# ---------------------------------------------------------------------------
# Constantes de Pantalla
# ---------------------------------------------------------------------------
SCREEN_HEIGHT: int = 600
SCREEN_WIDTH: int = 1100
SCREEN: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
FONT: pygame.font.Font = pygame.font.Font("freesansbold.ttf", 20)

# ---------------------------------------------------------------------------
# Assets del Dinosaurio
# ---------------------------------------------------------------------------
RUNNING_IMG: list[pygame.Surface] = [
    pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png")),
]

JUMPING_IMG: pygame.Surface = pygame.image.load(
    os.path.join("Assets/Dino", "DinoJump.png")
)

DUCKING_IMG: list[pygame.Surface] = [
    pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png")),
]

# ---------------------------------------------------------------------------
# Assets de Obstáculos
# ---------------------------------------------------------------------------
SMALL_CACTUS_IMG: list[pygame.Surface] = [
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png")),
]

LARGE_CACTUS_IMG: list[pygame.Surface] = [
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png")),
]

BIRD_IMG: list[pygame.Surface] = [
    pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
    pygame.image.load(os.path.join("Assets/Bird", "Bird2.png")),
]

# ---------------------------------------------------------------------------
# Assets del Entorno
# ---------------------------------------------------------------------------
CLOUD_IMG: pygame.Surface = pygame.image.load(
    os.path.join("Assets/Other", "Cloud.png")
)

BG_IMG: pygame.Surface = pygame.image.load(
    os.path.join("Assets/Other", "Track.png")
)
