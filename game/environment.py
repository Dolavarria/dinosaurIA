"""Módulo del entorno visual del juego.

Contiene las clases ``Cloud`` (nubes decorativas) y ``Game`` (estado global
del juego: velocidad, puntuación, fondo scrollable y lista de obstáculos).
"""

import random

import pygame

from game.config import BG_IMG, CLOUD_IMG, FONT, SCREEN, SCREEN_WIDTH


class Cloud:
    """Nube decorativa que se mueve de derecha a izquierda.

    Las nubes no afectan al gameplay; son puramente visuales para darle
    profundidad al escenario.
    """

    def __init__(self) -> None:
        self.x: int = SCREEN_WIDTH + random.randint(800, 1000)
        self.y: int = random.randint(50, 100)
        self.image: pygame.Surface = CLOUD_IMG
        self.width: int = self.image.get_width()

    def update(self, game_speed: int) -> None:
        """Mueve la nube y la reposiciona cuando sale de pantalla.

        Args:
            game_speed: Velocidad actual del juego (píxeles por frame).
        """
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja la nube en la pantalla.

        Args:
            screen: Superficie de Pygame donde se dibuja la nube.
        """
        screen.blit(self.image, (self.x, self.y))


class Game:
    """Estado global de una partida del juego Chrome Dinosaur.

    Gestiona la velocidad del juego, la puntuación, el fondo scrollable
    y la lista de obstáculos activos en pantalla.

    Attributes:
        MAX_SPEED: Velocidad máxima que puede alcanzar el juego.
        SPEED_INCREMENT_INTERVAL: Cada cuántos puntos se incrementa la velocidad.
    """

    MAX_SPEED: int = 40
    SPEED_INCREMENT_INTERVAL: int = 100

    def __init__(self) -> None:
        self.speed: int = 20
        self.x_pos_bg: int = 0
        self.y_pos_bg: int = 380
        self.points: int = 0
        self.obstacles: list = []
        self.cloud: Cloud = Cloud()

    def score(self) -> None:
        """Incrementa la puntuación y aumenta la velocidad periódicamente.

        Cada ``SPEED_INCREMENT_INTERVAL`` puntos, la velocidad sube en 1
        hasta alcanzar ``MAX_SPEED``.
        """
        self.points += 1
        if self.points % self.SPEED_INCREMENT_INTERVAL == 0:
            self.speed = min(self.speed + 1, self.MAX_SPEED)
        text = FONT.render("Points: " + str(self.points), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (1000, 40)
        SCREEN.blit(text, text_rect)

    def background(self) -> None:
        """Dibuja el fondo con efecto de scroll infinito (parallax)."""
        image_width = BG_IMG.get_width()
        SCREEN.blit(BG_IMG, (self.x_pos_bg, self.y_pos_bg))
        SCREEN.blit(BG_IMG, (image_width + self.x_pos_bg, self.y_pos_bg))
        if self.x_pos_bg <= -image_width:
            SCREEN.blit(BG_IMG, (image_width + self.x_pos_bg, self.y_pos_bg))
            self.x_pos_bg = 0
        self.x_pos_bg -= self.speed
