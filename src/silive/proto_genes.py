from __future__ import annotations

from dataclasses import dataclass

from .rdkit_chemistry import MOTIF_NAMES, RDKitEvaluation, format_rdkit_scorecard

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


def _elements_for_ring(evaluation: RDKitEvaluation, ring: tuple[int, ...]) -> tuple[str, ...]:
    by_index = {atom.index: atom.symbol for atom in evaluation.atoms}
    return tuple(by_index[index] for index in ring if index in by_index)


def _si_o_bond_count(evaluation: RDKitEvaluation) -> int:
    count = 0
    for bond in evaluation.bonds:
        pair = {bond.begin_symbol, bond.end_symbol}
        if pair == {"Si", "O"}:
            count += 1
    return count


def _terminal_atom_count(evaluation: RDKitEvaluation) -> int:
    return sum(1 for atom in evaluation.atoms if atom.degree <= 1)


def _si_o_ring_count(evaluation: RDKitEvaluation) -> int:
    count = 0
    for ring in evaluation.rings:
        elements = _elements_for_ring(evaluation, ring)
        if elements and set(elements) <= {"Si", "O"} and "Si" in elements and "O" in elements:
            count += 1
    return count


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


def detect_proto_genes(evaluation: RDKitEvaluation) -> list[ProtoGeneHit]:
    """Detect experimental chemical proto-genes from an RDKit evaluation."""

    if not evaluation.molecular_validity:
        return [
            _hit(
                "GENE_SI_TEMPLATE",
                "siloxane template",
                False,
                0.0,
                tuple(),
                {"template": 0.0, "stability": 0.0},
                ("POL", "SHELL"),
            ),
            _hit("GENE_FE_CATALYSIS", "iron oxide catalysis", False, 0.0, tuple(), {"catalysis": 0.0}, ("CAT",)),
            _hit("GENE_NI_CATALYSIS", "nickel oxide catalysis", False, 0.0, tuple(), {"catalysis": 0.0}, ("CAT",)),
            _hit("GENE_P_REPAIR", "phosphate repair bridge", False, 0.0, tuple(), {"repair": 0.0, "template": 0.0}, ("REPAIR",)),
            _hit("GENE_SILOXANE_SHELL", "siloxane shell network", False, 0.0, tuple(), {"stability": 0.0}, ("SHELL",)),
            _hit("GENE_LABILE_SEPARATION", "labile separation handle", False, 0.0, tuple(), {"separation": 0.0}, ("SEP",)),
        ]

    si_template = _motif_count(evaluation, "Si-O-Si")
    fe_o = _motif_count(evaluation, "Fe-O")
    ni_o = _motif_count(evaluation, "Ni-O")
    p_o = _motif_count(evaluation, "P-O")
    sio_bonds = _si_o_bond_count(evaluation)
    sio_rings = _si_o_ring_count(evaluation)
    terminal_atoms = _terminal_atom_count(evaluation)
    fragment_count = len(evaluation.fragments)
    si_count = evaluation.elements.count("Si")
    o_count = evaluation.elements.count("O")

    dense_sio_network = si_count >= 2 and o_count >= 2 and sio_bonds >= 4
    labile_evidence = []
    if fragment_count > 1:
        labile_evidence.append(f"{fragment_count} separated fragments")
    if terminal_atoms >= 2:
        labile_evidence.append(f"{terminal_atoms} terminal atoms")
    if fe_o or ni_o or p_o:
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
            sio_rings > 0 or dense_sio_network,
            (sio_rings + sio_bonds / 6),
            tuple(filter(None, (f"Si/O rings: {sio_rings}" if sio_rings else "", f"Si-O bonds: {sio_bonds}"))),
            {"stability": 0.22 * max(1, sio_rings) + 0.04 * sio_bonds},
            ("SHELL",),
        ),
        _hit(
            "GENE_LABILE_SEPARATION",
            "labile separation handle",
            bool(labile_evidence),
            (terminal_atoms / 6) + (fragment_count - 1) * 0.25,
            tuple(labile_evidence),
            {"separation": 0.12 * terminal_atoms + 0.20 * max(0, fragment_count - 1)},
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
