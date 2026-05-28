from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from .rdkit_search import evaluate_candidate, parse_candidate_file
from .reaction_simulator import simulate_reactions

DEFAULT_START_CANDIDATES = (
    "[Si]O[Si]",
    "[Si]O[Si]O[Fe]",
    "[Si]O[Si]O[Ni]",
    "[Si]OP(=O)(O)O",
)

MUTATION_OPERATORS = (
    "add_si_o_unit",
    "add_fe_o_center",
    "add_ni_o_center",
    "add_p_o_bridge",
    "close_si_o_ring_symbolically",
    "split_labile_bridge",
    "duplicate_si_o_segment",
    "remove_weak_terminal_group",
)


@dataclass(frozen=True, slots=True)
class EvolutionConfig:
    generations: int
    population_size: int
    elite_size: int
    mutation_rate: float
    reaction_rate: float
    seed: int | None
    start_candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvolutionCandidate:
    candidate_id: str
    parent_id: str | None
    molecule: str
    symbolic_description: str
    generation: int
    mutations: tuple[str, ...]
    applied_reactions: tuple[str, ...]
    candidate_score: float
    genome_score: float
    covered_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    detected_genes: tuple[str, ...]
    topology_tags: tuple[str, ...]
    viability: str


@dataclass(frozen=True, slots=True)
class EvolutionRun:
    config: EvolutionConfig
    history: list[EvolutionCandidate]
    final_population: list[EvolutionCandidate]
    best_candidate: EvolutionCandidate
    summary: dict[str, object]


def load_start_candidates(path: str | Path | None) -> tuple[str, ...]:
    if path is None:
        return DEFAULT_START_CANDIDATES
    parsed = parse_candidate_file(path)
    return tuple(molecule for molecule, _name in parsed) or DEFAULT_START_CANDIDATES


def _append_before_last_si(molecule: str, fragment: str) -> str:
    if molecule.endswith("[Si]"):
        return molecule[:-4] + fragment + "[Si]"
    return molecule + fragment


def mutate_molecule(molecule: str, rng: random.Random) -> tuple[str, str]:
    operator = rng.choice(MUTATION_OPERATORS)
    if operator == "add_si_o_unit":
        return molecule + "O[Si]", operator
    if operator == "add_fe_o_center":
        return molecule + "O[Fe]", operator
    if operator == "add_ni_o_center":
        return molecule + "O[Ni]", operator
    if operator == "add_p_o_bridge":
        return _append_before_last_si(molecule, "OP(=O)(O)O"), operator
    if operator == "close_si_o_ring_symbolically":
        return "[Si]1O[Si]O1", operator
    if operator == "split_labile_bridge":
        return molecule + ".[Si]O", operator
    if operator == "duplicate_si_o_segment":
        return molecule.replace("[Si]O[Si]", "[Si]O[Si]O[Si]", 1) if "[Si]O[Si]" in molecule else molecule + "O[Si]"
    if operator == "remove_weak_terminal_group":
        for suffix in ("O[Fe]", "O[Ni]", "O[Si]", ".[Si]O"):
            if molecule.endswith(suffix) and len(molecule) > len(suffix):
                return molecule[: -len(suffix)], operator
        return molecule, operator
    return molecule, operator


def _genes(candidate) -> tuple[str, ...]:
    return tuple(hit.gene_id for hit in candidate.gene_hits if hit.present)


def _symbolic_description(candidate, extra: str = "") -> str:
    chain = "-".join(candidate.rdkit_evaluation.symbolic_chain) or "invalid"
    tags = ",".join(candidate.symbolic_graph.topology_tags) or "no_topology"
    suffix = f" | {extra}" if extra else ""
    return f"chain={chain} | topology={tags}{suffix}"


