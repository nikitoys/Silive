from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from .chemistry import ChainEvaluation, evaluate_chain
from .model import DEFAULT_SHELL_SURVIVAL_BONUS, TARGET_SEQUENCE, SimulationConfig, simulate


@dataclass(frozen=True, slots=True)
class ChainSimulationResult:
    evaluation: ChainEvaluation
    genes: tuple[str, ...]
    runs: int
    generations: int
    survival_rate: float
    code_preservation_rate: float
    avg_final_population: float
    avg_final_stability: float
    avg_best_fitness: float


def _code_preservation(population: list, target_sequence: str) -> float:
    if not population:
        return 0.0
    preserved = sum(1 for organism in population if organism.sequence == target_sequence)
    return preserved / len(population)


def simulate_chain(
    chain: str | Iterable[str],
    *,
    generations: int = 100,
    runs: int = 20,
    seed: int | None = None,
    start_sequence: str = TARGET_SEQUENCE,
    population_limit: int = 100,
    start_population: int = 10,
    base_mutation_rate: float = 0.08,
    gene_mutation_rate: float = 0.03,
    shell_survival_bonus: float = DEFAULT_SHELL_SURVIVAL_BONUS,
) -> ChainSimulationResult:
    if generations <= 0:
        raise ValueError("generations must be positive")
    if runs <= 0:
        raise ValueError("runs must be positive")

    evaluation = evaluate_chain(chain)
    genes = tuple(sorted(evaluation.predicted_functions))
    rng = random.Random(seed)

    survival_count = 0
    final_populations: list[int] = []
    code_preservation_rates: list[float] = []
    final_stabilities: list[float] = []
    final_fitnesses: list[float] = []

    for _ in range(runs):
        run_seed = rng.randrange(0, 2**32)
        population, history = simulate(
            SimulationConfig(
                generations=generations,
                population_limit=population_limit,
                start_population=start_population,
                start_sequence=start_sequence,
                start_genes=frozenset(genes),
                base_mutation_rate=base_mutation_rate,
                gene_mutation_rate=gene_mutation_rate,
                shell_survival_bonus=shell_survival_bonus,
                seed=run_seed,
            )
        )
        final_record = history[-1]
        final_populations.append(final_record["population"])
        code_preservation_rates.append(_code_preservation(population, start_sequence))

        if population:
            survival_count += 1
            final_stabilities.append(final_record["avg_stability"])
            final_fitnesses.append(final_record["best_fitness"])
        else:
            final_stabilities.append(0.0)
            final_fitnesses.append(0.0)

    return ChainSimulationResult(
        evaluation=evaluation,
        genes=genes,
        runs=runs,
        generations=generations,
        survival_rate=round(survival_count / runs, 3),
        code_preservation_rate=round(sum(code_preservation_rates) / runs, 3),
        avg_final_population=round(sum(final_populations) / runs, 3),
        avg_final_stability=round(sum(final_stabilities) / runs, 3),
        avg_best_fitness=round(sum(final_fitnesses) / runs, 3),
    )


def format_chain_simulation(result: ChainSimulationResult) -> str:
    genes = " + ".join(result.genes) if result.genes else "none"
    missing = ", ".join(result.evaluation.missing_functions) if result.evaluation.missing_functions else "none"

    return "\n".join(
        [
            f"chain: {'-'.join(result.evaluation.chain)}",
            f"viability: {result.evaluation.viability}",
            f"viability score: {result.evaluation.viability_score:.3f}",
            f"predicted functions: {genes}",
            f"missing functions: {missing}",
            "",
            "simulation:",
            f"  runs: {result.runs}",
            f"  generations: {result.generations}",
            f"  survival_rate: {result.survival_rate:.3f}",
            f"  code_preservation_rate: {result.code_preservation_rate:.3f}",
            f"  avg_final_population: {result.avg_final_population:.3f}",
            f"  avg_final_stability: {result.avg_final_stability:.3f}",
            f"  avg_best_fitness: {result.avg_best_fitness:.3f}",
        ]
    )
