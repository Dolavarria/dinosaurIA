"""Punto de entrada para el entrenamiento con NEAT.

Este módulo contiene la lógica específica del algoritmo NEAT
(NeuroEvolution of Augmenting Topologies):

- ``eval_genomes``: Función de evaluación que simula una partida para
  cada genoma de la población.
- ``run``: Configura y ejecuta el ciclo de entrenamiento de NEAT.

La lógica del juego (clases, sprites, física) vive en el paquete ``game/``
y se importa desde ahí, permitiendo reutilizarla con otros algoritmos
(DQN, PPO) en fases futuras del proyecto.
"""

import glob
import os
import pickle
import random

import neat
import pygame

from game import (
    Bird,
    Dinosaur,
    Game,
    GenerationMetricsReporter,
    LargeCactus,
    MetricsLogger,
    SmallCactus,
)
from game.config import (
    BIRD_IMG,
    LARGE_CACTUS_IMG,
    SCREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SMALL_CACTUS_IMG,
)


def eval_genomes(
    genomes: list[tuple[int, neat.DefaultGenome]], config: neat.Config
) -> None:
    """Evalúa todos los genomas de una generación simulando una partida.

    Para cada genoma crea un dinosaurio y una red neuronal. Todos los
    dinosaurios juegan simultáneamente en la misma partida. El fitness
    se incrementa por sobrevivir y se penaliza al colisionar.

    Controles manuales durante la simulación:
    - **S**: Guarda el mejor genoma vivo como ``mejor_dinosaurio_manual.pkl``.
    - **Q**: Mata a todos los dinosaurios y pasa a la siguiente generación.

    Args:
        genomes: Lista de tuplas ``(genome_id, genome)`` de NEAT.
        config: Configuración activa de NEAT.
    """
    game = Game()

    dinosaurios: list[Dinosaur] = []
    redes_neuronales: list[neat.nn.FeedForwardNetwork] = []
    genomas: list[neat.DefaultGenome] = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        redes_neuronales.append(net)
        dinosaurios.append(Dinosaur())
        genomas.append(genome)

    clock = pygame.time.Clock()
    run = True

    while run and len(dinosaurios) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

            # Controles manuales
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    # Presionar 'S' para guardar el mejor dinosaurio actual
                    if genomas:
                        mejor_genoma = max(
                            genomas, key=lambda g: g.fitness
                        )
                        with open("mejor_dinosaurio_manual.pkl", "wb") as f:
                            pickle.dump(mejor_genoma, f)
                        print(
                            "¡Cerebro guardado manualmente! "
                            f"(Fitness: {mejor_genoma.fitness:.2f})"
                        )

                if event.key == pygame.K_q:
                    # Presionar 'Q' para matar a todos y pasar de generación
                    print("Generación terminada manualmente.")
                    dinosaurios.clear()
                    redes_neuronales.clear()
                    genomas.clear()

        SCREEN.fill((255, 255, 255))

        # Calculamos la distancia mínima para que el dinosaurio
        # alcance a aterrizar antes del próximo obstáculo
        distancia_segura = (game.speed * 21) + random.randint(50, 300)

        if len(game.obstacles) == 0 or (
            len(game.obstacles) < 2
            and game.obstacles[-1].rect.x < SCREEN_WIDTH - distancia_segura
        ):
            obstacle_type = random.randint(0, 2)
            if obstacle_type == 0:
                game.obstacles.append(SmallCactus(SMALL_CACTUS_IMG))
            elif obstacle_type == 1:
                game.obstacles.append(LargeCactus(LARGE_CACTUS_IMG))
            elif obstacle_type == 2:
                game.obstacles.append(Bird(BIRD_IMG))

        for x, dino in enumerate(dinosaurios):
            dino.draw(SCREEN)
            dino.update()

            # Visión: detectar el obstáculo más cercano ADELANTE del dino
            obstaculo_objetivo = None
            for obs in game.obstacles:
                if obs.rect.x + obs.rect.width > dino.dino_rect.x:
                    obstaculo_objetivo = obs
                    break

            if obstaculo_objetivo:
                distancia_obstaculo = (
                    obstaculo_objetivo.rect.x - dino.dino_rect.x
                )
                altura_obstaculo = obstaculo_objetivo.rect.y
                alto_obstaculo = obstaculo_objetivo.rect.height
            else:
                distancia_obstaculo = 1000
                altura_obstaculo = 0
                alto_obstaculo = 0

            # Normalizar entradas para mejor aprendizaje
            # Rango: [0, 1]
            dino_y_norm = dino.dino_rect.y / SCREEN_HEIGHT
            distancia_norm = min(distancia_obstaculo / 1000, 1.0)
            altura_norm = altura_obstaculo / SCREEN_HEIGHT
            alto_norm = alto_obstaculo / SCREEN_HEIGHT
            speed_norm = game.speed / 50

            # Recompensa por avanzar en el juego
            genomas[x].fitness += 0.1

            # Cerebro: 5 entradas → 2 salidas [saltar, agacharse]
            output = redes_neuronales[x].activate(
                (
                    dino_y_norm,
                    distancia_norm,
                    altura_norm,
                    alto_norm,
                    speed_norm,
                )
            )

            # Acción: elegir la señal más fuerte por encima de 0.5
            saltar = output[0]
            agacharse = output[1]

            if dino.dino_jump:
                # Si está en el aire, no puede cambiar de acción
                pass
            elif (
                saltar > 0.5
                and saltar >= agacharse
                and dino.dino_rect.y == dino.Y_POS
            ):
                # Saltar tiene prioridad si ambas superan 0.5
                dino.dino_jump = True
                dino.dino_run = False
                dino.dino_duck = False
            elif agacharse > 0.5:
                # Agacharse
                dino.dino_duck = True
                dino.dino_run = False
                dino.dino_jump = False
            else:
                # Correr (ninguna señal supera el umbral)
                dino.dino_run = True
                dino.dino_duck = False
                dino.dino_jump = False

            # Límite automático para evitar bucles infinitos
            if game.points >= 5000:
                print(
                    "¡Un dinosaurio ha superado los 5000 puntos! "
                    "Guardándolo y pasando a la siguiente generación."
                )
                mejor_genoma = max(genomas, key=lambda g: g.fitness)
                with open("mejor_dinosaurio_automatico.pkl", "wb") as f:
                    pickle.dump(mejor_genoma, f)
                dinosaurios.clear()
                redes_neuronales.clear()
                genomas.clear()
                break

        # Lógica de colisión
        obstacles_to_remove: list[int] = []
        for i, obstacle in enumerate(game.obstacles):
            obstacle.draw(SCREEN)
            obstacle.update(game.speed)

            # Marcar obstáculos que salieron de pantalla
            if obstacle.is_off_screen():
                obstacles_to_remove.append(i)

            for x in range(len(dinosaurios) - 1, -1, -1):
                if dinosaurios[x].dino_rect.colliderect(obstacle.rect):
                    genomas[x].fitness -= 2
                    dinosaurios.pop(x)
                    redes_neuronales.pop(x)
                    genomas.pop(x)

        # Limpiar obstáculos off-screen al final del loop
        for i in reversed(obstacles_to_remove):
            game.obstacles.pop(i)

        game.background()
        game.cloud.draw(SCREEN)
        game.cloud.update(game.speed)
        game.score()

        clock.tick(30)
        pygame.display.update()


