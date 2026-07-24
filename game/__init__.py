"""Paquete del juego Chrome Dinosaur.

Exporta las clases principales del juego para uso externo.
Esto permite hacer imports limpios desde ``main.py``::

    from game import Dinosaur, SmallCactus, LargeCactus, Bird, Game
    from game import MetricsLogger, GenerationMetricsReporter
"""

from game.dinosaur import Dinosaur
from game.environment import Cloud, Game
from game.metrics import GenerationMetricsReporter, MetricsLogger
from game.obstacles import Bird, LargeCactus, Obstacle, SmallCactus

__all__ = [
    "Bird",
    "Cloud",
    "Dinosaur",
    "Game",
    "GenerationMetricsReporter",
    "LargeCactus",
    "MetricsLogger",
    "Obstacle",
    "SmallCactus",
]
