from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable

from .chain_simulation import simulate_chain
from .chemistry import evaluate_chain, mutate_chain, parse_chain, search_chains, validate_environment
from .evolutionary_search import mutate_molecule
from .proto_genes import detect_proto_genes
from .proto_genome import MINIMAL_FUNCTIONS, evaluate_proto_genome
from .rdkit_chemistry import RDKitUnavailableError, evaluate_rdkit_molecule
from .rdkit_search import parse_candidate_file
from .reaction_simulator import simulate_reactions
from .symbolic_graph import SymbolicGraph, build_symbolic_graph

SAFETY_DISCLAIMER = (
    "Silive is a computational symbolic simulator. It does not provide synthesis protocols, "
    "lab parameters, quantities, temperatures, pressures, timings, or operational experimental instructions."
)

DEFAULT_SCORE_WEIGHTS = {
    "template": 0.22,
    "copyability": 0.20,
    "separation": 0.18,
    "survival": 0.18,
    "function_retention": 0.17,
    "lineage_depth": 0.05,
}

CHAIN_TO_MINIMAL_FUNCTIONS = {
    "POL": ("TEMPLATE", "POLYMERIZE"),
    "SEP": ("SEPARATE",),
    "SHELL": ("PROTECT",),
    "REPAIR": ("REPAIR",),
    "CAT": ("CATALYZE",),
}


@dataclass(frozen=True, slots=True)
class ProtoGeneMetrics:
    template_score: float
    copyability_score: float
    separation_score: float
    survival_score: float
    function_retention_rate: float
    lineage_depth: int
    proto_gene_score: float


@dataclass(frozen=True, slots=True)
class ProtoGeneCandidate:
    candidate_id: str
    parent_id: str | None
    mode: str
    source: str
    motif: str
    generation: int
    molecular_validity: bool
    parse_error: str | None
    environment: str | None
    topology_tags: tuple[str, ...]
    covered_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    detected_genes: tuple[str, ...]
    genome_score: float
    viability_score: float
    viability: str
    graph_properties: dict[str, float]
    reaction_ids: tuple[str, ...]
    metrics: ProtoGeneMetrics


@dataclass(frozen=True, slots=True)
class LineageNode:
    candidate_id: str
    parent_id: str | None
    generation: int
    mode: str
    motif: str
    event_labels: tuple[str, ...]
    retained_functions: tuple[str, ...]
    lost_functions: tuple[str, ...]
    new_functions: tuple[str, ...]
    function_retention_rate: float
    lineage_depth: int
    parent_score: float
    proto_gene_score: float
    score_delta: float
    extinct: bool


@dataclass(frozen=True, slots=True)
class ProtoGeneLineageConfig:
    mode: str
    generations: int = 10
    population_size: int = 20
    rounds: int = 200
    runs: int = 10
    seed: int | None = None
    environment: str | None = None
    input_path: str | None = None
    seed_chain: str | None = None
    retention_threshold: float = 0.60
    max_lineage_depth: int = 10


@dataclass(frozen=True, slots=True)
class ProtoGeneLineageRun:
    config: ProtoGeneLineageConfig
    ranked_candidates: list[ProtoGeneCandidate]
    lineage_history: list[LineageNode]
    best_candidate: ProtoGeneCandidate | None
    summary: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProtoGeneOutputPaths:
    proto_gene_candidates_csv: Path
    lineage_history_csv: Path
    proto_gene_summary_json: Path
    best_proto_gene_json: Path
    proto_gene_report_md: Path


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _round_score(value: float) -> float:
    return round(_clamp(value), 3)


def _minimal_from_chain_genes(genes: Iterable[str]) -> tuple[str, ...]:
    covered: set[str] = set()
    for gene in genes:
        covered.update(CHAIN_TO_MINIMAL_FUNCTIONS.get(gene, tuple()))
    return tuple(function for function in MINIMAL_FUNCTIONS if function in covered)


def _missing_minimal(covered: Iterable[str]) -> tuple[str, ...]:
    covered_set = set(covered)
    return tuple(function for function in MINIMAL_FUNCTIONS if function not in covered_set)


def _terminal_count(graph: SymbolicGraph) -> int:
    return sum(1 for node in graph.nodes if "terminal" in node.tags)


