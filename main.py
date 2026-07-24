"""Punto de entrada del proyecto Chrome Dinosaur AI.

Permite seleccionar y ejecutar diferentes algoritmos de entrenamiento
desde la línea de comandos usando subcomandos.

Uso::

    python main.py neat               # Entrenar con NEAT
    python main.py neat --force        # Re-entrenar aunque exista campeón
    python main.py neat --play         # Ver al campeón jugar
    python main.py neat --generations 100  # Cambiar número de generaciones
"""

import argparse
import sys


def main() -> None:
    """Parsea argumentos de la línea de comandos y ejecuta el trainer."""
    parser = argparse.ArgumentParser(
        description="Chrome Dinosaur AI — Entrenamiento con diferentes algoritmos",
        epilog="Ejemplo: python main.py neat --play",
    )
    subparsers = parser.add_subparsers(
        dest="algorithm",
        help="Algoritmo de IA a utilizar",
    )

    # -----------------------------------------------------------------
    # Subcomando: NEAT
    # -----------------------------------------------------------------
    neat_parser = subparsers.add_parser(
        "neat",
        help="Entrenar con NEAT (NeuroEvolution of Augmenting Topologies)",
    )
    neat_parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="Número máximo de generaciones (default: 50)",
    )
    neat_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-entrenar aunque ya exista un campeón",
    )
    neat_parser.add_argument(
        "--play",
        action="store_true",
        help="Ver al campeón guardado jugar (modo demo)",
    )

    # -----------------------------------------------------------------
    # Subcomando: DQN (Fase 2 — futuro)
    # -----------------------------------------------------------------
    # dqn_parser = subparsers.add_parser(
    #     "dqn",
    #     help="Entrenar con Deep Q-Network (Fase 2)",
    # )

    args = parser.parse_args()

    if args.algorithm == "neat":
        from trainers.neat_trainer import play_champion, run_neat

        if args.play:
            play_champion()
        else:
            run_neat(generations=args.generations, force=args.force)

    # elif args.algorithm == "dqn":
    #     from trainers.dqn_trainer import run_dqn
    #     run_dqn(...)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
