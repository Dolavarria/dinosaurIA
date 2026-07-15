import pygame
import os
import random
import glob
import neat
import pickle
import csv

pygame.init()

# Global Constants
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
FONT = pygame.font.Font("freesansbold.ttf", 20)

RUNNING = [
    pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png")),
]
JUMPING = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))
DUCKING = [
    pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png")),
]

SMALL_CACTUS = [
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png")),
]
LARGE_CACTUS = [
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png")),
]

BIRD = [
    pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
    pygame.image.load(os.path.join("Assets/Bird", "Bird2.png")),
]

CLOUD = pygame.image.load(os.path.join("Assets/Other", "Cloud.png"))
BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))


class MetricsLogger:
    """Clase para guardar métricas de entrenamiento en CSV"""

    def __init__(self, filename="training_metrics.csv"):
        self.filename = filename
        self.header_written = os.path.exists(filename) and os.path.getsize(filename) > 0

    def _write_header(self, writer):
        writer.writerow(
            [
                "generation",
                "best_fitness",
                "avg_fitness",
                "median_fitness",
                "min_fitness",
                "max_fitness",
                "num_species",
                "population_size",
            ]
        )

    def log_generation(self, gen, best, avg, median, min_f, max_f, species, pop_size):
        """Guardar métricas de una generación"""
        with open(self.filename, "a", newline="") as file:
            writer = csv.writer(file)

            if not self.header_written:
                self._write_header(writer)
                self.header_written = True

            writer.writerow(
                [
                    gen,
                    f"{best:.2f}",
                    f"{avg:.2f}",
                    f"{median:.2f}",
                    f"{min_f:.2f}",
                    f"{max_f:.2f}",
                    species,
                    pop_size,
                ]
            )

    def close(self):
        """Cerrar el archivo"""
        print(f"Métricas guardadas en: {self.filename}")


class GenerationMetricsReporter(neat.reporting.BaseReporter):
    """Reporter personalizado para NEAT que guarda métricas"""

    def __init__(self, logger):
        self.logger = logger
        self.generation = 0

    def end_generation(self, config, population, species_set):
        """Se ejecuta al final de cada generación"""
        # Obtener fitness de todos los genomas (solo los que fueron evaluados)
        fitnesses = [g.fitness for g in population.values() if g.fitness is not None]

        # Si no hay fitnesses válidas, retornar sin guardar
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


class Dinosaur:
    X_POS = 80
    Y_POS = 310
    Y_POS_DUCK = 340
    JUMP_VEL = 8.5

    def __init__(self):
        self.duck_img = DUCKING
        self.run_img = RUNNING
        self.jump_img = JUMPING

        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

    def update(self):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

    def duck(self):
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= int(self.jump_vel * 4)
            self.jump_vel -= 0.8
        if self.jump_vel < -self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL
            self.dino_rect.y = self.Y_POS

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))


class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self, game_speed):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))


class Obstacle:
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self, game_speed):
        self.rect.x -= game_speed

    def is_off_screen(self):
        """Retorna True si el obstáculo salió de la pantalla."""
        return self.rect.x < -self.rect.width

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 325


class LargeCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300


class Bird(Obstacle):
    # Alturas variables para que agacharse sea necesario
    # Bajo (270): el dino DEBE agacharse (colisiona corriendo, no agachado)
    # Suelo (320): el dino DEBE saltar (colisiona siempre, agacharse no ayuda)
    # Alto (200): decorativo, no colisiona con el dino
    BIRD_HEIGHTS = [270, 320, 200]

    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = random.choice(self.BIRD_HEIGHTS)
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index // 5], self.rect)
        self.index += 1


class Game:
    def __init__(self):
        self.speed = 20
        self.x_pos_bg = 0
        self.y_pos_bg = 380
        self.points = 0
        self.obstacles = []
        self.cloud = Cloud()

    def score(self):
        self.points += 1
        if self.points % 100 == 0:
            self.speed += 2
        text = FONT.render("Points: " + str(self.points), True, (0, 0, 0))
        textRect = text.get_rect()
        textRect.center = (1000, 40)
        SCREEN.blit(text, textRect)

    def background(self):
        image_width = BG.get_width()
        SCREEN.blit(BG, (self.x_pos_bg, self.y_pos_bg))
        SCREEN.blit(BG, (image_width + self.x_pos_bg, self.y_pos_bg))
        if self.x_pos_bg <= -image_width:
            SCREEN.blit(BG, (image_width + self.x_pos_bg, self.y_pos_bg))
            self.x_pos_bg = 0
        self.x_pos_bg -= self.speed


def eval_genomes(genomes, config):
    game = Game()

    dinosaurios = []
    redes_neuronales = []
    genomas = []

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

        SCREEN.fill((255, 255, 255))

        # Generación de obstáculos
        if len(game.obstacles) == 0:
            obstacle_type = random.randint(0, 2)
            if obstacle_type == 0:
                game.obstacles.append(SmallCactus(SMALL_CACTUS))
            elif obstacle_type == 1:
                game.obstacles.append(LargeCactus(LARGE_CACTUS))
            elif obstacle_type == 2:
                game.obstacles.append(Bird(BIRD))

        for x, dino in enumerate(dinosaurios):
            dino.draw(SCREEN)
            dino.update()

            # Visión: detectar el obstáculo más cercano
            if len(game.obstacles) > 0:
                distancia_obstaculo = game.obstacles[0].rect.x - dino.dino_rect.x
                altura_obstaculo = game.obstacles[0].rect.y
                alto_obstaculo = game.obstacles[0].rect.height
            else:
                distancia_obstaculo = 1000
                altura_obstaculo = 0
                alto_obstaculo = 0

            # Normalizar entradas para mejor aprendizaje
            # Rango: [0, 1]
            dino_y_norm = dino.dino_rect.y / SCREEN_HEIGHT
            distancia_norm = min(distancia_obstaculo / 1000, 1.0)
            altura_norm = altura_obstaculo / SCREEN_HEIGHT
            alto_norm = alto_obstaculo / SCREEN_HEIGHT  # Tamaño vertical del obstáculo
            speed_norm = game.speed / 50

            # Recompensa por avanzar en el juego
            genomas[x].fitness += 0.1

            # Cerebro: 5 entradas → 2 salidas [saltar, agacharse]
            output = redes_neuronales[x].activate(
                (dino_y_norm, distancia_norm, altura_norm, alto_norm, speed_norm)
            )

            # Acción: elegir la señal más fuerte por encima de 0.5
            saltar = output[0]
            agacharse = output[1]

            if dino.dino_jump:
                # Si está en el aire, no puede cambiar de acción
                pass
            elif saltar > 0.5 and saltar >= agacharse and dino.dino_rect.y == dino.Y_POS:
                # Saltar tiene prioridad si ambas superan 0.5 y saltar es mayor
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

        # Lógica de colisión
        obstacles_to_remove = []
        for i, obstacle in enumerate(game.obstacles):
            obstacle.draw(SCREEN)
            obstacle.update(game.speed)

            # Marcar obstáculos que salieron de pantalla
            if obstacle.is_off_screen():
                obstacles_to_remove.append(i)

            for x in range(len(dinosaurios) - 1, -1, -1):
                if dinosaurios[x].dino_rect.colliderect(obstacle.rect):
                    genomas[x].fitness -= 1
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


def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    # Cargar desde el checkpoint más reciente SI EXISTE, si no crear población nueva
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
        print("Cerebro del mejor dinosaurio guardado exitosamente como 'campeon.pkl'")


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