def _reaction_ids_for(evaluation, graph: SymbolicGraph | None = None) -> tuple[str, ...]:
    if not evaluation.molecular_validity:
        return tuple()
    return tuple(result.reaction_id for result in simulate_reactions(evaluation, graph))


def _score_aggregate(
    *,
    template_score: float,
    copyability_score: float,
    separation_score: float,
    survival_score: float,
    function_retention_rate: float,
    lineage_depth: int,
    max_lineage_depth: int,
) -> float:
    normalized_depth = _clamp(lineage_depth / max(1, max_lineage_depth))
    score = (
        DEFAULT_SCORE_WEIGHTS["template"] * template_score
        + DEFAULT_SCORE_WEIGHTS["copyability"] * copyability_score
        + DEFAULT_SCORE_WEIGHTS["separation"] * separation_score
        + DEFAULT_SCORE_WEIGHTS["survival"] * survival_score
        + DEFAULT_SCORE_WEIGHTS["function_retention"] * function_retention_rate
        + DEFAULT_SCORE_WEIGHTS["lineage_depth"] * normalized_depth
    )
    return _round_score(score)


def _metrics_from_chain(
    source: str,
    *,
    environment: str | None,
    runs: int,
    seed: int | None,
    retention: float,
    lineage_depth: int,
    max_lineage_depth: int,
) -> tuple[ProtoGeneMetrics, tuple[str, ...], tuple[str, ...], float, float, str]:
    evaluation = evaluate_chain(source, environment=environment)
    simulation = simulate_chain(source, environment=environment, runs=runs, seed=seed)
    covered = _minimal_from_chain_genes(evaluation.predicted_functions)
    missing = _missing_minimal(covered)

    template_score = evaluation.properties["template"]
    copyability_score = _round_score(0.55 * evaluation.function_scores["POL"] + 0.45 * template_score)
    separation_score = evaluation.properties["separation"]
    survival_score = _round_score(0.55 * evaluation.properties["stability"] + 0.45 * simulation.survival_rate)
    proto_gene_score = _score_aggregate(
        template_score=template_score,
        copyability_score=copyability_score,
        separation_score=separation_score,
        survival_score=survival_score,
        function_retention_rate=retention,
        lineage_depth=lineage_depth,
        max_lineage_depth=max_lineage_depth,
    )
    return (
        ProtoGeneMetrics(
            template_score=_round_score(template_score),
            copyability_score=copyability_score,
            separation_score=_round_score(separation_score),
            survival_score=survival_score,
            function_retention_rate=_round_score(retention),
            lineage_depth=lineage_depth,
            proto_gene_score=proto_gene_score,
        ),
        covered,
        missing,
        simulation.survival_rate,
        evaluation.viability_score,
        evaluation.viability,
    )


