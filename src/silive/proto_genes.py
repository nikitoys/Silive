from __future__ import annotations

from dataclasses import dataclass

from .rdkit_chemistry import RDKitEvaluation, format_rdkit_scorecard
from .symbolic_graph import SymbolicGraph, build_symbolic_graph

REQUIRED_FUNCTIONS = ("POL", "SEP", "SHELL", "REPAIR", "CAT")


@dataclass(frozen=True, slots=True)
class ProtoGeneHit:
    gene_id: str
    name: str
    present: bool
    strength: float
    evidence: tuple[str, ...]
    properties_delta: dict[str, float]
    functions: tuple[str, ...]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _motif_count(evaluation: RDKitEvaluation, motif: str) -> int:
    return int(evaluation.motifs.get(motif, 0))


def _hit(
    gene_id: str,
    name: str,
    present: bool,
    strength: float,
    evidence: tuple[str, ...],
    properties_delta: dict[str, float],
    functions: tuple[str, ...],
) -> ProtoGeneHit:
    return ProtoGeneHit(
        gene_id=gene_id,
        name=name,
        present=present,
        strength=round(_clamp(strength), 3),
        evidence=evidence if present else tuple(),
        properties_delta=properties_delta if present else {key: 0.0 for key in properties_delta},
        functions=functions if present else tuple(),
    )


def _absent_hits() -> list[ProtoGeneHit]:
    return [
        _hit("GENE_SI_TEMPLATE", "siloxane template", False, 0.0, tuple(), {"template": 0.0, "stability": 0.0}, ("POL", "SHELL")),
        _hit("GENE_FE_CATALYSIS", "iron oxide catalysis", False, 0.0, tuple(), {"catalysis": 0.0}, ("CAT",)),
        _hit("GENE_NI_CATALYSIS", "nickel oxide catalysis", False, 0.0, tuple(), {"catalysis": 0.0}, ("CAT",)),
        _hit("GENE_P_REPAIR", "phosphate repair bridge", False, 0.0, tuple(), {"repair": 0.0, "template": 0.0}, ("REPAIR",)),
        _hit("GENE_SILOXANE_SHELL", "siloxane shell network", False, 0.0, tuple(), {"stability": 0.0}, ("SHELL",)),
        _hit("GENE_LABILE_SEPARATION", "labile separation handle", False, 0.0, tuple(), {"separation": 0.0}, ("SEP",)),
    ]


def _terminal_node_count(graph: SymbolicGraph) -> int:
    return sum(1 for node in graph.nodes if "terminal" in node.tags)


