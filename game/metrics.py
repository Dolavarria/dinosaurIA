"""Módulo de métricas de entrenamiento.

Proporciona ``MetricsLogger``, una herramienta genérica para registrar
y persistir métricas de entrenamiento en formato CSV. Es compatible
con cualquier algoritmo de IA (NEAT, DQN, PPO, etc.) ya que solo se
encarga de escribir datos tabulares sin dependencias específicas.
"""

import csv
import os


class MetricsLogger:
    """Registra métricas de entrenamiento en un archivo CSV.

    Cada fila del CSV representa una generación/episodio e incluye:
    fitness (mejor, promedio, mediana, mínima, máxima), número de
    especies y tamaño de la población.

    Este logger es **algoritmo-agnóstico**: solo escribe datos.
    La responsabilidad de calcular las métricas es del trainer
    correspondiente (NEAT, DQN, etc.).

    Args:
        filename: Ruta del archivo CSV donde se guardan las métricas.
    """

    def __init__(self, filename: str = "metrics/neat/training_metrics.csv") -> None:
        self.filename = filename
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
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
            gen: Número de generación o episodio.
            best: Mejor fitness de la generación.
            avg: Fitness promedio.
            median: Fitness mediana.
            min_f: Fitness mínima.
            max_f: Fitness máxima.
            species: Número de especies activas (0 si no aplica).
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