def _metrics_from_rdkit(
    source: str,
    *,
    retention: float,
    lineage_depth: int,
    max_lineage_depth: int,
) -> tuple[
    ProtoGeneMetrics,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, float],
    float,
    str,
    bool,
    str | None,
]:
    evaluation = evaluate_rdkit_molecule(source)
    graph = build_symbolic_graph(evaluation)
    gene_hits = detect_proto_genes(evaluation)
    genome = evaluate_proto_genome(gene_hits, evaluation)
    detected_genes = tuple(hit.gene_id for hit in gene_hits if hit.present)
    reaction_ids = _reaction_ids_for(evaluation, graph)
    properties = graph.graph_properties
    tags = set(graph.topology_tags)

    si_template = float(evaluation.motifs.get("Si-O-Si", 0))
    backbone = properties.get("backbone_length", 0.0)
    network_score = properties.get("network_score", 0.0)
    fragment_count = properties.get("fragment_count", 0.0)
    ring_count = properties.get("ring_count", 0.0)
    terminals = _terminal_count(graph)

    template_score = _round_score(
        0.28 * min(1.0, si_template / 3)
        + 0.24 * min(1.0, backbone / 7)
        + 0.24 * network_score
        + 0.24 * (1.0 if "GENE_SI_TEMPLATE" in detected_genes else 0.0)
    )
    copyability_score = _round_score(
        0.30 * ("TEMPLATE" in genome.covered_functions)
        + 0.30 * ("POLYMERIZE" in genome.covered_functions)
        + 0.20 * (1.0 if "GENE_SI_TEMPLATE" in detected_genes else 0.0)
        + 0.20 * ("RXN_SIO_GROWTH" in reaction_ids or "RXN_FRAGMENT_REJOIN" in reaction_ids)
    )
    separation_score = _round_score(
        0.30 * ("SEPARATE" in genome.covered_functions)
        + 0.22 * (1.0 if "GENE_LABILE_SEPARATION" in detected_genes else 0.0)
        + 0.18 * min(1.0, max(0.0, fragment_count - 1))
        + 0.15 * min(1.0, terminals / 4)
        + 0.15 * ("RXN_LABILE_BREAK" in reaction_ids)
    )
    survival_score = _round_score(
        0.28 * ("PROTECT" in genome.covered_functions)
        + 0.24 * (1.0 if "GENE_SILOXANE_SHELL" in detected_genes else 0.0)
        + 0.24 * network_score
        + 0.14 * min(1.0, ring_count)
        + 0.10 * ("network" in tags or "ring" in tags)
    )
    proto_gene_score = _score_aggregate(
        template_score=template_score,
        copyability_score=copyability_score,
        separation_score=separation_score,
        survival_score=survival_score,
        function_retention_rate=retention,
        lineage_depth=lineage_depth,
        max_lineage_depth=max_lineage_depth,
    )

    return (
        ProtoGeneMetrics(
            template_score=template_score,
            copyability_score=copyability_score,
            separation_score=separation_score,
            survival_score=survival_score,
            function_retention_rate=_round_score(retention),
            lineage_depth=lineage_depth,
            proto_gene_score=proto_gene_score,
        ),
        genome.covered_functions,
        genome.missing_functions,
        detected_genes,
        graph.topology_tags,
        dict(properties),
        genome.genome_score,
        "minimal_proto_genome_candidate" if genome.minimal_viable else "partial_proto_genome_candidate",
        evaluation.molecular_validity,
        evaluation.parse_error,
    )


def chain_candidate(
    chain: str | Iterable[str],
    *,
    candidate_id: str,
    parent_id: str | None = None,
    generation: int = 0,
    environment: str | None = None,
    runs: int = 10,
    seed: int | None = None,
    retention: float = 1.0,
    lineage_depth: int = 0,
    max_lineage_depth: int = 10,
) -> ProtoGeneCandidate:
    motif = "-".join(parse_chain(chain))
    metrics, covered, missing, genome_score, viability_score, viability = _metrics_from_chain(
        motif,
        environment=environment,
        runs=runs,
        seed=seed,
        retention=retention,
        lineage_depth=lineage_depth,
        max_lineage_depth=max_lineage_depth,
    )
    return ProtoGeneCandidate(
        candidate_id=candidate_id,
        parent_id=parent_id,
        mode="chain",
        source=motif,
        motif=motif,
        generation=generation,
        molecular_validity=True,
        parse_error=None,
        environment=environment,
        topology_tags=("symbolic_chain",),
        covered_functions=covered,
        missing_functions=missing,
        detected_genes=tuple(),
        genome_score=genome_score,
        viability_score=viability_score,
        viability=viability,
        graph_properties={},
        reaction_ids=tuple(),
        metrics=metrics,
    )


def rdkit_candidate(
    molecule: str,
    *,
    candidate_id: str,
    parent_id: str | None = None,
    generation: int = 0,
    environment: str | None = None,
    retention: float = 1.0,
    lineage_depth: int = 0,
    max_lineage_depth: int = 10,
) -> ProtoGeneCandidate:
    (
        metrics,
        covered,
        missing,
        detected_genes,
        topology_tags,
        graph_properties,
        genome_score,
        viability,
        molecular_validity,
        parse_error,
    ) = _metrics_from_rdkit(
        molecule,
        retention=retention,
        lineage_depth=lineage_depth,
        max_lineage_depth=max_lineage_depth,
    )
    return ProtoGeneCandidate(
        candidate_id=candidate_id,
        parent_id=parent_id,
        mode="rdkit",
        source=molecule,
        motif=molecule,
        generation=generation,
        molecular_validity=molecular_validity,
        parse_error=parse_error,
        environment=environment,
        topology_tags=topology_tags,
        covered_functions=covered,
        missing_functions=missing,
        detected_genes=detected_genes,
        genome_score=genome_score,
        viability_score=genome_score,
        viability=viability if molecular_validity else "invalid_or_unusable",
        graph_properties=graph_properties,
        reaction_ids=tuple(),
        metrics=metrics,
    )


