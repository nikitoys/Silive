from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .chemistry import PROPERTY_NAMES, mutate_chain, parse_chain
from .environment_sweep import EnvironmentSweepResult, environment_label, run_environment_sweep
from .model import DEFAULT_SHELL_SURVIVAL_BONUS, TARGET_SEQUENCE


@dataclass(frozen=True, slots=True)
class NicheCandidate:
    chain: tuple[str, ...]
    environment: str | None
    mutation_count: int
    sweep: EnvironmentSweepResult
    result_index: int

    @property
    def simulation(self):
        return self.sweep.results[self.result_index]


@dataclass(frozen=True, slots=True)
class NicheSearchResult:
    seed_chain: tuple[str, ...]
    candidates: tuple[NicheCandidate, ...]
    top_candidates: tuple[NicheCandidate, ...]


@dataclass(frozen=True, slots=True)
class NicheSearchPaths:
    niche_search_csv: Path
    niche_search_json: Path


def niche_candidate_row(candidate: NicheCandidate) -> dict:
    simulation = candidate.simulation
    evaluation = simulation.evaluation
    row = {
        "chain": "-".join(candidate.chain),
        "environment": environment_label(candidate.environment),
        "mutation_count": candidate.mutation_count,
        "viability": evaluation.viability,
        "viability_score": evaluation.viability_score,
        "predicted_functions": "+".join(evaluation.predicted_functions),
        "missing_functions": "+".join(evaluation.missing_functions),
        "survival_rate": simulation.survival_rate,
        "code_preservation_rate": simulation.code_preservation_rate,
        "avg_final_population": simulation.avg_final_population,
        "avg_final_stability": simulation.avg_final_stability,
        "avg_best_fitness": simulation.avg_best_fitness,
        "runs": simulation.runs,
        "generations": simulation.generations,
    }
    for name in PROPERTY_NAMES:
        row[name] = evaluation.properties[name]
    for gene, score in evaluation.function_scores.items():
        row[gene] = score
    return row


def niche_candidate_sort_key(candidate: NicheCandidate) -> tuple[float, float, float, float]:
    simulation = candidate.simulation
    return (
        simulation.evaluation.viability_score,
        simulation.survival_rate,
        simulation.code_preservation_rate,
        simulation.avg_final_population,
    )


def run_niche_search(
    seed_chain: str | Iterable[str],
    *,
    rounds: int = 100,
    top_n: int = 10,
    seed: int | None = None,
    max_length: int = 16,
    generations: int = 100,
    runs: int = 20,
    start_sequence: str = TARGET_SEQUENCE,
    population_limit: int = 100,
    start_population: int = 10,
    base_mutation_rate: float = 0.08,
    gene_mutation_rate: float = 0.03,
    shell_survival_bonus: float = DEFAULT_SHELL_SURVIVAL_BONUS,
) -> NicheSearchResult:
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    rng = random.Random(seed)
    source = parse_chain(seed_chain)
    current = source
    seen: set[tuple[str, ...]] = set()
    candidates: list[NicheCandidate] = []

    for mutation_count in range(rounds + 1):
        if current not in seen:
            seen.add(current)
            sweep_seed = None if seed is None else seed + mutation_count * 1000
            sweep = run_environment_sweep(
                current,
                generations=generations,
                runs=runs,
                seed=sweep_seed,
                start_sequence=start_sequence,
                population_limit=population_limit,
                start_population=start_population,
                base_mutation_rate=base_mutation_rate,
                gene_mutation_rate=gene_mutation_rate,
                shell_survival_bonus=shell_survival_bonus,
            )
            for result_index, simulation in enumerate(sweep.results):
                candidates.append(
                    NicheCandidate(
                        chain=current,
                        environment=simulation.evaluation.environment,
                        mutation_count=mutation_count,
                        sweep=sweep,
                        result_index=result_index,
                    )
                )
        current = mutate_chain(current, rng, max_length=max_length)

    top_candidates = tuple(sorted(candidates, key=niche_candidate_sort_key, reverse=True)[:top_n])
    return NicheSearchResult(seed_chain=source, candidates=tuple(candidates), top_candidates=top_candidates)


def niche_search_rows(search: NicheSearchResult) -> list[dict]:
    return [niche_candidate_row(candidate) for candidate in search.top_candidates]


def niche_search_payload(search: NicheSearchResult) -> dict:
    return {
        "seed_chain": "-".join(search.seed_chain),
        "candidate_count": len(search.candidates),
        "top_candidates": niche_search_rows(search),
    }


def write_niche_search_csv(search: NicheSearchResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = niche_search_rows(search)
    if not rows:
        return
    fieldnames = ["rank", *list(rows[0])]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({"rank": rank, **row})


def write_niche_search_json(search: NicheSearchResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(niche_search_payload(search), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_niche_search_outputs(search: NicheSearchResult, output_dir: str | Path) -> NicheSearchPaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = NicheSearchPaths(
        niche_search_csv=directory / "niche_search.csv",
        niche_search_json=directory / "niche_search.json",
    )
    write_niche_search_csv(search, paths.niche_search_csv)
    write_niche_search_json(search, paths.niche_search_json)
    return paths


def format_niche_ranking(search: NicheSearchResult) -> str:
    lines = ["rank | score | survival | code | population | environment | viability | functions | chain"]
    lines.append("--- | ---: | ---: | ---: | ---: | --- | --- | --- | ---")
    for rank, candidate in enumerate(search.top_candidates, start=1):
        simulation = candidate.simulation
        evaluation = simulation.evaluation
        functions = "+".join(evaluation.predicted_functions) if evaluation.predicted_functions else "none"
        lines.append(
            f"{rank} | {evaluation.viability_score:.3f} | {simulation.survival_rate:.3f} | "
            f"{simulation.code_preservation_rate:.3f} | {simulation.avg_final_population:.3f} | "
            f"{environment_label(candidate.environment)} | {evaluation.viability} | {functions} | {'-'.join(candidate.chain)}"
        )
    return "\n".join(lines)
