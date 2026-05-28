from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .model import DEFAULT_SHELL_SURVIVAL_BONUS, TARGET_SEQUENCE, SimulationConfig, simulate


@dataclass(frozen=True, slots=True)
class SweepConfig:
    mutation_rates: Sequence[float]
    shell_bonuses: Sequence[float]
    genes: frozenset[str]
    generations: int = 100
    runs: int = 20
    population_limit: int = 100
    start_population: int = 10
    start_sequence: str = TARGET_SEQUENCE
    gene_mutation_rate: float = 0.03
    seed: int | None = None


def linspace(start: float, stop: float, steps: int) -> list[float]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if steps == 1:
        return [round(start, 10)]
    step = (stop - start) / (steps - 1)
    return [round(start + step * index, 10) for index in range(steps)]


def code_preservation(population, target: str = TARGET_SEQUENCE) -> float:
    if not population:
        return 0.0
    preserved = sum(1 for organism in population if organism.sequence == target)
    return preserved / len(population)


def classify_zone(survival_rate: float, code_preservation_rate: float, avg_final_stability: float) -> str:
    if survival_rate <= 0.05:
        return "dead"
    if survival_rate < 0.50:
        return "unstable"
    if code_preservation_rate < 0.50:
        return "drifting"
    if avg_final_stability > 0.88 and code_preservation_rate > 0.90:
        return "stable_life"
    return "proto_life"


def run_sweep(config: SweepConfig) -> list[dict]:
    rng = random.Random(config.seed)
    rows: list[dict] = []

    for mutation_rate in config.mutation_rates:
        for shell_bonus in config.shell_bonuses:
            survival_count = 0
            final_populations: list[int] = []
            final_stabilities: list[float] = []
            final_fitnesses: list[float] = []
            code_rates: list[float] = []

            for _ in range(config.runs):
                run_seed = rng.randrange(0, 2**32)
                population, history = simulate(
                    SimulationConfig(
                        generations=config.generations,
                        population_limit=config.population_limit,
                        start_population=config.start_population,
                        start_sequence=config.start_sequence,
                        start_genes=config.genes,
                        base_mutation_rate=mutation_rate,
                        gene_mutation_rate=config.gene_mutation_rate,
                        shell_survival_bonus=shell_bonus,
                        seed=run_seed,
                    )
                )
                final_record = history[-1]
                final_populations.append(final_record["population"])

                if population:
                    survival_count += 1
                    final_stabilities.append(final_record["avg_stability"])
                    final_fitnesses.append(final_record["best_fitness"])
                    code_rates.append(code_preservation(population, config.start_sequence))
                else:
                    final_stabilities.append(0.0)
                    final_fitnesses.append(0.0)
                    code_rates.append(0.0)

            survival_rate = survival_count / config.runs
            code_preservation_rate = sum(code_rates) / config.runs
            avg_final_stability = sum(final_stabilities) / config.runs

            rows.append(
                {
                    "mutation_rate": round(mutation_rate, 6),
                    "shell_bonus": round(shell_bonus, 6),
                    "genes": "+".join(sorted(config.genes)),
                    "runs": config.runs,
                    "generations": config.generations,
                    "survival_rate": round(survival_rate, 3),
                    "code_preservation_rate": round(code_preservation_rate, 3),
                    "avg_final_population": round(sum(final_populations) / config.runs, 3),
                    "avg_final_stability": round(avg_final_stability, 3),
                    "avg_best_fitness": round(sum(final_fitnesses) / config.runs, 3),
                    "zone": classify_zone(survival_rate, code_preservation_rate, avg_final_stability),
                }
            )

    return rows


def write_csv(rows: Iterable[dict], output_path: str | Path) -> None:
    rows = list(rows)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "mutation_rate",
        "shell_bonus",
        "genes",
        "runs",
        "generations",
        "survival_rate",
        "code_preservation_rate",
        "avg_final_population",
        "avg_final_stability",
        "avg_best_fitness",
        "zone",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def default_sweep_config() -> SweepConfig:
    return SweepConfig(
        mutation_rates=linspace(0.0, 0.30, 16),
        shell_bonuses=linspace(0.0, 0.40, 16),
        genes=frozenset({"POL", "SEP", "SHELL", "REPAIR"}),
        shell_bonuses_default=DEFAULT_SHELL_SURVIVAL_BONUS,
    )