def _retention(parent: ProtoGeneCandidate, child_functions: tuple[str, ...]) -> tuple[float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    parent_functions = set(parent.covered_functions)
    child_set = set(child_functions)
    if not parent_functions:
        rate = 0.0
    else:
        rate = len(parent_functions & child_set) / len(parent_functions)
    retained = tuple(function for function in MINIMAL_FUNCTIONS if function in parent_functions & child_set)
    lost = tuple(function for function in MINIMAL_FUNCTIONS if function in parent_functions - child_set)
    new = tuple(function for function in MINIMAL_FUNCTIONS if function in child_set - parent_functions)
    return _round_score(rate), retained, lost, new


def _events(parent: ProtoGeneCandidate, child: ProtoGeneCandidate, retained: tuple[str, ...], lost: tuple[str, ...], new: tuple[str, ...]) -> tuple[str, ...]:
    events = ["copy_attempt"]
    if child.metrics.copyability_score >= parent.metrics.copyability_score:
        events.append("template_extension")
    if child.metrics.separation_score >= 0.35:
        events.append("labile_separation")
    if child.molecular_validity and child.covered_functions:
        events.append("fragment_retained")
    if retained:
        events.append("function_retained")
    if lost:
        events.append("function_loss")
    if new:
        events.append("function_gain")
    return tuple(events)


def _is_viable(candidate: ProtoGeneCandidate, threshold: float) -> bool:
    metrics = candidate.metrics
    return (
        candidate.molecular_validity
        and bool(candidate.covered_functions)
        and metrics.template_score > 0.0
        and metrics.copyability_score > 0.0
        and metrics.separation_score > 0.0
        and metrics.survival_score > 0.0
        and metrics.function_retention_rate >= threshold
    )


def _rank_key(candidate: ProtoGeneCandidate) -> tuple[float, float, int, float]:
    return (
        candidate.metrics.proto_gene_score,
        candidate.metrics.function_retention_rate,
        candidate.metrics.lineage_depth,
        max(candidate.genome_score, candidate.viability_score),
    )


def _child_source(parent: ProtoGeneCandidate, rng: random.Random, index: int) -> str:
    if index % 2 == 0:
        return parent.source
    if parent.mode == "chain":
        mutated = mutate_chain(parse_chain(parent.source), rng)
        return "-".join(mutated)
    molecule, _operator = mutate_molecule(parent.source, rng)
    if index % 3 == 0 and "RXN_LABILE_BREAK" in parent.reaction_ids:
        return molecule + ".[Si]O"
    return molecule


def _with_reactions(candidate: ProtoGeneCandidate) -> ProtoGeneCandidate:
    if candidate.mode != "rdkit" or not candidate.molecular_validity:
        return candidate
    evaluation = evaluate_rdkit_molecule(candidate.source)
    graph = build_symbolic_graph(evaluation)
    return replace(candidate, reaction_ids=_reaction_ids_for(evaluation, graph))


def _make_child(
    parent: ProtoGeneCandidate,
    *,
    child_id: str,
    generation: int,
    rng: random.Random,
    child_index: int,
    config: ProtoGeneLineageConfig,
) -> tuple[ProtoGeneCandidate, LineageNode]:
    source = _child_source(parent, rng, child_index)
    provisional = (
        chain_candidate(
            source,
            candidate_id=child_id,
            parent_id=parent.candidate_id,
            generation=generation,
            environment=config.environment,
            runs=config.runs,
            seed=rng.randrange(0, 2**32),
            max_lineage_depth=config.max_lineage_depth,
        )
        if parent.mode == "chain"
        else rdkit_candidate(
            source,
            candidate_id=child_id,
            parent_id=parent.candidate_id,
            generation=generation,
            environment=config.environment,
            max_lineage_depth=config.max_lineage_depth,
        )
    )
    provisional = _with_reactions(provisional)
    retention, retained, lost, new = _retention(parent, provisional.covered_functions)
    depth = parent.metrics.lineage_depth + 1 if retention >= config.retention_threshold else 0
    child = (
        chain_candidate(
            source,
            candidate_id=child_id,
            parent_id=parent.candidate_id,
            generation=generation,
            environment=config.environment,
            runs=config.runs,
            seed=rng.randrange(0, 2**32),
            retention=retention,
            lineage_depth=depth,
            max_lineage_depth=config.max_lineage_depth,
        )
        if parent.mode == "chain"
        else rdkit_candidate(
            source,
            candidate_id=child_id,
            parent_id=parent.candidate_id,
            generation=generation,
            environment=config.environment,
            retention=retention,
            lineage_depth=depth,
            max_lineage_depth=config.max_lineage_depth,
        )
    )
    child = _with_reactions(child)
    extinct = not _is_viable(child, config.retention_threshold)
    node = LineageNode(
        candidate_id=child.candidate_id,
        parent_id=parent.candidate_id,
        generation=generation,
        mode=child.mode,
        motif=child.motif,
        event_labels=_events(parent, child, retained, lost, new),
        retained_functions=retained,
        lost_functions=lost,
        new_functions=new,
        function_retention_rate=retention,
        lineage_depth=depth,
        parent_score=parent.metrics.proto_gene_score,
        proto_gene_score=child.metrics.proto_gene_score,
        score_delta=round(child.metrics.proto_gene_score - parent.metrics.proto_gene_score, 3),
        extinct=extinct,
    )
    return child, node


def _initial_chain_population(config: ProtoGeneLineageConfig) -> list[ProtoGeneCandidate]:
    if not config.seed_chain:
        raise ValueError("--seed-chain is required when mode=chain")
    results = search_chains(
        config.seed_chain,
        rounds=config.rounds,
        top_n=config.population_size,
        seed=config.seed,
        environment=config.environment,
    )
    return [
        chain_candidate(
            result.evaluation.chain,
            candidate_id=f"g0_c{index}",
            generation=0,
            environment=config.environment,
            runs=config.runs,
            seed=(None if config.seed is None else config.seed + index),
            max_lineage_depth=config.max_lineage_depth,
        )
        for index, result in enumerate(results, start=1)
    ]


def _initial_rdkit_population(config: ProtoGeneLineageConfig) -> list[ProtoGeneCandidate]:
    if not config.input_path:
        raise ValueError("input path is required when mode=rdkit")
    rows = parse_candidate_file(config.input_path)
    return [
        _with_reactions(
            rdkit_candidate(
                molecule,
                candidate_id=f"g0_c{index}",
                generation=0,
                environment=config.environment,
                max_lineage_depth=config.max_lineage_depth,
            )
        )
        for index, (molecule, _name) in enumerate(rows[: config.population_size], start=1)
    ]


def run_proto_gene_lineage_search(config: ProtoGeneLineageConfig) -> ProtoGeneLineageRun:
    if config.mode not in {"chain", "rdkit"}:
        raise ValueError("mode must be 'chain' or 'rdkit'")
    if config.generations <= 0:
        raise ValueError("generations must be positive")
    if config.population_size <= 0:
        raise ValueError("population_size must be positive")
    validate_environment(config.environment)

    rng = random.Random(config.seed)
    population = _initial_chain_population(config) if config.mode == "chain" else _initial_rdkit_population(config)
    population.sort(key=_rank_key, reverse=True)
    population = population[: config.population_size]
    history: list[LineageNode] = []

    for generation in range(1, config.generations + 1):
        next_population: list[ProtoGeneCandidate] = []
        for index in range(config.population_size):
            parent = population[index % len(population)]
            child, node = _make_child(
                parent,
                child_id=f"g{generation}_c{index + 1}",
                generation=generation,
                rng=rng,
                child_index=index + 1,
                config=config,
            )
            history.append(node)
            if not node.extinct:
                next_population.append(child)

        if not next_population:
            population = []
            break

        next_population.sort(key=_rank_key, reverse=True)
        population = next_population[: config.population_size]

    ranked = sorted(population, key=_rank_key, reverse=True)
    best = ranked[0] if ranked else None
    summary = _summary(config, ranked, history, best)
    return ProtoGeneLineageRun(
        config=config,
        ranked_candidates=ranked,
        lineage_history=history,
        best_candidate=best,
        summary=summary,
    )


def _summary(
    config: ProtoGeneLineageConfig,
    ranked: list[ProtoGeneCandidate],
    history: list[LineageNode],
    best: ProtoGeneCandidate | None,
) -> dict[str, object]:
    viable_steps = [node for node in history if not node.extinct]
    avg_retention = sum(node.function_retention_rate for node in history) / len(history) if history else 0.0
    return {
        "config": asdict(config),
        "score_weights": DEFAULT_SCORE_WEIGHTS,
        "retention_threshold": config.retention_threshold,
        "candidate_count": len(ranked),
        "lineage_steps": len(history),
        "viable_lineage_steps": len(viable_steps),
        "avg_function_retention_rate": round(avg_retention, 3),
        "best_candidate_id": best.candidate_id if best else None,
        "best_proto_gene_score": best.metrics.proto_gene_score if best else 0.0,
        "best_lineage_depth": best.metrics.lineage_depth if best else 0,
        "extinct": not bool(ranked),
        "safety": SAFETY_DISCLAIMER,
    }


def _join(values: Iterable[str]) -> str:
    return ";".join(values)


def candidate_row(candidate: ProtoGeneCandidate) -> dict[str, str]:
    return {
        "candidate_id": candidate.candidate_id,
        "parent_id": candidate.parent_id or "",
        "mode": candidate.mode,
        "source": candidate.source,
        "motif": candidate.motif,
        "generation": str(candidate.generation),
        "molecular_validity": str(candidate.molecular_validity).lower(),
        "parse_error": candidate.parse_error or "",
        "environment": candidate.environment or "none",
        "topology_tags": _join(candidate.topology_tags),
        "covered_functions": _join(candidate.covered_functions),
        "missing_functions": _join(candidate.missing_functions),
        "detected_genes": _join(candidate.detected_genes),
        "genome_score": f"{candidate.genome_score:.3f}",
        "viability_score": f"{candidate.viability_score:.3f}",
        "viability": candidate.viability,
        "template_score": f"{candidate.metrics.template_score:.3f}",
        "copyability_score": f"{candidate.metrics.copyability_score:.3f}",
        "separation_score": f"{candidate.metrics.separation_score:.3f}",
        "survival_score": f"{candidate.metrics.survival_score:.3f}",
        "function_retention_rate": f"{candidate.metrics.function_retention_rate:.3f}",
        "lineage_depth": str(candidate.metrics.lineage_depth),
        "proto_gene_score": f"{candidate.metrics.proto_gene_score:.3f}",
        "reaction_ids": _join(candidate.reaction_ids),
    }


def lineage_row(node: LineageNode) -> dict[str, str]:
    return {
        "candidate_id": node.candidate_id,
        "parent_id": node.parent_id or "",
        "generation": str(node.generation),
        "mode": node.mode,
        "motif": node.motif,
        "event_labels": _join(node.event_labels),
        "retained_functions": _join(node.retained_functions),
        "lost_functions": _join(node.lost_functions),
        "new_functions": _join(node.new_functions),
        "function_retention_rate": f"{node.function_retention_rate:.3f}",
        "lineage_depth": str(node.lineage_depth),
        "parent_score": f"{node.parent_score:.3f}",
        "proto_gene_score": f"{node.proto_gene_score:.3f}",
        "score_delta": f"{node.score_delta:.3f}",
        "extinct": str(node.extinct).lower(),
    }


def write_proto_gene_outputs(run: ProtoGeneLineageRun, output_dir: str | Path) -> ProtoGeneOutputPaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = ProtoGeneOutputPaths(
        proto_gene_candidates_csv=directory / "proto_gene_candidates.csv",
        lineage_history_csv=directory / "lineage_history.csv",
        proto_gene_summary_json=directory / "proto_gene_summary.json",
        best_proto_gene_json=directory / "best_proto_gene.json",
        proto_gene_report_md=directory / "proto_gene_report.md",
    )

    candidate_rows = [candidate_row(candidate) for candidate in run.ranked_candidates]
    candidate_fields = list(candidate_row(_empty_candidate()).keys())
    with paths.proto_gene_candidates_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fields)
        writer.writeheader()
        writer.writerows(candidate_rows)

    lineage_rows = [lineage_row(node) for node in run.lineage_history]
    lineage_fields = list(lineage_row(_empty_lineage_node()).keys())
    with paths.lineage_history_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=lineage_fields)
        writer.writeheader()
        writer.writerows(lineage_rows)

    paths.proto_gene_summary_json.write_text(json.dumps(run.summary, indent=2, sort_keys=True), encoding="utf-8")
    best_payload = asdict(run.best_candidate) if run.best_candidate else {"best_candidate": None}
    paths.best_proto_gene_json.write_text(json.dumps(best_payload, indent=2, sort_keys=True), encoding="utf-8")
    paths.proto_gene_report_md.write_text(format_proto_gene_report(run), encoding="utf-8")
    return paths


