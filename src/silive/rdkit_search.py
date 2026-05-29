from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .proto_genes import ProtoGeneHit, detect_proto_genes
from .proto_genome import ProtoGenomeEvaluation, evaluate_proto_genome
from .rdkit_chemistry import RDKitEvaluation, evaluate_rdkit_molecule
from .symbolic_genome import score_symbolic_viability, symbolic_genome_from_molecule
from .symbolic_graph import SymbolicGraph, build_symbolic_graph

CRITICAL_FUNCTIONS = ("TEMPLATE", "CATALYZE", "PROTECT")
SYMBOLIC_PRESERVATION_THRESHOLD = 0.25


@dataclass(frozen=True, slots=True)
class RDKitCandidate:
    name: str
    molecule: str
    rdkit_evaluation: RDKitEvaluation
    symbolic_graph: SymbolicGraph
    gene_hits: list[ProtoGeneHit]
    genome_evaluation: ProtoGenomeEvaluation
    rdkit_valid_score: float
    symbolic_viability_score: float
    candidate_score: float
    viability: str
    risk_flags: tuple[str, ...]
    preservation_reason: str


def parse_candidate_file(path: str | Path) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for line_number, raw_line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        molecule = parts[0]
        name = parts[1].strip() if len(parts) > 1 else f"candidate_{line_number}"
        candidates.append((molecule, name))
    return candidates


def _present_gene_ids(gene_hits: list[ProtoGeneHit]) -> set[str]:
    return {hit.gene_id for hit in gene_hits if hit.present}


def _combo_bonus(rdkit_evaluation: RDKitEvaluation, gene_hits: list[ProtoGeneHit]) -> float:
    genes = _present_gene_ids(gene_hits)
    motifs = rdkit_evaluation.motifs
    has_si_template = motifs.get("Si-O-Si", 0) > 0 or "GENE_SI_TEMPLATE" in genes
    has_metal = motifs.get("Fe-O", 0) > 0 or motifs.get("Ni-O", 0) > 0
    has_repair = motifs.get("P-O", 0) > 0 or "GENE_P_REPAIR" in genes
    bonus = 0.0
    if has_si_template and has_metal:
        bonus += 0.08
    if has_si_template and has_repair:
        bonus += 0.08
    if has_si_template and has_metal and has_repair:
        bonus += 0.12
    return bonus


def score_candidate(
    rdkit_evaluation: RDKitEvaluation,
    gene_hits: list[ProtoGeneHit],
    genome_evaluation: ProtoGenomeEvaluation,
) -> float:
    if not rdkit_evaluation.molecular_validity:
        return 0.0

    covered = set(genome_evaluation.covered_functions)
    missing = set(genome_evaluation.missing_functions)
    coverage_score = len(covered) / 6
    critical_present = sum(1 for function in CRITICAL_FUNCTIONS if function in covered) / len(CRITICAL_FUNCTIONS)
    missing_penalty = 0.08 * len(missing & set(CRITICAL_FUNCTIONS)) + 0.03 * len(missing - set(CRITICAL_FUNCTIONS))
    score = (
        0.48 * genome_evaluation.genome_score
        + 0.24 * coverage_score
        + 0.18 * critical_present
        + _combo_bonus(rdkit_evaluation, gene_hits)
        - missing_penalty
    )
    return round(max(0.0, min(1.0, score)), 3)


def rdkit_valid_score(rdkit_evaluation: RDKitEvaluation) -> float:
    return 1.0 if rdkit_evaluation.molecular_validity else 0.0


def symbolic_viability_score(molecule: str) -> float:
    return score_symbolic_viability(symbolic_genome_from_molecule(molecule))


def candidate_risk_flags(rdkit_evaluation: RDKitEvaluation, symbolic_score: float) -> tuple[str, ...]:
    flags: list[str] = []
    if not rdkit_evaluation.molecular_validity:
        flags.append("rdkit_invalid")
    if symbolic_score >= SYMBOLIC_PRESERVATION_THRESHOLD and not rdkit_evaluation.molecular_validity:
        flags.append("symbolic_only")
        flags.append("requires_chemical_validation")
    return tuple(flags)


def preservation_reason(rdkit_evaluation: RDKitEvaluation, symbolic_score: float) -> str:
    if rdkit_evaluation.molecular_validity:
        return "rdkit_validated"
    if symbolic_score >= SYMBOLIC_PRESERVATION_THRESHOLD:
        return "preserved_for_symbolic_motif_search"
    return "not_preserved_low_symbolic_score"


def classify_viability(
    candidate_score: float,
    genome_evaluation: ProtoGenomeEvaluation,
    rdkit_score: float,
    symbolic_score: float,
) -> str:
    if rdkit_score == 0.0 and symbolic_score >= SYMBOLIC_PRESERVATION_THRESHOLD:
        return "symbolic_only_invalid_candidate"
    if genome_evaluation.minimal_viable and candidate_score >= 0.80:
        return "minimal_proto_genome_candidate"
    if candidate_score >= 0.65:
        return "strong_incomplete_candidate"
    if candidate_score >= 0.40:
        return "partial_candidate"
    if candidate_score > 0.0:
        return "weak_candidate"
    return "invalid_or_unusable"


