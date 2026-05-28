from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .chain_simulation import ChainSimulationResult, simulate_chain
from .chemistry import PROPERTY_NAMES, SUPPORTED_ENVIRONMENTS
from .model import DEFAULT_SHELL_SURVIVAL_BONUS, TARGET_SEQUENCE

ENVIRONMENT_SWEEP_ORDER: tuple[str | None, ...] = (None, *SUPPORTED_ENVIRONMENTS)


@dataclass(frozen=True, slots=True)
class EnvironmentSweepPaths:
    environment_sweep_csv: Path
    environment_sweep_json: Path


@dataclass(frozen=True, slots=True)
class EnvironmentSweepResult:
    chain: tuple[str, ...]
    results: tuple[ChainSimulationResult, ...]
    ranking: tuple[ChainSimulationResult, ...]


def environment_label(environment: str | None) -> str:
    return environment or "none"


def environment_sweep_row(result: ChainSimulationResult) -> dict:
    evaluation = result.evaluation
    row = {
        "environment": environment_label(evaluation.environment),
        "chain": "-".join(evaluation.chain),
        "viability": evaluation.viability,
        "viability_score": evaluation.viability_score,
        "predicted_functions": "+".join(evaluation.predicted_functions),
        "missing_functions": "+".join(evaluation.missing_functions),
        "survival_rate": result.survival_rate,
        "code_preservation_rate": result.code_preservation_rate,
        "avg_final_population": result.avg_final_population,
        "avg_final_stability": result.avg_final_stability,
        "avg_best_fitness": result.avg_best_fitness,
        "runs": result.runs,
        "generations": result.generations,
    }
    for name in PROPERTY_NAMES:
        row[name] = evaluation.properties[name]
    for gene, score in evaluation.function_scores.items():
        row[gene] = score
    return row


def environment_sweep_rows(sweep: EnvironmentSweepResult) -> list[dict]:
    return [environment_sweep_row(result) for result in sweep.results]


def environment_sweep_payload(sweep: EnvironmentSweepResult) -> dict:
    return {
        "chain": "-".join(sweep.chain),
        "environments": environment_sweep_rows(sweep),
        "ranking": [environment_sweep_row(result) for result in sweep.ranking],
    }


def run_environment_sweep(
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
) -> EnvironmentSweepResult:
    results: list[ChainSimulationResult] = []
    for index, environment in enumerate(ENVIRONMENT_SWEEP_ORDER):
        run_seed = None if seed is None else seed + index
        results.append(
            simulate_chain(
                chain,
                environment=environment,
                generations=generations,
                runs=runs,
                seed=run_seed,
                start_sequence=start_sequence,
                population_limit=population_limit,
                start_population=start_population,
                base_mutation_rate=base_mutation_rate,
                gene_mutation_rate=gene_mutation_rate,
                shell_survival_bonus=shell_survival_bonus,
            )
        )

    ranking = tuple(
        sorted(
            results,
            key=lambda result: (
                result.evaluation.viability_score,
                result.survival_rate,
                result.code_preservation_rate,
                result.avg_final_population,
            ),
            reverse=True,
        )
    )
    return EnvironmentSweepResult(chain=results[0].evaluation.chain, results=tuple(results), ranking=ranking)


def write_environment_sweep_csv(sweep: EnvironmentSweepResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = environment_sweep_rows(sweep)
    if not rows:
        return
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_environment_sweep_json(sweep: EnvironmentSweepResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(environment_sweep_payload(sweep), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_environment_sweep_outputs(sweep: EnvironmentSweepResult, output_dir: str | Path) -> EnvironmentSweepPaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = EnvironmentSweepPaths(
        environment_sweep_csv=directory / "environment_sweep.csv",
        environment_sweep_json=directory / "environment_sweep.json",
    )
    write_environment_sweep_csv(sweep, paths.environment_sweep_csv)
    write_environment_sweep_json(sweep, paths.environment_sweep_json)
    return paths


def format_environment_ranking(sweep: EnvironmentSweepResult) -> str:
    lines = ["rank | environment | viability_score | survival_rate | code_preservation_rate | viability | functions"]
    lines.append("--- | --- | ---: | ---: | ---: | --- | ---")
    for rank, result in enumerate(sweep.ranking, start=1):
        evaluation = result.evaluation
        functions = "+".join(evaluation.predicted_functions) if evaluation.predicted_functions else "none"
        lines.append(
            f"{rank} | {environment_label(evaluation.environment)} | "
            f"{evaluation.viability_score:.3f} | {result.survival_rate:.3f} | "
            f"{result.code_preservation_rate:.3f} | {evaluation.viability} | {functions}"
        )
    return "\n".join(lines)
