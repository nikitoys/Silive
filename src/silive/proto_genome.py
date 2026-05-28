from __future__ import annotations

from dataclasses import dataclass

from .proto_genes import ProtoGeneHit, detect_proto_genes, proto_gene_summary
from .rdkit_chemistry import RDKitEvaluation, format_rdkit_scorecard
from .symbolic_graph import build_symbolic_graph

MINIMAL_FUNCTIONS = ("TEMPLATE", "POLYMERIZE", "CATALYZE", "SEPARATE", "PROTECT", "REPAIR")


@dataclass(frozen=True, slots=True)
class ProtoGenomeEvaluation:
    covered_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    gene_hits: list[ProtoGeneHit]
    minimal_viable: bool
    bottlenecks: tuple[str, ...]
    recommendations: tuple[str, ...]
    genome_score: float


def _present(gene_hits: list[ProtoGeneHit], gene_id: str) -> bool:
    return any(hit.gene_id == gene_id and hit.present for hit in gene_hits)


def _hit_strength(gene_hits: list[ProtoGeneHit], gene_id: str) -> float:
    for hit in gene_hits:
        if hit.gene_id == gene_id and hit.present:
            return hit.strength
    return 0.0


def _graph_strengths(evaluation: RDKitEvaluation) -> dict[str, float]:
    graph = build_symbolic_graph(evaluation)
    properties = graph.graph_properties
    backbone_length = properties.get("backbone_length", 0.0)
    network_score = properties.get("network_score", 0.0)
    ring_count = properties.get("ring_count", 0.0)
    fragment_count = properties.get("fragment_count", 0.0)
    terminal_count = sum(1 for node in graph.nodes if "terminal" in node.tags)
    return {
        "polymerize": min(1.0, backbone_length / 7 + network_score * 0.45),
        "protect": min(1.0, network_score + ring_count * 0.25),
        "separate": min(1.0, terminal_count / 6 + max(0.0, fragment_count - 1) * 0.25),
    }


def _has_separation_handle(gene_hits: list[ProtoGeneHit], graph_strengths: dict[str, float]) -> bool:
    if _present(gene_hits, "GENE_LABILE_SEPARATION"):
        return True
    return graph_strengths["separate"] >= 0.25


def _cover_functions(gene_hits: list[ProtoGeneHit], evaluation: RDKitEvaluation) -> tuple[set[str], dict[str, float]]:
    covered: set[str] = set()
    strengths = {function: 0.0 for function in MINIMAL_FUNCTIONS}
    graph_strengths = _graph_strengths(evaluation)

    if _present(gene_hits, "GENE_SI_TEMPLATE"):
        covered.add("TEMPLATE")
        strengths["TEMPLATE"] = max(strengths["TEMPLATE"], _hit_strength(gene_hits, "GENE_SI_TEMPLATE"))

    if graph_strengths["polymerize"] >= 0.35:
        covered.add("POLYMERIZE")
        strengths["POLYMERIZE"] = graph_strengths["polymerize"]

    if _present(gene_hits, "GENE_FE_CATALYSIS") or _present(gene_hits, "GENE_NI_CATALYSIS"):
        covered.add("CATALYZE")
        strengths["CATALYZE"] = max(
            _hit_strength(gene_hits, "GENE_FE_CATALYSIS"),
            _hit_strength(gene_hits, "GENE_NI_CATALYSIS"),
        )

    if _present(gene_hits, "GENE_P_REPAIR"):
        covered.add("REPAIR")
        strengths["REPAIR"] = _hit_strength(gene_hits, "GENE_P_REPAIR")

    if _present(gene_hits, "GENE_SILOXANE_SHELL") or graph_strengths["protect"] >= 0.45:
        covered.add("PROTECT")
        strengths["PROTECT"] = max(_hit_strength(gene_hits, "GENE_SILOXANE_SHELL"), graph_strengths["protect"])

    if _has_separation_handle(gene_hits, graph_strengths):
        covered.add("SEPARATE")
        strengths["SEPARATE"] = max(0.25, _hit_strength(gene_hits, "GENE_LABILE_SEPARATION"), graph_strengths["separate"])

    return covered, strengths


