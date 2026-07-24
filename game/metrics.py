"""Módulo de métricas de entrenamiento.

Proporciona herramientas para registrar y persistir métricas de cada
generación durante el entrenamiento con NEAT:

- ``MetricsLogger``: Escribe métricas en un archivo CSV.
- ``GenerationMetricsReporter``: Reporter de NEAT que calcula estadísticas
  al final de cada generación y las envía al logger.
"""

import csv
import os
from typing import Any

import neat


class MetricsLogger:
    """Registra métricas de entrenamiento en un archivo CSV.

    Cada fila del CSV representa una generación e incluye:
    fitness (mejor, promedio, mediana, mínima, máxima), número de
    especies y tamaño de la población.

    Args:
        filename: Ruta del archivo CSV donde se guardan las métricas.
    """

    def __init__(self, filename: str = "training_metrics.csv") -> None:
        self.filename = filename
        self.header_written: bool = (
            os.path.exists(filename) and os.path.getsize(filename) > 0
        )

    def _write_header(self, writer: csv.writer) -> None:
        """Escribe la fila de encabezados en el CSV."""
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

    def log_generation(
        self,
        gen: int,
        best: float,
        avg: float,
        median: float,
        min_f: float,
        max_f: float,
        species: int,
        pop_size: int,
    ) -> None:
        """Guarda las métricas de una generación en el CSV.

        Args:
            gen: Número de generación.
            best: Mejor fitness de la generación.
            avg: Fitness promedio.
            median: Fitness mediana.
            min_f: Fitness mínima.
            max_f: Fitness máxima.
            species: Número de especies activas.
            pop_size: Tamaño de la población.
        """
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

    def close(self) -> None:
        """Imprime mensaje de confirmación al finalizar el entrenamiento."""
        print(f"Métricas guardadas en: {self.filename}")


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
