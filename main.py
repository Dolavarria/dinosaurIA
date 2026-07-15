import pygame
import os
import random
import neat
import pickle

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
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < -self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))


class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self):
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

    def update(self):
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
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = 250
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index // 5], self.rect)
        self.index += 1


def score():
    global points, game_speed
    points += 1
    # Cada 100 frames, el juego se vuelve más rápido
    if points % 100 == 0:
        game_speed += 2

    text = FONT.render("Points: " + str(points), True, (0, 0, 0))
    textRect = text.get_rect()
    textRect.center = (1000, 40)
    SCREEN.blit(text, textRect)


def background():
    global x_pos_bg, y_pos_bg, game_speed
    image_width = BG.get_width()
    SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
    SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
    if x_pos_bg <= -image_width:
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        x_pos_bg = 0
    x_pos_bg -= game_speed


def eval_genomes(genomes, config):
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles
    game_speed = 20
    x_pos_bg = 0
    y_pos_bg = 380
    points = 0
    obstacles = []
    cloud = Cloud()

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
        if len(obstacles) == 0:
            obstacle_type = random.randint(0, 2)
            if obstacle_type == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS))
            elif obstacle_type == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS))
            elif obstacle_type == 2:
                obstacles.append(Bird(BIRD))

        for x, dino in enumerate(dinosaurios):
            dino.draw(SCREEN)
            dino.update()

            # Visión
            if len(obstacles) > 0:
                distancia_obstaculo = obstacles[0].rect.x - dino.dino_rect.x
                altura_obstaculo = obstacles[0].rect.y
            else:
                distancia_obstaculo = 1000
                altura_obstaculo = 0

            # Normalizar entradas para mejor aprendizaje
            # Rango: [0, 1]
            dino_y_norm = dino.dino_rect.y / SCREEN_HEIGHT
            distancia_norm = min(distancia_obstaculo / 1000, 1.0)  # Normalizar a ~1
            altura_norm = altura_obstaculo / SCREEN_HEIGHT
            speed_norm = game_speed / 50  # Rango típico es ~20-60

            # Recompensa por avanzar en el juego
            genomas[x].fitness += 0.1

            # Cerebro
            output = redes_neuronales[x].activate(
                (dino_y_norm, distancia_norm, altura_norm, speed_norm)
            )

            # Acción
            if output[0] > 0.5 and not dino.dino_jump:
                dino.dino_jump = True
                dino.dino_run = False
            elif not dino.dino_jump:
                dino.dino_run = True

        # Lógica de colisión
        obstacles_to_remove = []
        for i, obstacle in enumerate(obstacles):
            obstacle.draw(SCREEN)
            obstacle.update()

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
            obstacles.pop(i)

        background()
        cloud.draw(SCREEN)
        cloud.update()
        score()

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

    # Cargar desde checkpoint SI EXISTE, si no crear población nueva
    checkpoint_file = "neat-checkpoint-25"
    if os.path.exists(checkpoint_file):
        pop = neat.Checkpointer.restore_checkpoint(checkpoint_file)
        print(f"Cargado checkpoint: {checkpoint_file}")
    else:
        pop = neat.Population(config)
        print("Iniciando entrenamiento desde cero (población nueva)")

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    # Checkpoint automático (cada 5 generaciones)
    pop.add_reporter(neat.Checkpointer(5))

    # Iniciar el entrenamiento
    winner = pop.run(eval_genomes, 50)

    # Guardar al campeón definitivo
    print("\n¡Entrenamiento finalizado!")
    with open("campeon.pkl", "wb") as f:
        pickle.dump(winner, f)
        print("Cerebro del mejor dinosaurio guardado exitosamente como 'campeon.pkl'")


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