def evaluate_candidate(molecule: str, name: str) -> RDKitCandidate:
    rdkit_evaluation = evaluate_rdkit_molecule(molecule)
    symbolic_graph = build_symbolic_graph(rdkit_evaluation)
    gene_hits = detect_proto_genes(rdkit_evaluation)
    genome_evaluation = evaluate_proto_genome(gene_hits, rdkit_evaluation)
    candidate_score = score_candidate(rdkit_evaluation, gene_hits, genome_evaluation)
    rdkit_score = rdkit_valid_score(rdkit_evaluation)
    symbolic_score = symbolic_viability_score(molecule)
    return RDKitCandidate(
        name=name,
        molecule=molecule,
        rdkit_evaluation=rdkit_evaluation,
        symbolic_graph=symbolic_graph,
        gene_hits=gene_hits,
        genome_evaluation=genome_evaluation,
        rdkit_valid_score=rdkit_score,
        symbolic_viability_score=symbolic_score,
        candidate_score=candidate_score,
        viability=classify_viability(candidate_score, genome_evaluation, rdkit_score, symbolic_score),
        risk_flags=candidate_risk_flags(rdkit_evaluation, symbolic_score),
        preservation_reason=preservation_reason(rdkit_evaluation, symbolic_score),
    )


def search_rdkit_candidates(path: str | Path, *, top: int | None = None) -> list[RDKitCandidate]:
    candidates = [evaluate_candidate(molecule, name) for molecule, name in parse_candidate_file(path)]
    candidates.sort(key=lambda item: (item.candidate_score, item.symbolic_viability_score), reverse=True)
    if top is not None:
        return candidates[:top]
    return candidates


def _join(values: tuple[str, ...] | list[str]) -> str:
    return ";".join(values)


def _detected_genes(candidate: RDKitCandidate) -> list[str]:
    return [hit.gene_id for hit in candidate.gene_hits if hit.present]


def _prop(candidate: RDKitCandidate, key: str) -> str:
    return f"{candidate.symbolic_graph.graph_properties.get(key, 0.0):.3f}"


def candidate_rows(candidates: list[RDKitCandidate]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rank, candidate in enumerate(candidates, start=1):
        rows.append(
            {
                "rank": str(rank),
                "name": candidate.name,
                "molecule": candidate.molecule,
                "score": f"{candidate.candidate_score:.3f}",
                "rdkit_valid_score": f"{candidate.rdkit_valid_score:.3f}",
                "symbolic_viability_score": f"{candidate.symbolic_viability_score:.3f}",
                "molecular_validity": str(candidate.rdkit_evaluation.molecular_validity).lower(),
                "covered_functions": _join(candidate.genome_evaluation.covered_functions),
                "missing_functions": _join(candidate.genome_evaluation.missing_functions),
                "detected_genes": _join(_detected_genes(candidate)),
                "symbolic_chain": "-".join(candidate.rdkit_evaluation.symbolic_chain),
                "topology_tags": _join(candidate.symbolic_graph.topology_tags),
                "backbone_length": _prop(candidate, "backbone_length"),
                "ring_count": _prop(candidate, "ring_count"),
                "fragment_count": _prop(candidate, "fragment_count"),
                "network_score": _prop(candidate, "network_score"),
                "branching_score": _prop(candidate, "branching_score"),
                "viability": candidate.viability,
                "risk_flags": _join(candidate.risk_flags),
                "preservation_reason": candidate.preservation_reason,
            }
        )
    return rows


def write_rdkit_search_csv(candidates: list[RDKitCandidate], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = candidate_rows(candidates)
    fieldnames = [
        "rank",
        "name",
        "molecule",
        "score",
        "rdkit_valid_score",
        "symbolic_viability_score",
        "molecular_validity",
        "covered_functions",
        "missing_functions",
        "detected_genes",
        "symbolic_chain",
        "topology_tags",
        "backbone_length",
        "ring_count",
        "fragment_count",
        "network_score",
        "branching_score",
        "viability",
        "risk_flags",
        "preservation_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_rdkit_search_table(candidates: list[RDKitCandidate]) -> str:
    rows = candidate_rows(candidates)
    if not rows:
        return (
            "rank name score rdkit_valid symbolic_viability validity covered "
            "missing genes topology viability risks preservation"
        )

    header = (
        "rank | name | score | rdkit_valid | symbolic_viability | valid | covered | "
        "missing | genes | topology | viability | risks | preservation"
    )
    separator = "--- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | ---"
    lines = [header, separator]
    for row in rows:
        lines.append(
            " | ".join(
                [
                    row["rank"],
                    row["name"],
                    row["score"],
                    row["rdkit_valid_score"],
                    row["symbolic_viability_score"],
                    row["molecular_validity"],
                    row["covered_functions"] or "none",
                    row["missing_functions"] or "none",
                    row["detected_genes"] or "none",
                    row["topology_tags"] or "none",
                    row["viability"],
                    row["risk_flags"] or "none",
                    row["preservation_reason"],
                ]
            )
        )
    return "\n".join(lines)
