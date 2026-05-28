from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .proto_genes import detect_proto_genes
from .proto_genome import MINIMAL_FUNCTIONS, evaluate_proto_genome
from .rdkit_chemistry import RDKitEvaluation, evaluate_rdkit_molecule
from .rdkit_search import parse_candidate_file
from .symbolic_graph import SymbolicGraph, build_symbolic_graph


@dataclass(frozen=True, slots=True)
class ReactionRule:
    rule_id: str
    name: str
    description: str
    required_tags: tuple[str, ...]
    adds_motifs: dict[str, int]
    removes_motifs: dict[str, int]
    property_delta: dict[str, float]
    function_delta: dict[str, float]
    risk_delta: dict[str, float]


@dataclass(frozen=True, slots=True)
class ReactionResult:
    source_molecule: str
    reaction_id: str
    reaction_name: str
    product_symbolic_description: str
    changed_motifs: dict[str, int]
    before_score: float
    after_score: float
    delta_score: float
    new_functions: tuple[str, ...]
    lost_functions: tuple[str, ...]
    risks: tuple[str, ...]
    notes: tuple[str, ...]


REACTION_RULES: tuple[ReactionRule, ...] = (
    ReactionRule(
        "RXN_SIO_GROWTH",
        "Si-O backbone growth",
        "Abstractly extend the siloxane backbone by one Si-O unit.",
        tuple(),
        {"Si-O": 1, "Si-O-Si": 1},
        {},
        {"backbone_length": 2.0, "network_score": 0.08},
        {"TEMPLATE": 0.10, "POLYMERIZE": 0.22, "PROTECT": 0.05},
        {"overgrowth": 0.05},
    ),
    ReactionRule(
        "RXN_SIO_BRANCH",
        "Si-O network branching",
        "Abstractly branch a Si-O scaffold into a denser network.",
        ("siloxane_rich",),
        {"Si-O": 2},
        {},
        {"branching_score": 0.15, "network_score": 0.22},
        {"POLYMERIZE": 0.12, "PROTECT": 0.25},
        {"gelation": 0.10, "template_loss": 0.05},
    ),
    ReactionRule(
        "RXN_FE_CENTER_ADD",
        "Fe-O catalytic center addition",
        "Abstractly add an iron-oxide catalytic center to the scaffold.",
        tuple(),
        {"Fe-O": 1},
        {},
        {"metal_o_bond_count": 1.0},
        {"CATALYZE": 0.30},
        {"oxidative_damage": 0.08},
    ),
    ReactionRule(
        "RXN_NI_CENTER_ADD",
        "Ni-O catalytic center addition",
        "Abstractly add a nickel-oxide catalytic center to the scaffold.",
        tuple(),
        {"Ni-O": 1},
        {},
        {"metal_o_bond_count": 1.0},
        {"CATALYZE": 0.26},
        {"metal_poisoning": 0.06},
    ),
    ReactionRule(
        "RXN_P_REPAIR_BRIDGE",
        "P-O repair bridge addition",
        "Abstractly add a phosphate-like bridge for defect stabilization.",
        tuple(),
        {"P-O": 2},
        {},
        {"p_o_bond_count": 2.0, "network_score": 0.05},
        {"REPAIR": 0.32, "TEMPLATE": 0.08},
        {"hydrolysis_lability": 0.08},
    ),
    ReactionRule(
        "RXN_LABILE_BREAK",
        "Labile bridge break / separation",
        "Abstractly split a weak bridge to model copy or fragment separation.",
        tuple(),
        {},
        {"Si-O": 1},
        {"fragment_count": 1.0, "network_score": -0.08},
        {"SEPARATE": 0.35},
        {"fragment_loss": 0.12, "stability_loss": 0.10},
    ),
    ReactionRule(
        "RXN_RING_CLOSURE",
        "Si/O ring closure",
        "Abstractly close a siloxane path into a protective ring.",
        ("siloxane_rich",),
        {"Si-O": 1},
        {},
        {"ring_count": 1.0, "network_score": 0.20},
        {"PROTECT": 0.28, "TEMPLATE": 0.05},
        {"rigidity": 0.07},
    ),
    ReactionRule(
        "RXN_FRAGMENT_REJOIN",
        "Fragment rejoin through Si-O bridge",
        "Abstractly reconnect separated fragments through a Si-O bridge.",
        ("fragmented",),
        {"Si-O": 1, "Si-O-Si": 1},
        {},
        {"fragment_count": -1.0, "network_score": 0.15, "backbone_length": 1.0},
        {"POLYMERIZE": 0.15, "PROTECT": 0.10},
        {"misligation": 0.08},
    ),
)


