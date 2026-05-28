from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .chain_simulation import ChainSimulationResult, format_chain_simulation, simulate_chain
from .chemistry import PROPERTY_NAMES
from .model import DEFAULT_SHELL_SURVIVAL_BONUS, TARGET_SEQUENCE


@dataclass(frozen=True, slots=True)
class ChainReportPaths:
    chain_score_json: Path
    chain_score_csv: Path
    chain_report_txt: Path
    simulation_summary_csv: Path


def chain_score_dict(result: ChainSimulationResult) -> dict:
    evaluation = result.evaluation
    return {
        "chain": "-".join(evaluation.chain),
        "environment": evaluation.environment or "none",
        "viability": evaluation.viability,
        "viability_score": evaluation.viability_score,
        "predicted_functions": list(evaluation.predicted_functions),
        "missing_functions": list(evaluation.missing_functions),
        "recommendations": list(evaluation.recommendations),
        "properties": dict(evaluation.properties),
        "function_scores": dict(evaluation.function_scores),
    }


def simulation_summary_dict(result: ChainSimulationResult) -> dict:
    genes = "+".join(result.genes)
    return {
        "chain": "-".join(result.evaluation.chain),
        "environment": result.evaluation.environment or "none",
        "genes": genes,
        "runs": result.runs,
        "generations": result.generations,
        "survival_rate": result.survival_rate,
        "code_preservation_rate": result.code_preservation_rate,
        "avg_final_population": result.avg_final_population,
        "avg_final_stability": result.avg_final_stability,
        "avg_best_fitness": result.avg_best_fitness,
    }


def write_chain_score_json(result: ChainSimulationResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(json.dumps(chain_score_dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_chain_score_csv(result: ChainSimulationResult, output_path: str | Path) -> None:
    path = Path(output_path)
    evaluation = result.evaluation
    row = {
        "chain": "-".join(evaluation.chain),
        "environment": evaluation.environment or "none",
        "viability": evaluation.viability,
        "viability_score": evaluation.viability_score,
        "predicted_functions": "+".join(evaluation.predicted_functions),
        "missing_functions": "+".join(evaluation.missing_functions),
        "recommendations": " | ".join(evaluation.recommendations),
    }
    for name in PROPERTY_NAMES:
        row[name] = evaluation.properties[name]
    for gene, score in evaluation.function_scores.items():
        row[gene] = score

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def write_simulation_summary_csv(result: ChainSimulationResult, output_path: str | Path) -> None:
    path = Path(output_path)
    row = simulation_summary_dict(result)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def format_chain_report(result: ChainSimulationResult) -> str:
    evaluation = result.evaluation
    functions = " + ".join(evaluation.predicted_functions) if evaluation.predicted_functions else "none"
    missing = ", ".join(evaluation.missing_functions) if evaluation.missing_functions else "none"

    lines = [
        "Silive chain report",
        "===================",
        "",
        f"Chain: {'-'.join(evaluation.chain)}",
        f"Environment: {evaluation.environment or 'none'}",
        f"Viability class: {evaluation.viability}",
        f"Viability score: {evaluation.viability_score:.3f}",
        f"Predicted functions: {functions}",
        f"Missing functions: {missing}",
        "",
        "Properties:",
    ]
    for name in PROPERTY_NAMES:
        lines.append(f"  - {name}: {evaluation.properties[name]:.3f}")

    lines.extend(["", "Function scores:"])
    for gene, score in evaluation.function_scores.items():
        lines.append(f"  - {gene}: {score:.3f}")

    lines.extend(["", "Recommendations:"])
    if evaluation.recommendations:
        for recommendation in evaluation.recommendations:
            lines.append(f"  - {recommendation}")
    else:
        lines.append("  - no missing required or long-term functions detected")

    lines.extend(["", format_chain_simulation(result)])
    return "\n".join(lines) + "\n"


def write_chain_report_txt(result: ChainSimulationResult, output_path: str | Path) -> None:
    Path(output_path).write_text(format_chain_report(result), encoding="utf-8")


def write_chain_report_outputs(result: ChainSimulationResult, output_dir: str | Path) -> ChainReportPaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    paths = ChainReportPaths(
        chain_score_json=directory / "chain_score.json",
        chain_score_csv=directory / "chain_score.csv",
        chain_report_txt=directory / "chain_report.txt",
        simulation_summary_csv=directory / "simulation_summary.csv",
    )
    write_chain_score_json(result, paths.chain_score_json)
    write_chain_score_csv(result, paths.chain_score_csv)
    write_chain_report_txt(result, paths.chain_report_txt)
    write_simulation_summary_csv(result, paths.simulation_summary_csv)
    return paths


def create_chain_report(
    chain: str | Iterable[str],
    *,
    output_dir: str | Path,
    environment: str | None = None,
    generations: int = 100,
    runs: int = 20,
    seed: int | None = None,
    start_sequence: str = TARGET_SEQUENCE,
    population_limit: int = 100,
    start_population: int = 10,
    base_mutation_rate: float = 0.08,
    gene_mutation_rate: float = 0.03,
    shell_survival_bonus: float = DEFAULT_SHELL_SURVIVAL_BONUS,
) -> tuple[ChainSimulationResult, ChainReportPaths]:
    result = simulate_chain(
        chain,
        environment=environment,
        generations=generations,
        runs=runs,
        seed=seed,
        start_sequence=start_sequence,
        population_limit=population_limit,
        start_population=start_population,
        base_mutation_rate=base_mutation_rate,
        gene_mutation_rate=gene_mutation_rate,
        shell_survival_bonus=shell_survival_bonus,
    )
    paths = write_chain_report_outputs(result, output_dir)
    return result, paths