def _candidate_from_molecule(
    molecule: str,
    *,
    candidate_id: str,
    parent_id: str | None,
    generation: int,
    mutations: tuple[str, ...],
    applied_reactions: tuple[str, ...],
    symbolic_note: str = "",
) -> EvolutionCandidate:
    evaluated = evaluate_candidate(molecule, candidate_id)
    return EvolutionCandidate(
        candidate_id=candidate_id,
        parent_id=parent_id,
        molecule=molecule,
        symbolic_description=_symbolic_description(evaluated, symbolic_note),
        generation=generation,
        mutations=mutations,
        applied_reactions=applied_reactions,
        candidate_score=evaluated.candidate_score,
        genome_score=evaluated.genome_evaluation.genome_score,
        covered_functions=evaluated.genome_evaluation.covered_functions,
        missing_functions=evaluated.genome_evaluation.missing_functions,
        detected_genes=_genes(evaluated),
        topology_tags=evaluated.symbolic_graph.topology_tags,
        viability=evaluated.viability,
    )


def _reaction_variant(parent: EvolutionCandidate, generation: int, index: int) -> EvolutionCandidate | None:
    evaluated = evaluate_candidate(parent.molecule, parent.candidate_id)
    reactions = simulate_reactions(evaluated.rdkit_evaluation, evaluated.symbolic_graph)
    if not reactions:
        return None
    best = reactions[0]
    symbolic_note = f"abstract_reaction={best.reaction_id}; expected_delta={best.delta_score:+.3f}; product={best.product_symbolic_description}"
    return EvolutionCandidate(
        candidate_id=f"g{generation}_r{index}",
        parent_id=parent.candidate_id,
        molecule=parent.molecule,
        symbolic_description=_symbolic_description(evaluated, symbolic_note),
        generation=generation,
        mutations=parent.mutations,
        applied_reactions=(*parent.applied_reactions, best.reaction_id),
        candidate_score=round(max(0.0, min(1.0, parent.candidate_score + best.delta_score * 0.5)), 3),
        genome_score=round(max(0.0, min(1.0, parent.genome_score + best.delta_score)), 3),
        covered_functions=tuple(sorted(set(parent.covered_functions) | set(best.new_functions))),
        missing_functions=tuple(function for function in parent.missing_functions if function not in set(best.new_functions)),
        detected_genes=parent.detected_genes,
        topology_tags=parent.topology_tags,
        viability="symbolic_reaction_candidate",
    )


def _sort_population(population: list[EvolutionCandidate]) -> list[EvolutionCandidate]:
    return sorted(population, key=lambda item: (item.candidate_score, item.genome_score), reverse=True)


def run_evolution(config: EvolutionConfig) -> EvolutionRun:
    rng = random.Random(config.seed)
    start = config.start_candidates or DEFAULT_START_CANDIDATES
    population = [
        _candidate_from_molecule(
            molecule,
            candidate_id=f"g0_c{index}",
            parent_id=None,
            generation=0,
            mutations=tuple(),
            applied_reactions=tuple(),
        )
        for index, molecule in enumerate(start, start=1)
    ]
    population = _sort_population(population)[: config.population_size]
    history: list[EvolutionCandidate] = list(population)

    for generation in range(1, config.generations + 1):
        elites = _sort_population(population)[: max(1, config.elite_size)]
        next_population: list[EvolutionCandidate] = list(elites)
        counter = 1
        while len(next_population) < config.population_size:
            parent = rng.choice(elites)
            child_molecule = parent.molecule
            mutations = list(parent.mutations)
            symbolic_note = ""
            if rng.random() <= config.mutation_rate:
                child_molecule, mutation = mutate_molecule(child_molecule, rng)
                mutations.append(mutation)
                symbolic_note = f"mutation={mutation}"
            child = _candidate_from_molecule(
                child_molecule,
                candidate_id=f"g{generation}_c{counter}",
                parent_id=parent.candidate_id,
                generation=generation,
                mutations=tuple(mutations),
                applied_reactions=parent.applied_reactions,
                symbolic_note=symbolic_note,
            )
            next_population.append(child)
            counter += 1

            if len(next_population) < config.population_size and rng.random() <= config.reaction_rate:
                reaction_child = _reaction_variant(parent, generation, counter)
                if reaction_child is not None:
                    next_population.append(reaction_child)
                    counter += 1

        population = _sort_population(next_population)[: config.population_size]
        history.extend(population)

    final_population = _sort_population(population)
    best = final_population[0]
    summary: dict[str, object] = {
        "generations": config.generations,
        "population_size": config.population_size,
        "elite_size": config.elite_size,
        "mutation_rate": config.mutation_rate,
        "reaction_rate": config.reaction_rate,
        "seed": config.seed,
        "history_size": len(history),
        "best_candidate_id": best.candidate_id,
        "best_candidate_score": best.candidate_score,
        "best_genome_score": best.genome_score,
        "best_viability": best.viability,
        "best_molecule": best.molecule,
    }
    return EvolutionRun(config=config, history=history, final_population=final_population, best_candidate=best, summary=summary)