def _base_functions(evaluation: RDKitEvaluation) -> tuple[set[str], float]:
    gene_hits = detect_proto_genes(evaluation)
    genome = evaluate_proto_genome(gene_hits, evaluation)
    return set(genome.covered_functions), genome.genome_score


def _rule_allowed(rule: ReactionRule, graph: SymbolicGraph) -> bool:
    tags = set(graph.topology_tags)
    return all(tag in tags for tag in rule.required_tags)


def _predicted_functions(base_functions: set[str], rule: ReactionRule) -> set[str]:
    predicted = set(base_functions)
    for function, delta in rule.function_delta.items():
        if delta > 0.0:
            predicted.add(function)
    return predicted


def _risk_labels(rule: ReactionRule) -> tuple[str, ...]:
    return tuple(key for key, value in rule.risk_delta.items() if value > 0.0)


def _after_score(before_score: float, base_functions: set[str], rule: ReactionRule) -> float:
    predicted = _predicted_functions(base_functions, rule)
    coverage_gain = (len(predicted) - len(base_functions)) / len(MINIMAL_FUNCTIONS)
    function_gain = sum(max(0.0, value) for value in rule.function_delta.values()) / len(MINIMAL_FUNCTIONS)
    topology_gain = sum(value for value in rule.property_delta.values() if value > 0.0) * 0.04
    risk_penalty = sum(value for value in rule.risk_delta.values()) * 0.10
    score = before_score + 0.45 * coverage_gain + 0.35 * function_gain + topology_gain - risk_penalty
    return round(max(0.0, min(1.0, score)), 3)


def _changed_motifs(rule: ReactionRule) -> dict[str, int]:
    changed: dict[str, int] = {}
    for key, value in rule.adds_motifs.items():
        changed[key] = changed.get(key, 0) + value
    for key, value in rule.removes_motifs.items():
        changed[key] = changed.get(key, 0) - value
    return changed


def _product_description(evaluation: RDKitEvaluation, graph: SymbolicGraph, rule: ReactionRule) -> str:
    backbone = "-".join(evaluation.symbolic_chain) if evaluation.symbolic_chain else "graph"
    tags = ",".join(graph.topology_tags) if graph.topology_tags else "untagged"
    added = ",".join(f"+{key}:{value}" for key, value in rule.adds_motifs.items()) or "no_add"
    removed = ",".join(f"-{key}:{value}" for key, value in rule.removes_motifs.items()) or "no_remove"
    return f"{backbone} | topology={tags} | {rule.rule_id} | {added} | {removed}"


def _notes(rule: ReactionRule, graph: SymbolicGraph) -> tuple[str, ...]:
    notes = [rule.description]
    if rule.required_tags:
        notes.append("requires topology tags: " + ", ".join(rule.required_tags))
    if graph.main_backbone:
        notes.append(f"main backbone length: {len(graph.main_backbone)}")
    return tuple(notes)


