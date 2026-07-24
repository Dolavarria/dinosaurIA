"""Entrenador basado en NEAT (NeuroEvolution of Augmenting Topologies).

Este módulo contiene toda la lógica específica del algoritmo NEAT:

- ``GenerationMetricsReporter``: Reporter que calcula y guarda métricas
  de cada generación.
- ``eval_genomes``: Función de evaluación que simula una partida para
  cada genoma de la población.
- ``run_neat``: Configura y ejecuta el ciclo de entrenamiento.
- ``play_champion``: Carga al campeón y lo muestra jugando en modo demo.

La lógica del juego (clases, sprites, física) se importa desde el
paquete ``game/``, que es algoritmo-agnóstico y reutilizable.
"""

import glob
import pickle
from pathlib import Path
from typing import Any

import neat
import pygame

from game import Dinosaur, Game, MetricsLogger
from game.config import SCREEN

# ---------------------------------------------------------------------------
# Rutas del proyecto (relativas al directorio raíz)
# ---------------------------------------------------------------------------
# Se usa __file__ para que las rutas funcionen sin importar desde
# dónde se ejecute el script (ej: python main.py, python -m trainers, etc.)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

MODELS_DIR: Path = PROJECT_ROOT / "models" / "neat"
CHAMPION_PATH: Path = MODELS_DIR / "campeon.pkl"
MANUAL_SAVE_PATH: Path = MODELS_DIR / "guardado_manual.pkl"
CONFIG_PATH: Path = PROJECT_ROOT / "config-feedforward.txt"
METRICS_PATH: Path = PROJECT_ROOT / "training_metrics.csv"

# ---------------------------------------------------------------------------
# Constantes de entrenamiento
# ---------------------------------------------------------------------------
AUTO_SAVE_THRESHOLD: int = 5000
"""Puntos que debe alcanzar un dinosaurio para ser guardado automáticamente."""