def run(config_path: str) -> None:
    """Configura y ejecuta el ciclo de entrenamiento de NEAT.

    Carga la configuración desde un archivo, restaura el checkpoint más
    reciente si existe, agrega reporters para métricas y stdout, y
    lanza el entrenamiento por un máximo de 50 generaciones.

    Al finalizar, guarda el mejor genoma como ``campeon.pkl``.

    Args:
        config_path: Ruta al archivo de configuración de NEAT
                     (``config-feedforward.txt``).
    """
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    # Cargar desde el checkpoint más reciente SI EXISTE
    checkpoints = sorted(
        glob.glob("neat-checkpoint-*"),
        key=lambda f: int(f.split("-")[-1]),
    )
    if checkpoints:
        checkpoint_file = checkpoints[-1]
        pop = neat.Checkpointer.restore_checkpoint(checkpoint_file)
        print(f"Cargado checkpoint: {checkpoint_file}")
    else:
        pop = neat.Population(config)
        print("Iniciando entrenamiento desde cero (población nueva)")

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    # Crear logger de métricas y agregarlo como reporter
    metrics_logger = MetricsLogger("training_metrics.csv")
    pop.add_reporter(GenerationMetricsReporter(metrics_logger))

    # Checkpoint automático (cada 5 generaciones)
    pop.add_reporter(neat.Checkpointer(5))

    # Iniciar el entrenamiento
    winner = pop.run(eval_genomes, 50)

    # Cerrar el logger de métricas
    metrics_logger.close()

    # Guardar al campeón definitivo
    print("\n¡Entrenamiento finalizado!")
    with open("campeon.pkl", "wb") as f:
        pickle.dump(winner, f)
        print(
            "Cerebro del mejor dinosaurio guardado exitosamente "
            "como 'campeon.pkl'"
        )


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