def simulate_reactions(rdkit_evaluation: RDKitEvaluation, symbolic_graph: SymbolicGraph | None = None) -> list[ReactionResult]:
    graph = symbolic_graph or build_symbolic_graph(rdkit_evaluation)
    base_functions, before_score = _base_functions(rdkit_evaluation)
    results: list[ReactionResult] = []

    for rule in REACTION_RULES:
        if not _rule_allowed(rule, graph):
            continue
        predicted = _predicted_functions(base_functions, rule)
        after_score = _after_score(before_score, base_functions, rule)
        results.append(
            ReactionResult(
                source_molecule=rdkit_evaluation.source,
                reaction_id=rule.rule_id,
                reaction_name=rule.name,
                product_symbolic_description=_product_description(rdkit_evaluation, graph, rule),
                changed_motifs=_changed_motifs(rule),
                before_score=before_score,
                after_score=after_score,
                delta_score=round(after_score - before_score, 3),
                new_functions=tuple(function for function in MINIMAL_FUNCTIONS if function in predicted and function not in base_functions),
                lost_functions=tuple(function for function in MINIMAL_FUNCTIONS if function in base_functions and function not in predicted),
                risks=_risk_labels(rule),
                notes=_notes(rule, graph),
            )
        )

    results.sort(key=lambda item: item.delta_score, reverse=True)
    return results


def format_reaction_results(results: list[ReactionResult], *, top: int | None = None) -> str:
    visible = results[:top] if top is not None else results
    if not visible:
        return "reaction opportunities: none"

    lines = [f"source genome_score: {visible[0].before_score:.3f}", "", "reaction opportunities:"]
    for index, result in enumerate(visible, start=1):
        new_functions = ",".join(result.new_functions) if result.new_functions else "none"
        risks = ",".join(result.risks) if result.risks else "none"
        lines.extend(
            [
                f"{index}. {result.reaction_id} - {result.reaction_name}",
                f"   before_score: {result.before_score:.3f}",
                f"   after_score:  {result.after_score:.3f}",
                f"   delta_score:  {result.delta_score:+.3f}",
                f"   new_functions: {new_functions}",
                f"   risks: {risks}",
                f"   product: {result.product_symbolic_description}",
            ]
        )
    return "\n".join(lines)


def reaction_search(input_path: str | Path, *, top: int | None = None) -> list[tuple[str, str, ReactionResult]]:
    rows: list[tuple[str, str, ReactionResult]] = []
    for molecule, name in parse_candidate_file(input_path):
        evaluation = evaluate_rdkit_molecule(molecule)
        if not evaluation.molecular_validity:
            continue
        for result in simulate_reactions(evaluation):
            rows.append((name, molecule, result))
    rows.sort(key=lambda item: item[2].delta_score, reverse=True)
    if top is not None:
        return rows[:top]
    return rows


def write_reaction_search_csv(rows: list[tuple[str, str, ReactionResult]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "name",
        "molecule",
        "reaction_id",
        "reaction_name",
        "before_score",
        "after_score",
        "delta_score",
        "new_functions",
        "risks",
        "product_symbolic_description",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, (name, molecule, result) in enumerate(rows, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "name": name,
                    "molecule": molecule,
                    "reaction_id": result.reaction_id,
                    "reaction_name": result.reaction_name,
                    "before_score": f"{result.before_score:.3f}",
                    "after_score": f"{result.after_score:.3f}",
                    "delta_score": f"{result.delta_score:.3f}",
                    "new_functions": ";".join(result.new_functions),
                    "risks": ";".join(result.risks),
                    "product_symbolic_description": result.product_symbolic_description,
                }
            )


def format_reaction_search_table(rows: list[tuple[str, str, ReactionResult]]) -> str:
    if not rows:
        return "rank | name | reaction | delta | new_functions | risks"
    lines = ["rank | name | reaction | before | after | delta | new_functions | risks", "--- | --- | --- | ---: | ---: | ---: | --- | ---"]
    for rank, (name, _molecule, result) in enumerate(rows, start=1):
        lines.append(
            " | ".join(
                [
                    str(rank),
                    name,
                    result.reaction_id,
                    f"{result.before_score:.3f}",
                    f"{result.after_score:.3f}",
                    f"{result.delta_score:+.3f}",
                    ";".join(result.new_functions) or "none",
                    ";".join(result.risks) or "none",
                ]
            )
        )
    return "\n".join(lines)
