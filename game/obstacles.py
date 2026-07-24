"""Módulo de obstáculos del juego.

Define la jerarquía de obstáculos: una clase base ``Obstacle`` y tres
subclases concretas (``SmallCactus``, ``LargeCactus``, ``Bird``) que el
dinosaurio debe esquivar durante la partida.
"""

import random

import pygame

from game.config import SCREEN_WIDTH


class Obstacle:
    """Clase base para todos los obstáculos del juego.

    Cada obstáculo tiene una imagen (sprite sheet), un índice de tipo
    que selecciona qué variante visual usar, y un rectángulo de colisión.

    Args:
        image: Lista de superficies con las variantes del obstáculo.
        obstacle_type: Índice que indica qué variante visual usar.
    """

    def __init__(
        self, image: list[pygame.Surface], obstacle_type: int
    ) -> None:
        self.image = image
        self.type = obstacle_type
        self.rect: pygame.Rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self, game_speed: int) -> None:
        """Mueve el obstáculo hacia la izquierda según la velocidad del juego.

        Args:
            game_speed: Velocidad actual del juego (píxeles por frame).
        """
        self.rect.x -= game_speed

    def is_off_screen(self) -> bool:
        """Comprueba si el obstáculo salió completamente de la pantalla.

        Returns:
            ``True`` si el obstáculo ya no es visible.
        """
        return self.rect.x < -self.rect.width

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el obstáculo en la pantalla.

        Args:
            screen: Superficie de Pygame donde se dibuja el sprite.
        """
        screen.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    """Cactus pequeño que aparece a nivel del suelo.

    Selecciona aleatoriamente una de las 3 variantes visuales disponibles.
    """

    def __init__(self, image: list[pygame.Surface]) -> None:
        self.type: int = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 325


class LargeCactus(Obstacle):
    """Cactus grande que aparece a nivel del suelo.

    Selecciona aleatoriamente una de las 3 variantes visuales disponibles.
    """

    def __init__(self, image: list[pygame.Surface]) -> None:
        self.type: int = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300


class Bird(Obstacle):
    """Pájaro que vuela a diferentes alturas.

    Las alturas posibles determinan qué acción debe tomar el dinosaurio:
    - **270 (bajo)**: el dino DEBE agacharse.
    - **320 (suelo)**: el dino DEBE saltar.
    - **200 (alto)**: decorativo, no colisiona con el dino.

    Attributes:
        BIRD_HEIGHTS: Lista de alturas posibles para el pájaro.
    """

    BIRD_HEIGHTS: list[int] = [270, 320, 200]

    def __init__(self, image: list[pygame.Surface]) -> None:
        self.type: int = 0
        super().__init__(image, self.type)
        self.rect.y = random.choice(self.BIRD_HEIGHTS)
        self.index: int = 0

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el pájaro con animación de aleteo.

        Args:
            screen: Superficie de Pygame donde se dibuja el sprite.
        """
        if self.index >= 9:
            self.index = 0
        screen.blit(self.image[self.index // 5], self.rect)
        self.index += 1
