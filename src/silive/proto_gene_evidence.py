from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .proto_genes import ProtoGeneHit, detect_proto_genes
from .proto_genome import MINIMAL_FUNCTIONS, ProtoGenomeEvaluation, evaluate_proto_genome
from .rdkit_chemistry import RDKitEvaluation, evaluate_rdkit_molecule
from .rdkit_search import score_candidate
from .symbolic_genome import symbolic_genome_from_molecule, symbolic_genome_to_molecule
from .symbolic_graph import SymbolicGraph, build_symbolic_graph

MODEL_VERSION = "proto-gene-evidence-v0.1"

EVIDENCE_GRADES = ("NONE", "MOTIF_HIT", "FUNCTIONAL_CANDIDATE", "LINEAGE_RETAINED", "ROBUST_LEAD")
FEATURE_GROUPS = ("template", "catalysis", "repair", "protection", "separation")
FEATURE_TO_GENES = {
    "template": ("GENE_SI_TEMPLATE",),
    "catalysis": ("GENE_FE_CATALYSIS", "GENE_NI_CATALYSIS"),
    "repair": ("GENE_P_REPAIR",),
    "protection": ("GENE_SILOXANE_SHELL",),
    "separation": ("GENE_LABILE_SEPARATION",),
}
FEATURE_TO_FUNCTIONS = {
    "template": ("TEMPLATE", "POLYMERIZE"),
    "catalysis": ("CATALYZE",),
    "repair": ("REPAIR",),
    "protection": ("PROTECT",),
    "separation": ("SEPARATE",),
}


@dataclass(frozen=True, slots=True)
class EvidenceCorpusRow:
    candidate_id: str
    group: str
    molecule: str
    expected_present_genes: tuple[str, ...]
    expected_absent_genes: tuple[str, ...]
    expected_covered_functions: tuple[str, ...]
    expected_missing_functions: tuple[str, ...]
    expected_evidence_grade: str
    rationale: str


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    corpus_row: EvidenceCorpusRow
    rdkit_evaluation: RDKitEvaluation
    symbolic_graph: SymbolicGraph
    gene_hits: list[ProtoGeneHit]
    genome_evaluation: ProtoGenomeEvaluation
    proto_gene_score: float
    observed_genes: tuple[str, ...]
    observed_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    gene_false_positives: tuple[str, ...]
    gene_false_negatives: tuple[str, ...]
    function_false_positives: tuple[str, ...]
    function_false_negatives: tuple[str, ...]
    null_percentile: float
    null_retention_rate: float
    enriched_over_null: bool
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class NullModelRow:
    candidate_id: str
    null_index: int
    molecule: str
    proto_gene_score: float
    observed_genes: tuple[str, ...]
    observed_functions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AblationRow:
    candidate_id: str
    disabled_feature: str
    baseline_functions: tuple[str, ...]
    ablated_functions: tuple[str, ...]
    lost_functions: tuple[str, ...]
    baseline_score: float
    ablated_score: float


@dataclass(frozen=True, slots=True)
class ProtoGeneEvidenceRun:
    model_version: str
    candidates: list[EvidenceCandidate]
    null_rows: list[NullModelRow]
    ablation_rows: list[AblationRow]
    summary: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProtoGeneEvidencePaths:
    evidence_summary_json: Path
    evidence_candidates_csv: Path
    null_model_csv: Path
    ablation_summary_csv: Path
    proto_gene_evidence_report_md: Path


def _split_values(value: str | None) -> tuple[str, ...]:
    if not value:
        return tuple()
    return tuple(part.strip() for part in value.split(";") if part.strip() and part.strip().upper() != "NONE")


def _join(values: Iterable[str]) -> str:
    return ";".join(values)


def read_evidence_corpus(path: str | Path) -> list[EvidenceCorpusRow]:
    rows: list[EvidenceCorpusRow] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                EvidenceCorpusRow(
                    candidate_id=raw["candidate_id"],
                    group=raw["group"],
                    molecule=raw["molecule"],
                    expected_present_genes=_split_values(raw.get("expected_present_genes")),
                    expected_absent_genes=_split_values(raw.get("expected_absent_genes")),
                    expected_covered_functions=_split_values(raw.get("expected_covered_functions")),
                    expected_missing_functions=_split_values(raw.get("expected_missing_functions")),
                    expected_evidence_grade=raw["expected_evidence_grade"],
                    rationale=raw.get("rationale", ""),
                )
            )
    return rows