def _recommendations(missing: tuple[str, ...]) -> tuple[str, ...]:
    recommendations: list[str] = []
    if "REPAIR" in missing:
        recommendations.append("add a P-O / phosphate-like repair bridge")
    if "CATALYZE" in missing:
        recommendations.append("add an Fe-O or Ni-O catalytic center")
    if "PROTECT" in missing:
        recommendations.append("add a Si-O ring or denser siloxane network")
    if "SEPARATE" in missing:
        recommendations.append("add a labile bridge or terminal separation handle")
    if "TEMPLATE" in missing:
        recommendations.append("add repeated Si-O-Si template motifs")
    if "POLYMERIZE" in missing:
        recommendations.append("extend the Si-O chain or connect it into a network")
    return tuple(recommendations)


def _bottlenecks(missing: tuple[str, ...], strengths: dict[str, float]) -> tuple[str, ...]:
    bottlenecks = list(missing)
    for function, strength in strengths.items():
        if function not in missing and strength < 0.34:
            bottlenecks.append(f"weak_{function}")
    return tuple(bottlenecks)


def _score(covered: set[str], strengths: dict[str, float], evaluation: RDKitEvaluation) -> float:
    if not evaluation.molecular_validity:
        return 0.0
    coverage_score = len(covered) / len(MINIMAL_FUNCTIONS)
    strength_score = sum(strengths.values()) / len(MINIMAL_FUNCTIONS)
    critical_bonus = 0.0
    if {"TEMPLATE", "POLYMERIZE", "CATALYZE"} <= covered:
        critical_bonus += 0.10
    if {"PROTECT", "SEPARATE", "REPAIR"} <= covered:
        critical_bonus += 0.10
    return round(min(1.0, 0.65 * coverage_score + 0.35 * strength_score + critical_bonus), 3)


def evaluate_proto_genome(gene_hits: list[ProtoGeneHit], rdkit_evaluation: RDKitEvaluation) -> ProtoGenomeEvaluation:
    covered_set, strengths = _cover_functions(gene_hits, rdkit_evaluation)
    covered = tuple(function for function in MINIMAL_FUNCTIONS if function in covered_set)
    missing = tuple(function for function in MINIMAL_FUNCTIONS if function not in covered_set)
    minimal_viable = not missing and rdkit_evaluation.molecular_validity
    return ProtoGenomeEvaluation(
        covered_functions=covered,
        missing_functions=missing,
        gene_hits=gene_hits,
        minimal_viable=minimal_viable,
        bottlenecks=_bottlenecks(missing, strengths),
        recommendations=_recommendations(missing),
        genome_score=_score(covered_set, strengths, rdkit_evaluation),
    )


def format_proto_genome_evaluation(evaluation: ProtoGenomeEvaluation) -> str:
    lines = [
        "minimal proto-genome coverage",
        "",
        "covered functions:",
        "  " + (", ".join(evaluation.covered_functions) if evaluation.covered_functions else "none"),
        "",
        "missing functions:",
        "  " + (", ".join(evaluation.missing_functions) if evaluation.missing_functions else "none"),
        "",
        f"minimal_viable: {str(evaluation.minimal_viable).lower()}",
        f"genome_score: {evaluation.genome_score:.3f}",
        "",
        "bottlenecks:",
        "  " + (", ".join(evaluation.bottlenecks) if evaluation.bottlenecks else "none"),
        "",
        "recommendations:",
    ]
    if evaluation.recommendations:
        lines.extend(f"  - {item}" for item in evaluation.recommendations)
    else:
        lines.append("  none")
    return "\n".join(lines)


def format_rdkit_genome_scorecard(rdkit_evaluation: RDKitEvaluation) -> str:
    gene_hits = detect_proto_genes(rdkit_evaluation)
    genome = evaluate_proto_genome(gene_hits, rdkit_evaluation)
    return (
        format_rdkit_scorecard(rdkit_evaluation)
        + "\n\n"
        + proto_gene_summary(gene_hits)
        + "\n\n"
        + format_proto_genome_evaluation(genome)
    )