def _empty_metrics() -> ProtoGeneMetrics:
    return ProtoGeneMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)


def _empty_candidate() -> ProtoGeneCandidate:
    return ProtoGeneCandidate(
        "",
        None,
        "",
        "",
        "",
        0,
        False,
        None,
        None,
        tuple(),
        tuple(),
        tuple(),
        tuple(),
        0.0,
        0.0,
        "",
        {},
        tuple(),
        _empty_metrics(),
    )


def _empty_lineage_node() -> LineageNode:
    return LineageNode("", None, 0, "", "", tuple(), tuple(), tuple(), tuple(), 0.0, 0, 0.0, 0.0, 0.0, True)


def format_proto_gene_report(run: ProtoGeneLineageRun) -> str:
    best = run.best_candidate
    lines = [
        "# Proto-Gene Lineage Report",
        "",
        "## Summary",
        "",
        f"- mode: {run.config.mode}",
        f"- candidates: {len(run.ranked_candidates)}",
        f"- lineage steps: {len(run.lineage_history)}",
        f"- extinct: {str(run.summary['extinct']).lower()}",
        "",
        "## Best Candidate",
        "",
    ]
    if best is None:
        lines.append("No candidate survived the lineage thresholds.")
    else:
        lines.extend(
            [
                f"- candidate_id: {best.candidate_id}",
                f"- motif: `{best.motif}`",
                f"- proto_gene_score: {best.metrics.proto_gene_score:.3f}",
                f"- lineage_depth: {best.metrics.lineage_depth}",
                f"- covered_functions: {_join(best.covered_functions) or 'none'}",
                f"- missing_functions: {_join(best.missing_functions) or 'none'}",
                f"- topology_tags: {_join(best.topology_tags) or 'none'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `proto_gene_candidates.csv`: ranked final candidates and metrics.",
            "- `lineage_history.csv`: parent/child transitions and function retention.",
            "- `proto_gene_summary.json`: run configuration, thresholds, and aggregate metrics.",
            "- `best_proto_gene.json`: machine-readable best candidate.",
            "",
            "## Known Limitations",
            "",
            "- Heuristic graph/motif model, not kinetic, thermodynamic, quantum, or laboratory validation.",
            "- RDKit parsing is a convenience layer and may reject useful symbolic motifs.",
            "- Lineage events are computational abstractions, not real synthesis routes.",
            "- `proto_gene_score` is a ranking heuristic, not evidence of life or experimental feasibility.",
            "- Environments are symbolic modifiers, not physical operating conditions.",
            "",
            "## Safety and Scope",
            "",
            SAFETY_DISCLAIMER,
        ]
    )
    return "\n".join(lines) + "\n"


def format_proto_gene_summary(run: ProtoGeneLineageRun) -> str:
    if run.best_candidate is None:
        return "proto-gene lineage search\n\nresult: extinction\n"
    best = run.best_candidate
    return "\n".join(
        [
            "proto-gene lineage search",
            "",
            f"mode: {run.config.mode}",
            f"best_candidate: {best.candidate_id}",
            f"best_proto_gene_score: {best.metrics.proto_gene_score:.3f}",
            f"lineage_depth: {best.metrics.lineage_depth}",
            f"covered_functions: {_join(best.covered_functions) or 'none'}",
            f"missing_functions: {_join(best.missing_functions) or 'none'}",
            f"candidates: {len(run.ranked_candidates)}",
            f"lineage_steps: {len(run.lineage_history)}",
        ]
    )


def run_and_write_proto_gene_lineage_search(config: ProtoGeneLineageConfig, output_dir: str | Path) -> tuple[ProtoGeneLineageRun, ProtoGeneOutputPaths]:
    try:
        run = run_proto_gene_lineage_search(config)
    except RDKitUnavailableError:
        raise
    paths = write_proto_gene_outputs(run, output_dir)
    return run, paths
