"""Paquete del juego Chrome Dinosaur.

Exporta las clases principales del juego para uso externo.
Este paquete es **algoritmo-agnóstico**: no depende de ninguna
librería de IA (ni NEAT, ni PyTorch, ni Gymnasium).

Uso típico::

    from game import Dinosaur, Game, MetricsLogger
    from game.config import SCREEN, SCREEN_HEIGHT
"""

from game.dinosaur import Dinosaur
from game.environment import Cloud, Game
from game.metrics import MetricsLogger
from game.obstacles import Bird, LargeCactus, Obstacle, SmallCactus

__all__ = [
    "Bird",
    "Cloud",
    "Dinosaur",
    "Game",
    "LargeCactus",
    "MetricsLogger",
    "Obstacle",
    "SmallCactus",
]
