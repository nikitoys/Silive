from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .proto_genes import ProtoGeneHit, detect_proto_genes
from .proto_genome import ProtoGenomeEvaluation, evaluate_proto_genome
from .rdkit_chemistry import RDKitEvaluation, evaluate_rdkit_molecule
from .symbolic_graph import SymbolicGraph, build_symbolic_graph

CRITICAL_FUNCTIONS = ("TEMPLATE", "CATALYZE", "PROTECT")


@dataclass(frozen=True, slots=True)
class RDKitCandidate:
    name: str
    molecule: str
    rdkit_evaluation: RDKitEvaluation
    symbolic_graph: SymbolicGraph
    gene_hits: list[ProtoGeneHit]
    genome_evaluation: ProtoGenomeEvaluation
    candidate_score: float
    viability: str


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


def classify_viability(candidate_score: float, genome_evaluation: ProtoGenomeEvaluation) -> str:
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
    return RDKitCandidate(
        name=name,
        molecule=molecule,
        rdkit_evaluation=rdkit_evaluation,
        symbolic_graph=symbolic_graph,
        gene_hits=gene_hits,
        genome_evaluation=genome_evaluation,
        candidate_score=candidate_score,
        viability=classify_viability(candidate_score, genome_evaluation),
    )


def search_rdkit_candidates(path: str | Path, *, top: int | None = None) -> list[RDKitCandidate]:
    candidates = [evaluate_candidate(molecule, name) for molecule, name in parse_candidate_file(path)]
    candidates.sort(key=lambda item: item.candidate_score, reverse=True)
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
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_rdkit_search_table(candidates: list[RDKitCandidate]) -> str:
    rows = candidate_rows(candidates)
    if not rows:
        return "rank name score validity covered missing genes topology viability"

    header = "rank | name | score | valid | covered | missing | genes | topology | viability"
    separator = "--- | --- | ---: | --- | --- | --- | --- | --- | ---"
    lines = [header, separator]
    for row in rows:
        lines.append(
            " | ".join(
                [
                    row["rank"],
                    row["name"],
                    row["score"],
                    row["molecular_validity"],
                    row["covered_functions"] or "none",
                    row["missing_functions"] or "none",
                    row["detected_genes"] or "none",
                    row["topology_tags"] or "none",
                    row["viability"],
                ]
            )
        )
    return "\n".join(lines)