def _candidate_row(candidate: EvolutionCandidate) -> dict[str, str]:
    return {
        "candidate_id": candidate.candidate_id,
        "parent_id": candidate.parent_id or "",
        "generation": str(candidate.generation),
        "molecule": candidate.molecule,
        "symbolic_description": candidate.symbolic_description,
        "mutations": ";".join(candidate.mutations),
        "applied_reactions": ";".join(candidate.applied_reactions),
        "candidate_score": f"{candidate.candidate_score:.3f}",
        "genome_score": f"{candidate.genome_score:.3f}",
        "covered_functions": ";".join(candidate.covered_functions),
        "missing_functions": ";".join(candidate.missing_functions),
        "detected_genes": ";".join(candidate.detected_genes),
        "topology_tags": ";".join(candidate.topology_tags),
        "viability": candidate.viability,
    }


def write_candidates_csv(candidates: list[EvolutionCandidate], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [_candidate_row(candidate) for candidate in candidates]
    fieldnames = list(rows[0].keys()) if rows else list(_candidate_row(EvolutionCandidate('', None, '', '', 0, tuple(), tuple(), 0, 0, tuple(), tuple(), tuple(), tuple(), '')).keys())
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_best_candidate(candidate: EvolutionCandidate) -> str:
    interpretation = "partial motif candidate"
    if not candidate.missing_functions:
        interpretation = "covers all minimal symbolic proto-genome functions"
    elif candidate.candidate_score >= 0.65:
        interpretation = "strong but incomplete symbolic proto-genome candidate"

    return "\n".join(
        [
            "best evolutionary candidate",
            "",
            f"candidate_id: {candidate.candidate_id}",
            f"parent_id: {candidate.parent_id or 'none'}",
            f"molecule: {candidate.molecule}",
            f"symbolic_description: {candidate.symbolic_description}",
            f"candidate_score: {candidate.candidate_score:.3f}",
            f"genome_score: {candidate.genome_score:.3f}",
            f"viability: {candidate.viability}",
            f"detected_genes: {', '.join(candidate.detected_genes) or 'none'}",
            f"covered_functions: {', '.join(candidate.covered_functions) or 'none'}",
            f"missing_functions: {', '.join(candidate.missing_functions) or 'none'}",
            f"topology_tags: {', '.join(candidate.topology_tags) or 'none'}",
            f"mutations: {', '.join(candidate.mutations) or 'none'}",
            f"applied_reactions: {', '.join(candidate.applied_reactions) or 'none'}",
            f"interpretation: {interpretation}",
        ]
    )


def write_evolution_outputs(run: EvolutionRun, output_dir: str | Path) -> None:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    write_candidates_csv(run.history, directory / "evolution_history.csv")
    write_candidates_csv(run.final_population, directory / "final_population.csv")
    (directory / "best_candidate.txt").write_text(format_best_candidate(run.best_candidate), encoding="utf-8")
    (directory / "summary.json").write_text(json.dumps(run.summary, indent=2, sort_keys=True), encoding="utf-8")


def format_evolution_summary(run: EvolutionRun) -> str:
    best = run.best_candidate
    return "\n".join(
        [
            "evolutionary RDKit/symbolic search",
            "",
            f"generations: {run.config.generations}",
            f"population_size: {run.config.population_size}",
            f"history_size: {len(run.history)}",
            f"best_candidate: {best.candidate_id}",
            f"best_score: {best.candidate_score:.3f}",
            f"best_genome_score: {best.genome_score:.3f}",
            f"best_molecule: {best.molecule}",
            f"covered_functions: {', '.join(best.covered_functions) or 'none'}",
            f"missing_functions: {', '.join(best.missing_functions) or 'none'}",
            f"viability: {best.viability}",
        ]
    )