def detect_proto_genes(evaluation: RDKitEvaluation) -> list[ProtoGeneHit]:
    """Detect experimental chemical proto-genes from an RDKit evaluation."""

    if not evaluation.molecular_validity:
        return _absent_hits()

    graph = build_symbolic_graph(evaluation)
    properties = graph.graph_properties
    tags = set(graph.topology_tags)
    si_template = _motif_count(evaluation, "Si-O-Si")
    fe_o = _motif_count(evaluation, "Fe-O")
    ni_o = _motif_count(evaluation, "Ni-O")
    p_o = _motif_count(evaluation, "P-O")
    sio_bonds = int(properties.get("si_o_bond_count", 0.0))
    ring_count = int(properties.get("ring_count", 0.0))
    fragment_count = int(properties.get("fragment_count", 0.0))
    network_score = float(properties.get("network_score", 0.0))
    terminal_nodes = _terminal_node_count(graph)

    shell_present = "ring" in tags or "network" in tags or network_score >= 0.45
    labile_evidence = []
    if "fragmented" in tags or fragment_count > 1:
        labile_evidence.append(f"{fragment_count} separated fragments")
    if terminal_nodes >= 2:
        labile_evidence.append(f"{terminal_nodes} terminal nodes")
    if "metal_center" in tags or "phosphate_bridge" in tags:
        labile_evidence.append("hetero-oxide bridge candidates")

    return [
        _hit(
            "GENE_SI_TEMPLATE",
            "siloxane template",
            si_template > 0,
            si_template / 3,
            (f"Si-O-Si motifs: {si_template}",),
            {"template": 0.28 * si_template, "stability": 0.18 * si_template},
            ("POL", "SHELL"),
        ),
        _hit(
            "GENE_FE_CATALYSIS",
            "iron oxide catalysis",
            fe_o > 0,
            fe_o / 3,
            (f"Fe-O bonds: {fe_o}",),
            {"catalysis": 0.30 * fe_o},
            ("CAT",),
        ),
        _hit(
            "GENE_NI_CATALYSIS",
            "nickel oxide catalysis",
            ni_o > 0,
            ni_o / 3,
            (f"Ni-O bonds: {ni_o}",),
            {"catalysis": 0.26 * ni_o},
            ("CAT",),
        ),
        _hit(
            "GENE_P_REPAIR",
            "phosphate repair bridge",
            p_o > 0,
            p_o / 3,
            (f"P-O bonds: {p_o}",),
            {"repair": 0.30 * p_o, "template": 0.08 * p_o},
            ("REPAIR", "POL"),
        ),
        _hit(
            "GENE_SILOXANE_SHELL",
            "siloxane shell network",
            shell_present,
            network_score + ring_count * 0.25,
            tuple(filter(None, (f"topology={','.join(graph.topology_tags)}", f"Si-O bonds: {sio_bonds}", f"rings: {ring_count}" if ring_count else ""))),
            {"stability": 0.22 * max(1, ring_count) + 0.20 * network_score},
            ("SHELL",),
        ),
        _hit(
            "GENE_LABILE_SEPARATION",
            "labile separation handle",
            bool(labile_evidence),
            (terminal_nodes / 6) + (fragment_count - 1) * 0.25,
            tuple(labile_evidence),
            {"separation": 0.12 * terminal_nodes + 0.20 * max(0, fragment_count - 1)},
            ("SEP",),
        ),
    ]


def covered_functions(gene_hits: list[ProtoGeneHit]) -> tuple[str, ...]:
    covered: set[str] = set()
    for hit in gene_hits:
        if hit.present:
            covered.update(hit.functions)
    return tuple(function for function in REQUIRED_FUNCTIONS if function in covered)


def missing_functions(gene_hits: list[ProtoGeneHit]) -> tuple[str, ...]:
    covered = set(covered_functions(gene_hits))
    return tuple(function for function in REQUIRED_FUNCTIONS if function not in covered)


def proto_gene_summary(gene_hits: list[ProtoGeneHit]) -> str:
    detected = [hit for hit in gene_hits if hit.present]
    absent = [hit for hit in gene_hits if not hit.present]
    covered = covered_functions(gene_hits)
    missing = missing_functions(gene_hits)

    lines = ["proto-gene summary", "", "detected genes:"]
    if detected:
        for hit in detected:
            evidence = "; ".join(hit.evidence) if hit.evidence else "no evidence"
            deltas = ", ".join(f"{key}+={value:.2f}" for key, value in hit.properties_delta.items() if value)
            lines.append(f"  {hit.gene_id}: strength={hit.strength:.3f}; functions={','.join(hit.functions)}; {evidence}; {deltas}")
    else:
        lines.append("  none")

    lines.extend(["", "absent genes:"])
    if absent:
        for hit in absent:
            lines.append(f"  {hit.gene_id}: {hit.name}")
    else:
        lines.append("  none")

    lines.extend(["", "covered functions:", "  " + (", ".join(covered) if covered else "none")])
    lines.extend(["", "missing functions:", "  " + (", ".join(missing) if missing else "none")])
    return "\n".join(lines)


def format_rdkit_gene_scorecard(evaluation: RDKitEvaluation) -> str:
    hits = detect_proto_genes(evaluation)
    return format_rdkit_scorecard(evaluation) + "\n\n" + proto_gene_summary(hits)
