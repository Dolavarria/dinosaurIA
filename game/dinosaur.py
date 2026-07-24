"""Módulo del dinosaurio (jugador).

Contiene la clase ``Dinosaur`` que representa al personaje controlable
del juego. Gestiona los tres estados posibles: correr, saltar y agacharse.
"""

import pygame

from game.config import DUCKING_IMG, JUMPING_IMG, RUNNING_IMG


class Dinosaur:
    """Personaje principal del juego Chrome Dinosaur.

    El dinosaurio puede estar en uno de tres estados:
    - **Corriendo**: estado por defecto, avanza sobre el suelo.
    - **Saltando**: se eleva y cae siguiendo una parábola simple.
    - **Agachado**: reduce su hitbox para esquivar pájaros bajos.

    Attributes:
        X_POS: Posición horizontal fija del dinosaurio en pantalla.
        Y_POS: Posición vertical cuando está corriendo o saltando.
        Y_POS_DUCK: Posición vertical cuando está agachado (más abajo).
        JUMP_VEL: Velocidad inicial de salto.
    """

    X_POS: int = 80
    Y_POS: int = 310
    Y_POS_DUCK: int = 340
    JUMP_VEL: float = 8.5

    def __init__(self) -> None:
        self.duck_img = DUCKING_IMG
        self.run_img = RUNNING_IMG
        self.jump_img = JUMPING_IMG

        self.dino_duck: bool = False
        self.dino_run: bool = True
        self.dino_jump: bool = False

        self.step_index: int = 0
        self.jump_vel: float = self.JUMP_VEL
        self.image: pygame.Surface = self.run_img[0]
        self.dino_rect: pygame.Rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

    def update(self) -> None:
        """Actualiza el estado del dinosaurio según la acción activa."""
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

    def duck(self) -> None:
        """Ejecuta la animación de agacharse."""
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self) -> None:
        """Ejecuta la animación de correr."""
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def jump(self) -> None:
        """Ejecuta la física del salto (parábola simple)."""
        self.image = self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= int(self.jump_vel * 4)
            self.jump_vel -= 0.8
        if self.jump_vel < -self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL
            self.dino_rect.y = self.Y_POS

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el dinosaurio en la pantalla.

        Args:
            screen: Superficie de Pygame donde se dibuja el sprite.
        """
        screen.blit(self.image, (self.dino_rect.x, self.dino_rect.y))