# =========================================================================
# Reporter de Métricas (específico de NEAT)
# =========================================================================
class GenerationMetricsReporter(neat.reporting.BaseReporter):
    """Reporter personalizado de NEAT que calcula y guarda métricas.

    Se conecta al ciclo de vida de NEAT a través del método
    ``end_generation``, que se ejecuta automáticamente al terminar
    cada generación.

    Args:
        logger: Instancia de ``MetricsLogger`` donde se persisten los datos.
    """

    def __init__(self, logger: MetricsLogger) -> None:
        self.logger = logger
        self.generation: int = 0

    def end_generation(
        self,
        config: neat.Config,
        population: dict[int, Any],
        species_set: neat.DefaultSpeciesSet,
    ) -> None:
        """Calcula estadísticas de fitness y las registra en el logger.

        Se ejecuta automáticamente al final de cada generación de NEAT.

        Args:
            config: Configuración activa de NEAT.
            population: Diccionario de genomas de la generación actual.
            species_set: Conjunto de especies activas.
        """
        # Obtener fitness de todos los genomas evaluados
        fitnesses = [
            g.fitness for g in population.values() if g.fitness is not None
        ]

        # Si no hay fitnesses válidas, avanzar sin guardar
        if not fitnesses:
            self.generation += 1
            return

        # Calcular estadísticas
        best = max(fitnesses)
        avg = sum(fitnesses) / len(fitnesses)
        median = sorted(fitnesses)[len(fitnesses) // 2]
        min_f = min(fitnesses)
        max_f = max(fitnesses)

        # Número de especies y tamaño de población
        num_species = len(species_set.species)
        pop_size = len(population)

        # Guardar en CSV
        self.logger.log_generation(
            gen=self.generation,
            best=best,
            avg=avg,
            median=median,
            min_f=min_f,
            max_f=max_f,
            species=num_species,
            pop_size=pop_size,
        )

        self.generation += 1


# =========================================================================
# Guardado de Campeón (progresivo)
# =========================================================================
def _save_champion(
    genome: neat.DefaultGenome,
    path: Path,
    reason: str,
    force_overwrite: bool = False,
) -> None:
    """Guarda el genoma como campeón, solo si es mejor que el existente.

    Si ya existe un campeón guardado con fitness igual o superior,
    no se sobreescribe (a menos que ``force_overwrite=True``).

    Args:
        genome: Genoma a guardar.
        path: Ruta del archivo ``.pkl`` de destino.
        reason: Motivo del guardado (se imprime en consola).
        force_overwrite: Si es ``True``, ignora la comparación de fitness.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Si ya existe un campeón, solo sobreescribir si el nuevo es mejor o si es guardado forzado
    if path.exists() and not force_overwrite:
        with open(path, "rb") as f:
            existing = pickle.load(f)
        if existing.fitness >= genome.fitness:
            print(
                f"ℹ️  Campeón actual (fitness {existing.fitness:.2f}) "
                f"es igual o mejor. No se sobreescribe."
            )
            return

    with open(path, "wb") as f:
        pickle.dump(genome, f)
    print(f"🏆 Campeón guardado (fitness {genome.fitness:.2f}) — {reason}")


# =========================================================================
# Función de Evaluación de NEAT
# =========================================================================
def eval_genomes(
    genomes: list[tuple[int, neat.DefaultGenome]], config: neat.Config
) -> None:
    """Evalúa todos los genomas de una generación simulando una partida.

    Para cada genoma crea un dinosaurio y una red neuronal. Todos los
    dinosaurios juegan simultáneamente en la misma partida. El fitness
    se incrementa por sobrevivir (+0.1/frame) y se penaliza al
    colisionar (-2).

    Controles manuales durante la simulación:

    - **S**: Guarda el mejor genoma vivo en ``models/neat/guardado_manual.pkl``.
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
                        mejor = max(genomas, key=lambda g: g.fitness)
                        _save_champion(
                            mejor,
                            MANUAL_SAVE_PATH,
                            "Guardado manual (tecla S)",
                            force_overwrite=True,
                        )

                if event.key == pygame.K_q:
                    # Presionar 'Q' para matar a todos y pasar de generación
                    print("Generación terminada manualmente.")
                    dinosaurios.clear()
                    redes_neuronales.clear()
                    genomas.clear()

        SCREEN.fill((255, 255, 255))

        # Generar obstáculos si hay espacio
        game.spawn_obstacles()

        for x, dino in enumerate(dinosaurios):
            dino.draw(SCREEN)
            dino.update()

            # Observación normalizada (reutilizable por cualquier algoritmo)
            observation = game.get_observation(dino)

            # Recompensa por avanzar en el juego
            genomas[x].fitness += 0.1

            # Cerebro: 5 entradas → 2 salidas [saltar, agacharse]
            output = redes_neuronales[x].activate(observation)

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
            if game.points >= AUTO_SAVE_THRESHOLD:
                print(
                    f"¡Un dinosaurio ha superado los {AUTO_SAVE_THRESHOLD} "
                    f"puntos! Guardándolo y pasando a la siguiente generación."
                )
                mejor = max(genomas, key=lambda g: g.fitness)
                _save_champion(
                    mejor,
                    CHAMPION_PATH,
                    f"{AUTO_SAVE_THRESHOLD} puntos alcanzados",
                )
                dinosaurios.clear()
                redes_neuronales.clear()
                genomas.clear()
                break

        # Dibujar obstáculos y verificar colisiones
        for obstacle in game.obstacles:
            obstacle.draw(SCREEN)
            for x in range(len(dinosaurios) - 1, -1, -1):
                if dinosaurios[x].dino_rect.colliderect(obstacle.rect):
                    genomas[x].fitness -= 2
                    dinosaurios.pop(x)
                    redes_neuronales.pop(x)
                    genomas.pop(x)

        # Mover obstáculos y limpiar los que salieron de pantalla
        game.update_obstacles()

        # Renderizar entorno
        game.background(SCREEN)
        game.cloud.draw(SCREEN)
        game.cloud.update(game.speed)
        game.update_score()
        game.draw_score(SCREEN)

        clock.tick(30)
        pygame.display.update()


# =========================================================================
# Modo Demo: Ver al campeón jugar
# =========================================================================
def play_champion() -> None:
    """Carga al campeón guardado y lo muestra jugando en modo demo.

    El campeón juega una partida completa hasta que colisiona con un
    obstáculo o el usuario cierra la ventana (Q o botón de cerrar).
    """
    if not CHAMPION_PATH.exists():
        print("❌ No hay campeón guardado.")
        print(f"   Esperado en: {CHAMPION_PATH}")
        print("   Ejecutá 'python main.py neat' para entrenar primero.")
        return

    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        str(CONFIG_PATH),
    )

    with open(CHAMPION_PATH, "rb") as f:
        champion = pickle.load(f)

    print(f"🏆 Cargando campeón (fitness: {champion.fitness:.2f})")
    print("   Presioná Q o cerrá la ventana para salir.")

    net = neat.nn.FeedForwardNetwork.create(champion, config)
    game = Game()
    dino = Dinosaur()
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False

        SCREEN.fill((255, 255, 255))

        game.spawn_obstacles()

        dino.update()
        dino.draw(SCREEN)

        # El campeón decide qué hacer
        observation = game.get_observation(dino)
        output = net.activate(observation)

        saltar = output[0]
        agacharse = output[1]

        if dino.dino_jump:
            pass
        elif (
            saltar > 0.5
            and saltar >= agacharse
            and dino.dino_rect.y == dino.Y_POS
        ):
            dino.dino_jump = True
            dino.dino_run = False
            dino.dino_duck = False
        elif agacharse > 0.5:
            dino.dino_duck = True
            dino.dino_run = False
            dino.dino_jump = False
        else:
            dino.dino_run = True
            dino.dino_duck = False
            dino.dino_jump = False

        # Dibujar obstáculos y verificar colisión
        for obstacle in game.obstacles:
            obstacle.draw(SCREEN)
            if dino.dino_rect.colliderect(obstacle.rect):
                print(f"💀 Colisión. Puntuación final: {game.points}")
                running = False
                break

        game.update_obstacles()

        game.background(SCREEN)
        game.cloud.draw(SCREEN)
        game.cloud.update(game.speed)
        game.update_score()
        game.draw_score(SCREEN)

        clock.tick(30)
        pygame.display.update()

    pygame.time.wait(2000)
    pygame.quit()