def _observed_gene_ids(gene_hits: list[ProtoGeneHit]) -> tuple[str, ...]:
    return tuple(hit.gene_id for hit in gene_hits if hit.present)


def _evaluate_molecule(molecule: str) -> tuple[RDKitEvaluation, SymbolicGraph, list[ProtoGeneHit], ProtoGenomeEvaluation, float]:
    rdkit_evaluation = evaluate_rdkit_molecule(molecule)
    symbolic_graph = build_symbolic_graph(rdkit_evaluation)
    gene_hits = detect_proto_genes(rdkit_evaluation)
    genome_evaluation = evaluate_proto_genome(gene_hits, rdkit_evaluation)
    candidate_score = score_candidate(rdkit_evaluation, gene_hits, genome_evaluation)
    return rdkit_evaluation, symbolic_graph, gene_hits, genome_evaluation, candidate_score


def compare_sets(expected: Iterable[str], observed: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    expected_set = set(expected)
    observed_set = set(observed)
    false_positives = tuple(sorted(observed_set - expected_set))
    false_negatives = tuple(sorted(expected_set - observed_set))
    return false_positives, false_negatives


def precision_recall(expected: Iterable[str], observed: Iterable[str]) -> dict[str, float]:
    expected_set = set(expected)
    observed_set = set(observed)
    true_positives = len(expected_set & observed_set)
    false_positives = len(observed_set - expected_set)
    false_negatives = len(expected_set - observed_set)
    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 1.0
    recall = true_positives / (true_positives + false_negatives) if true_positives + false_negatives else 1.0
    return {"precision": round(precision, 3), "recall": round(recall, 3)}


def generate_null_variants(molecule: str, *, runs: int, seed: int | None = None) -> list[str]:
    if runs < 0:
        raise ValueError("null runs must be non-negative")
    rng = random.Random(seed)
    genome = symbolic_genome_from_molecule(molecule)
    variants: list[str] = []
    for index in range(runs):
        shuffled_fragments = []
        for fragment in genome.fragments:
            elements = list(fragment)
            rng.shuffle(elements)
            if tuple(elements) == fragment and len(elements) > 1:
                offset = (index % (len(elements) - 1)) + 1
                elements = elements[offset:] + elements[:offset]
            shuffled_fragments.append(tuple(elements))
        shuffled = type(genome)(fragments=tuple(shuffled_fragments), motifs=tuple(), topology_hints=tuple())
        variants.append(symbolic_genome_to_molecule(shuffled))
    return variants


def _null_percentile(score: float, null_scores: list[float]) -> float:
    if not null_scores:
        return 1.0
    below_or_equal = sum(1 for null_score in null_scores if null_score <= score)
    return round(below_or_equal / len(null_scores), 3)


def _retention_rate(original_genes: tuple[str, ...], null_rows: list[NullModelRow]) -> float:
    if not original_genes or not null_rows:
        return 0.0
    original = set(original_genes)
    retained = 0
    threshold = max(1, len(original) // 2)
    for row in null_rows:
        if len(original & set(row.observed_genes)) >= threshold:
            retained += 1
    return round(retained / len(null_rows), 3)


def assign_evidence_grade(
    *,
    observed_genes: tuple[str, ...],
    observed_functions: tuple[str, ...],
    proto_gene_score: float,
    null_percentile: float,
    null_retention_rate: float,
    enriched_over_null: bool,
) -> str:
    if not observed_genes and not observed_functions:
        return "NONE"
    if observed_genes and not observed_functions:
        return "MOTIF_HIT"
    if enriched_over_null and null_percentile >= 0.80 and proto_gene_score >= 0.65 and len(observed_functions) >= 5:
        return "ROBUST_LEAD"
    if proto_gene_score >= 0.45 and null_retention_rate >= 0.25 and len(observed_functions) >= 3:
        return "LINEAGE_RETAINED"
    return "FUNCTIONAL_CANDIDATE"


def _ablate_functions(functions: tuple[str, ...], disabled_feature: str) -> tuple[str, ...]:
    disabled = set(FEATURE_TO_FUNCTIONS[disabled_feature])
    return tuple(function for function in functions if function not in disabled)


def ablate_candidate(candidate: EvidenceCandidate, disabled_feature: str) -> AblationRow:
    if disabled_feature not in FEATURE_GROUPS:
        raise ValueError(f"unknown feature group: {disabled_feature}")
    ablated_functions = _ablate_functions(candidate.observed_functions, disabled_feature)
    lost_functions = tuple(function for function in candidate.observed_functions if function not in ablated_functions)
    coverage_ratio = len(ablated_functions) / len(MINIMAL_FUNCTIONS)
    ablated_score = round(min(candidate.proto_gene_score, 0.65 * coverage_ratio + 0.35 * candidate.proto_gene_score), 3)
    return AblationRow(
        candidate_id=candidate.corpus_row.candidate_id,
        disabled_feature=disabled_feature,
        baseline_functions=candidate.observed_functions,
        ablated_functions=ablated_functions,
        lost_functions=lost_functions,
        baseline_score=candidate.proto_gene_score,
        ablated_score=ablated_score,
    )


def _evaluate_nulls(row: EvidenceCorpusRow, *, null_runs: int, seed: int | None) -> list[NullModelRow]:
    null_rows: list[NullModelRow] = []
    for index, molecule in enumerate(generate_null_variants(row.molecule, runs=null_runs, seed=seed), start=1):
        _, _, gene_hits, genome, score = _evaluate_molecule(molecule)
        null_rows.append(
            NullModelRow(
                candidate_id=row.candidate_id,
                null_index=index,
                molecule=molecule,
                proto_gene_score=score,
                observed_genes=_observed_gene_ids(gene_hits),
                observed_functions=genome.covered_functions,
            )
        )
    return null_rows


def evaluate_corpus_row(row: EvidenceCorpusRow, *, null_runs: int = 50, seed: int | None = None) -> tuple[EvidenceCandidate, list[NullModelRow]]:
    rdkit_evaluation, symbolic_graph, gene_hits, genome_evaluation, score = _evaluate_molecule(row.molecule)
    observed_genes = _observed_gene_ids(gene_hits)
    observed_functions = genome_evaluation.covered_functions
    gene_false_positives, gene_false_negatives = compare_sets(row.expected_present_genes, observed_genes)
    function_false_positives, function_false_negatives = compare_sets(row.expected_covered_functions, observed_functions)
    null_rows = _evaluate_nulls(row, null_runs=null_runs, seed=seed)
    null_scores = [item.proto_gene_score for item in null_rows]
    percentile = _null_percentile(score, null_scores)
    retention = _retention_rate(observed_genes, null_rows)
    enriched = bool(null_scores) and score > max(null_scores)
    grade = assign_evidence_grade(
        observed_genes=observed_genes,
        observed_functions=observed_functions,
        proto_gene_score=score,
        null_percentile=percentile,
        null_retention_rate=retention,
        enriched_over_null=enriched,
    )
    return (
        EvidenceCandidate(
            corpus_row=row,
            rdkit_evaluation=rdkit_evaluation,
            symbolic_graph=symbolic_graph,
            gene_hits=gene_hits,
            genome_evaluation=genome_evaluation,
            proto_gene_score=score,
            observed_genes=observed_genes,
            observed_functions=observed_functions,
            missing_functions=genome_evaluation.missing_functions,
            gene_false_positives=gene_false_positives,
            gene_false_negatives=gene_false_negatives,
            function_false_positives=function_false_positives,
            function_false_negatives=function_false_negatives,
            null_percentile=percentile,
            null_retention_rate=retention,
            enriched_over_null=enriched,
            evidence_grade=grade,
        ),
        null_rows,
    )


def _summary(candidates: list[EvidenceCandidate], null_rows: list[NullModelRow], ablation_rows: list[AblationRow]) -> dict[str, object]:
    expected_genes = [gene for candidate in candidates for gene in candidate.corpus_row.expected_present_genes]
    observed_genes = [gene for candidate in candidates for gene in candidate.observed_genes]
    expected_functions = [function for candidate in candidates for function in candidate.corpus_row.expected_covered_functions]
    observed_functions = [function for candidate in candidates for function in candidate.observed_functions]
    grade_counts: dict[str, int] = {grade: 0 for grade in EVIDENCE_GRADES}
    for candidate in candidates:
        grade_counts[candidate.evidence_grade] = grade_counts.get(candidate.evidence_grade, 0) + 1
    return {
        "model_version": MODEL_VERSION,
        "candidate_count": len(candidates),
        "null_variant_count": len(null_rows),
        "gene_metrics": precision_recall(expected_genes, observed_genes),
        "function_metrics": precision_recall(expected_functions, observed_functions),
        "gene_false_positives": sorted({gene for candidate in candidates for gene in candidate.gene_false_positives}),
        "gene_false_negatives": sorted({gene for candidate in candidates for gene in candidate.gene_false_negatives}),
        "function_false_positives": sorted({function for candidate in candidates for function in candidate.function_false_positives}),
        "function_false_negatives": sorted({function for candidate in candidates for function in candidate.function_false_negatives}),
        "grade_counts": grade_counts,
        "enriched_over_null_count": sum(1 for candidate in candidates if candidate.enriched_over_null),
        "ablation_loss_count": sum(1 for row in ablation_rows if row.lost_functions),
        "safety_scope": "computational evidence only; no synthesis protocols or lab parameters",
    }


def run_proto_gene_evidence(
    corpus_path: str | Path,
    *,
    null_runs: int = 50,
    seed: int | None = None,
    disabled_features: tuple[str, ...] = FEATURE_GROUPS,
) -> ProtoGeneEvidenceRun:
    candidates: list[EvidenceCandidate] = []
    null_rows: list[NullModelRow] = []
    ablation_rows: list[AblationRow] = []
    for row_index, row in enumerate(read_evidence_corpus(corpus_path)):
        candidate, candidate_null_rows = evaluate_corpus_row(row, null_runs=null_runs, seed=None if seed is None else seed + row_index)
        candidates.append(candidate)
        null_rows.extend(candidate_null_rows)
        for feature in disabled_features:
            ablation_rows.append(ablate_candidate(candidate, feature))
    return ProtoGeneEvidenceRun(
        model_version=MODEL_VERSION,
        candidates=candidates,
        null_rows=null_rows,
        ablation_rows=ablation_rows,
        summary=_summary(candidates, null_rows, ablation_rows),
    )


def candidate_rows(candidates: list[EvidenceCandidate]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate in candidates:
        row = candidate.corpus_row
        rows.append(
            {
                "model_version": MODEL_VERSION,
                "candidate_id": row.candidate_id,
                "group": row.group,
                "molecule": row.molecule,
                "molecular_validity": str(candidate.rdkit_evaluation.molecular_validity).lower(),
                "proto_gene_score": f"{candidate.proto_gene_score:.3f}",
                "expected_present_genes": _join(row.expected_present_genes),
                "observed_genes": _join(candidate.observed_genes),
                "gene_false_positives": _join(candidate.gene_false_positives),
                "gene_false_negatives": _join(candidate.gene_false_negatives),
                "expected_covered_functions": _join(row.expected_covered_functions),
                "observed_functions": _join(candidate.observed_functions),
                "function_false_positives": _join(candidate.function_false_positives),
                "function_false_negatives": _join(candidate.function_false_negatives),
                "expected_evidence_grade": row.expected_evidence_grade,
                "evidence_grade": candidate.evidence_grade,
                "null_percentile": f"{candidate.null_percentile:.3f}",
                "null_retention_rate": f"{candidate.null_retention_rate:.3f}",
                "enriched_over_null": str(candidate.enriched_over_null).lower(),
                "topology_tags": _join(candidate.symbolic_graph.topology_tags),
                "rationale": row.rationale,
            }
        )
    return rows


def null_model_rows(rows: list[NullModelRow]) -> list[dict[str, str]]:
    return [
        {
            "model_version": MODEL_VERSION,
            "candidate_id": row.candidate_id,
            "null_index": str(row.null_index),
            "molecule": row.molecule,
            "proto_gene_score": f"{row.proto_gene_score:.3f}",
            "observed_genes": _join(row.observed_genes),
            "observed_functions": _join(row.observed_functions),
        }
        for row in rows
    ]


def ablation_summary_rows(rows: list[AblationRow]) -> list[dict[str, str]]:
    return [
        {
            "model_version": MODEL_VERSION,
            "candidate_id": row.candidate_id,
            "disabled_feature": row.disabled_feature,
            "baseline_functions": _join(row.baseline_functions),
            "ablated_functions": _join(row.ablated_functions),
            "lost_functions": _join(row.lost_functions),
            "baseline_score": f"{row.baseline_score:.3f}",
            "ablated_score": f"{row.ablated_score:.3f}",
        }
        for row in rows
    ]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["model_version"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_evidence_report(run: ProtoGeneEvidenceRun) -> str:
    candidates = run.candidates
    robust = [candidate for candidate in candidates if candidate.evidence_grade == "ROBUST_LEAD"]
    proto_candidates = [candidate for candidate in candidates if candidate.evidence_grade in {"FUNCTIONAL_CANDIDATE", "LINEAGE_RETAINED", "ROBUST_LEAD"}]
    false_positive_rows = [candidate for candidate in candidates if candidate.gene_false_positives or candidate.function_false_positives]
    false_negative_rows = [candidate for candidate in candidates if candidate.gene_false_negatives or candidate.function_false_negatives]
    single_feature_rows = [row for row in run.ablation_rows if row.lost_functions and len(row.baseline_functions) - len(row.lost_functions) <= 1]
    enriched = [candidate for candidate in candidates if candidate.enriched_over_null]

    lines = [
        "# Proto-gene evidence report",
        "",
        f"- model_version: `{run.model_version}`",
        "- scope: computational evidence only; not wet-lab proof",
        "- safety: no synthesis protocols or lab parameters are included",
        "",
        "## Summary",
        "",
        f"- candidates: {run.summary['candidate_count']}",
        f"- null variants: {run.summary['null_variant_count']}",
        f"- gene precision/recall: {run.summary['gene_metrics']}",
        f"- function precision/recall: {run.summary['function_metrics']}",
        f"- enriched over null: {run.summary['enriched_over_null_count']}",
        "",
        "## Proto-gene candidates",
    ]
    if proto_candidates:
        for candidate in proto_candidates:
            lines.append(
                f"- {candidate.corpus_row.candidate_id}: grade={candidate.evidence_grade}; "
                f"score={candidate.proto_gene_score:.3f}; genes={_join(candidate.observed_genes) or 'none'}; "
                f"functions={_join(candidate.observed_functions) or 'none'}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Strong and robust leads"])
    if robust:
        for candidate in robust:
            lines.append(f"- {candidate.corpus_row.candidate_id}: null_percentile={candidate.null_percentile:.3f}")
    else:
        lines.append("- none under this run")

    covered = sorted({function for candidate in candidates for function in candidate.observed_functions})
    lines.extend(["", "## Functions covered robustly", "", "- " + (_join(covered) if covered else "none")])

    lines.extend(["", "## False positives"])
    if false_positive_rows:
        for candidate in false_positive_rows:
            lines.append(
                f"- {candidate.corpus_row.candidate_id}: genes={_join(candidate.gene_false_positives) or 'none'}; "
                f"functions={_join(candidate.function_false_positives) or 'none'}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## False negatives"])
    if false_negative_rows:
        for candidate in false_negative_rows:
            lines.append(
                f"- {candidate.corpus_row.candidate_id}: genes={_join(candidate.gene_false_negatives) or 'none'}; "
                f"functions={_join(candidate.function_false_negatives) or 'none'}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Single-heuristic dependencies"])
    if single_feature_rows:
        for row in single_feature_rows:
            lines.append(f"- {row.candidate_id}: disable {row.disabled_feature} loses {_join(row.lost_functions)}")
    else:
        lines.append("- none flagged by this ablation run")

    lines.extend(["", "## Enriched over null"])
    if enriched:
        for candidate in enriched:
            lines.append(f"- {candidate.corpus_row.candidate_id}: percentile={candidate.null_percentile:.3f}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Model limitations",
            "",
            "- Evidence is limited to the current Silive heuristics and corpus expectations.",
            "- Null variants are symbolic motif shuffles, not real reaction products.",
            "- Ablation removes modeled feature groups; it is not a physical intervention.",
            "- RDKit parsing is optional and may reject symbolic candidates that remain useful for model tests.",
            "- Chemistry-like interpretations are heuristic/model assumptions, not experimental claims.",
        ]
    )
    return "\n".join(lines)


def write_proto_gene_evidence_outputs(run: ProtoGeneEvidenceRun, output_dir: str | Path) -> ProtoGeneEvidencePaths:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = ProtoGeneEvidencePaths(
        evidence_summary_json=output / "evidence_summary.json",
        evidence_candidates_csv=output / "evidence_candidates.csv",
        null_model_csv=output / "null_model.csv",
        ablation_summary_csv=output / "ablation_summary.csv",
        proto_gene_evidence_report_md=output / "proto_gene_evidence_report.md",
    )
    paths.evidence_summary_json.write_text(json.dumps(run.summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(paths.evidence_candidates_csv, candidate_rows(run.candidates))
    _write_csv(paths.null_model_csv, null_model_rows(run.null_rows))
    _write_csv(paths.ablation_summary_csv, ablation_summary_rows(run.ablation_rows))
    paths.proto_gene_evidence_report_md.write_text(build_evidence_report(run) + "\n", encoding="utf-8")
    return paths
