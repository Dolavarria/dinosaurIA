"""Módulo del entorno visual del juego.

Contiene las clases ``Cloud`` (nubes decorativas) y ``Game`` (estado global
del juego: velocidad, puntuación, fondo scrollable y lista de obstáculos).

La clase ``Game`` expone métodos reutilizables por cualquier algoritmo de IA:
- ``reset()``: Reinicia el juego para un nuevo episodio.
- ``spawn_obstacles()``: Genera obstáculos cuando es necesario.
- ``update_obstacles()``: Mueve obstáculos y limpia los que salen de pantalla.
- ``get_observation(dino)``: Retorna la observación normalizada para el agente.
- ``update_score()`` / ``draw_score(screen)``: Lógica y visual separadas.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from game.config import (
    BG_IMG,
    BIRD_IMG,
    CLOUD_IMG,
    FONT,
    LARGE_CACTUS_IMG,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SMALL_CACTUS_IMG,
)
from game.obstacles import Bird, LargeCactus, SmallCactus

if TYPE_CHECKING:
    from game.dinosaur import Dinosaur


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

    Esta clase está diseñada para ser **algoritmo-agnóstica**: expone métodos
    reutilizables tanto por NEAT como por DQN u otros algoritmos de IA.

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

    # ------------------------------------------------------------------
    # Métodos de lógica (sin renderizado — usables en entrenamiento rápido)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reinicia el juego a su estado inicial para un nuevo episodio.

        Útil en Aprendizaje por Refuerzo (RL) donde cada episodio
        requiere un entorno limpio.
        """
        self.speed = 20
        self.x_pos_bg = 0
        self.points = 0
        self.obstacles.clear()
        self.cloud = Cloud()

    def update_score(self) -> None:
        """Incrementa la puntuación y aumenta la velocidad periódicamente.

        Cada ``SPEED_INCREMENT_INTERVAL`` puntos (100 por defecto), la
        velocidad sube en 1 hasta alcanzar ``MAX_SPEED`` (40 por defecto).

        Este método solo actualiza la lógica interna. Para dibujar
        la puntuación en pantalla, usar ``draw_score(screen)``.
        """
        self.points += 1
        if self.points % self.SPEED_INCREMENT_INTERVAL == 0:
            self.speed = min(self.speed + 1, self.MAX_SPEED)

    def spawn_obstacles(self) -> None:
        """Genera nuevos obstáculos cuando hay espacio suficiente.

        Calcula una distancia segura basada en la velocidad actual para
        evitar que aparezcan obstáculos imposibles de esquivar. Elige
        aleatoriamente entre cactus pequeño, cactus grande o pájaro.
        """
        distancia_segura = (self.speed * 21) + random.randint(50, 300)
        if len(self.obstacles) == 0 or (
            len(self.obstacles) < 2
            and self.obstacles[-1].rect.x < SCREEN_WIDTH - distancia_segura
        ):
            obstacle_type = random.randint(0, 2)
            if obstacle_type == 0:
                self.obstacles.append(SmallCactus(SMALL_CACTUS_IMG))
            elif obstacle_type == 1:
                self.obstacles.append(LargeCactus(LARGE_CACTUS_IMG))
            elif obstacle_type == 2:
                self.obstacles.append(Bird(BIRD_IMG))

    def update_obstacles(self) -> None:
        """Mueve los obstáculos y elimina los que salieron de pantalla.

        Itera sobre todos los obstáculos, los mueve hacia la izquierda
        según la velocidad del juego, y elimina los que ya no son visibles.
        """
        indices_to_remove: list[int] = []
        for i, obstacle in enumerate(self.obstacles):
            obstacle.update(self.speed)
            if obstacle.is_off_screen():
                indices_to_remove.append(i)
        for i in reversed(indices_to_remove):
            self.obstacles.pop(i)

    def get_observation(self, dino: Dinosaur) -> tuple[float, ...]:
        """Retorna la observación normalizada para el agente de IA.

        Detecta el obstáculo más cercano que esté por delante del
        dinosaurio y calcula las distancias y dimensiones normalizadas.

        Args:
            dino: Instancia del dinosaurio para calcular distancias relativas.

        Returns:
            Tupla con 5 valores normalizados en rango [0, 1]:

            - **posición_y_dino**: Qué tan alto/bajo está el dino.
            - **distancia_obstáculo**: Distancia horizontal al próximo obstáculo.
            - **altura_obstáculo**: Posición vertical del obstáculo.
            - **alto_obstáculo**: Tamaño vertical del obstáculo.
            - **velocidad_juego**: Velocidad actual normalizada.
        """
        obstaculo_objetivo = None
        for obs in self.obstacles:
            if obs.rect.x + obs.rect.width > dino.dino_rect.x:
                obstaculo_objetivo = obs
                break

        if obstaculo_objetivo:
            distancia = obstaculo_objetivo.rect.x - dino.dino_rect.x
            altura = obstaculo_objetivo.rect.y
            alto = obstaculo_objetivo.rect.height
        else:
            distancia = 1000
            altura = 0
            alto = 0

        return (
            dino.dino_rect.y / SCREEN_HEIGHT,
            min(distancia / 1000, 1.0),
            altura / SCREEN_HEIGHT,
            alto / SCREEN_HEIGHT,
            self.speed / 50,
        )

    # ------------------------------------------------------------------
    # Métodos de renderizado (solo se usan cuando hay display activo)
    # ------------------------------------------------------------------

    def draw_score(self, screen: pygame.Surface) -> None:
        """Dibuja la puntuación actual en la esquina superior derecha.

        Args:
            screen: Superficie de Pygame donde se renderiza el texto.
        """
        text = FONT.render("Points: " + str(self.points), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (1000, 40)
        screen.blit(text, text_rect)

    def background(self, screen: pygame.Surface) -> None:
        """Dibuja el fondo con efecto de scroll infinito (parallax).

        Args:
            screen: Superficie de Pygame donde se renderiza el fondo.
        """
        image_width = BG_IMG.get_width()
        screen.blit(BG_IMG, (self.x_pos_bg, self.y_pos_bg))
        screen.blit(BG_IMG, (image_width + self.x_pos_bg, self.y_pos_bg))
        if self.x_pos_bg <= -image_width:
            screen.blit(BG_IMG, (image_width + self.x_pos_bg, self.y_pos_bg))
            self.x_pos_bg = 0
        self.x_pos_bg -= self.speed