# =========================================================================
# Función Principal de Entrenamiento NEAT
# =========================================================================
def run_neat(generations: int = 50, force: bool = False) -> None:
    """Configura y ejecuta el ciclo de entrenamiento de NEAT.

    Antes de entrenar, verifica si ya existe un campeón guardado.
    Si existe, detiene el entrenamiento y sugiere usar ``--force``
    o ``--play``.

    Carga la configuración desde ``config-feedforward.txt``, restaura
    el checkpoint más reciente si existe, agrega reporters para
    métricas y stdout, y lanza el entrenamiento.

    Args:
        generations: Número máximo de generaciones a entrenar.
        force: Si es ``True``, re-entrena aunque ya exista un campeón.
    """
    # Verificar si ya existe un campeón
    if CHAMPION_PATH.exists() and not force:
        with open(CHAMPION_PATH, "rb") as f:
            existing = pickle.load(f)
        print("=" * 60)
        print("⚠️  Ya existe un campeón entrenado.")
        print(f"   Archivo: {CHAMPION_PATH}")
        print(f"   Fitness: {existing.fitness:.2f}")
        print()
        print("   Opciones:")
        print("   • python main.py neat --force  → Re-entrenar desde cero")
        print("   • python main.py neat --play   → Ver al campeón jugar")
        print("=" * 60)
        return

    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        str(CONFIG_PATH),
    )

    # Cargar desde el checkpoint más reciente SI EXISTE
    checkpoint_pattern = str(PROJECT_ROOT / "neat-checkpoint-*")
    checkpoints = sorted(
        glob.glob(checkpoint_pattern),
        key=lambda f: int(f.split("-")[-1]),
    )

    if checkpoints and not force:
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
    metrics_logger = MetricsLogger(str(METRICS_PATH))
    pop.add_reporter(GenerationMetricsReporter(metrics_logger))

    # Checkpoint automático (cada 5 generaciones)
    checkpoint_prefix = str(PROJECT_ROOT / "neat-checkpoint-")
    pop.add_reporter(neat.Checkpointer(5, filename_prefix=checkpoint_prefix))

    # Iniciar el entrenamiento
    winner = pop.run(eval_genomes, generations)

    # Cerrar el logger de métricas
    metrics_logger.close()

    # Guardar al campeón definitivo
    print("\n¡Entrenamiento finalizado!")
    _save_champion(winner, CHAMPION_PATH, "Entrenamiento completado")
