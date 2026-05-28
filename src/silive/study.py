from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .sweep import SweepConfig, run_sweep, write_csv

CORE_GENES = frozenset({"POL", "SEP", "SHELL"})
REPAIR_GENES = frozenset({"POL", "SEP", "SHELL", "REPAIR"})


@dataclass(frozen=True, slots=True)
class RepairStudyResult:
    without_repair_rows: list[dict]
    with_repair_rows: list[dict]
    delta_rows: list[dict]
    summary: dict


def _index_rows(rows: list[dict]) -> dict[tuple[float, float], dict]:
    return {
        (float(row["mutation_rate"]), float(row["shell_bonus"])): row
        for row in rows
    }


def _zone_score(zone: str) -> int:
    order = {
        "dead": 0,
        "unstable": 1,
        "drifting": 2,
        "proto_life": 3,
        "stable_life": 4,
    }
    return order.get(zone, -1)


def build_delta_rows(without_repair_rows: list[dict], with_repair_rows: list[dict]) -> list[dict]:
    without_index = _index_rows(without_repair_rows)
    with_index = _index_rows(with_repair_rows)
    keys = sorted(set(without_index) & set(with_index))
    delta_rows: list[dict] = []

    for key in keys:
        mutation_rate, shell_bonus = key
        base = without_index[key]
        repaired = with_index[key]
        survival_delta = float(repaired["survival_rate"]) - float(base["survival_rate"])
        code_delta = float(repaired["code_preservation_rate"]) - float(base["code_preservation_rate"])
        stability_delta = float(repaired["avg_final_stability"]) - float(base["avg_final_stability"])
        fitness_delta = float(repaired["avg_best_fitness"]) - float(base["avg_best_fitness"])
        zone_improvement = _zone_score(str(repaired["zone"])) - _zone_score(str(base["zone"]))

        delta_rows.append(
            {
                "mutation_rate": round(mutation_rate, 6),
                "shell_bonus": round(shell_bonus, 6),
                "base_genes": base["genes"],
                "repair_genes": repaired["genes"],
                "base_zone": base["zone"],
                "repair_zone": repaired["zone"],
                "survival_delta": round(survival_delta, 3),
                "code_preservation_delta": round(code_delta, 3),
                "avg_final_stability_delta": round(stability_delta, 3),
                "avg_best_fitness_delta": round(fitness_delta, 3),
                "zone_improvement": zone_improvement,
            }
        )

    return delta_rows


def summarize_repair_effect(delta_rows: list[dict]) -> dict:
    if not delta_rows:
        return {
            "points": 0,
            "positive_survival_points": 0,
            "positive_code_points": 0,
            "improved_zone_points": 0,
            "avg_survival_delta": 0.0,
            "avg_code_preservation_delta": 0.0,
            "max_survival_delta": 0.0,
            "max_code_preservation_delta": 0.0,
        }

    return {
        "points": len(delta_rows),
        "positive_survival_points": sum(1 for row in delta_rows if row["survival_delta"] > 0),
        "positive_code_points": sum(1 for row in delta_rows if row["code_preservation_delta"] > 0),
        "improved_zone_points": sum(1 for row in delta_rows if row["zone_improvement"] > 0),
        "avg_survival_delta": round(sum(row["survival_delta"] for row in delta_rows) / len(delta_rows), 3),
        "avg_code_preservation_delta": round(
            sum(row["code_preservation_delta"] for row in delta_rows) / len(delta_rows), 3
        ),
        "max_survival_delta": max(row["survival_delta"] for row in delta_rows),
        "max_code_preservation_delta": max(row["code_preservation_delta"] for row in delta_rows),
    }


def run_repair_study(base_config: SweepConfig) -> RepairStudyResult:
    without_repair_config = SweepConfig(
        mutation_rates=base_config.mutation_rates,
        shell_bonuses=base_config.shell_bonuses,
        genes=CORE_GENES,
        generations=base_config.generations,
        runs=base_config.runs,
        population_limit=base_config.population_limit,
        start_population=base_config.start_population,
        start_sequence=base_config.start_sequence,
        gene_mutation_rate=base_config.gene_mutation_rate,
        seed=base_config.seed,
    )
    with_repair_config = SweepConfig(
        mutation_rates=base_config.mutation_rates,
        shell_bonuses=base_config.shell_bonuses,
        genes=REPAIR_GENES,
        generations=base_config.generations,
        runs=base_config.runs,
        population_limit=base_config.population_limit,
        start_population=base_config.start_population,
        start_sequence=base_config.start_sequence,
        gene_mutation_rate=base_config.gene_mutation_rate,
        seed=base_config.seed,
    )

    without_repair_rows = run_sweep(without_repair_config)
    with_repair_rows = run_sweep(with_repair_config)
    delta_rows = build_delta_rows(without_repair_rows, with_repair_rows)
    summary = summarize_repair_effect(delta_rows)

    return RepairStudyResult(
        without_repair_rows=without_repair_rows,
        with_repair_rows=with_repair_rows,
        delta_rows=delta_rows,
        summary=summary,
    )


def write_delta_csv(rows: list[dict], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mutation_rate",
        "shell_bonus",
        "base_genes",
        "repair_genes",
        "base_zone",
        "repair_zone",
        "survival_delta",
        "code_preservation_delta",
        "avg_final_stability_delta",
        "avg_best_fitness_delta",
        "zone_improvement",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_repair_study_outputs(result: RepairStudyResult, output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "without_repair": output / "without_repair.csv",
        "with_repair": output / "with_repair.csv",
        "delta": output / "repair_delta.csv",
        "summary": output / "repair_summary.txt",
    }

    write_csv(result.without_repair_rows, paths["without_repair"])
    write_csv(result.with_repair_rows, paths["with_repair"])
    write_delta_csv(result.delta_rows, paths["delta"])

    with paths["summary"].open("w", encoding="utf-8") as handle:
        for key, value in result.summary.items():
            handle.write(f"{key}: {value}\n")

    return paths
