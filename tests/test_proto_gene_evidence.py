import importlib.util

import pytest

from silive.proto_gene_evidence import (
    MODEL_VERSION,
    EvidenceCandidate,
    EvidenceCorpusRow,
    ablate_candidate,
    assign_evidence_grade,
    generate_null_variants,
    read_evidence_corpus,
    run_proto_gene_evidence,
    write_proto_gene_evidence_outputs,
)


def test_evidence_grading_distinguishes_levels() -> None:
    assert (
        assign_evidence_grade(
            observed_genes=(),
            observed_functions=(),
            proto_gene_score=0.0,
            null_percentile=0.0,
            null_retention_rate=0.0,
            enriched_over_null=False,
        )
        == "NONE"
    )
    assert (
        assign_evidence_grade(
            observed_genes=("GENE_SI_TEMPLATE",),
            observed_functions=(),
            proto_gene_score=0.2,
            null_percentile=0.5,
            null_retention_rate=0.0,
            enriched_over_null=False,
        )
        == "MOTIF_HIT"
    )
    assert (
        assign_evidence_grade(
            observed_genes=("GENE_SI_TEMPLATE", "GENE_FE_CATALYSIS"),
            observed_functions=("TEMPLATE", "POLYMERIZE", "CATALYZE"),
            proto_gene_score=0.5,
            null_percentile=0.7,
            null_retention_rate=0.5,
            enriched_over_null=False,
        )
        == "LINEAGE_RETAINED"
    )
    assert (
        assign_evidence_grade(
            observed_genes=("GENE_SI_TEMPLATE", "GENE_FE_CATALYSIS", "GENE_P_REPAIR"),
            observed_functions=("TEMPLATE", "POLYMERIZE", "CATALYZE", "SEPARATE", "REPAIR"),
            proto_gene_score=0.8,
            null_percentile=0.9,
            null_retention_rate=0.5,
            enriched_over_null=True,
        )
        == "ROBUST_LEAD"
    )


def test_null_variants_are_deterministic_with_seed() -> None:
    first = generate_null_variants("[Si]O[Si]O[Fe]", runs=5, seed=42)
    second = generate_null_variants("[Si]O[Si]O[Fe]", runs=5, seed=42)

    assert first == second
    assert len(first) == 5
    assert any(variant != "[Si]O[Si]O[Fe]" for variant in first)


def test_ablation_changes_expected_fields() -> None:
    corpus_row = EvidenceCorpusRow(
        candidate_id="candidate",
        group="test",
        molecule="[Si]O[Si]",
        expected_present_genes=(),
        expected_absent_genes=(),
        expected_covered_functions=(),
        expected_missing_functions=(),
        expected_evidence_grade="FUNCTIONAL_CANDIDATE",
        rationale="test fixture",
    )
    candidate = EvidenceCandidate(
        corpus_row=corpus_row,
        rdkit_evaluation=None,  # type: ignore[arg-type]
        symbolic_graph=None,  # type: ignore[arg-type]
        gene_hits=[],
        genome_evaluation=None,  # type: ignore[arg-type]
        proto_gene_score=0.6,
        observed_genes=("GENE_SI_TEMPLATE",),
        observed_functions=("TEMPLATE", "POLYMERIZE", "SEPARATE"),
        missing_functions=("CATALYZE", "PROTECT", "REPAIR"),
        gene_false_positives=(),
        gene_false_negatives=(),
        function_false_positives=(),
        function_false_negatives=(),
        null_percentile=0.8,
        null_retention_rate=0.4,
        enriched_over_null=True,
        evidence_grade="LINEAGE_RETAINED",
    )

    row = ablate_candidate(candidate, "template")

    assert row.disabled_feature == "template"
    assert row.lost_functions == ("TEMPLATE", "POLYMERIZE")
    assert row.ablated_functions == ("SEPARATE",)
    assert row.ablated_score < row.baseline_score


def test_read_evidence_corpus_smoke() -> None:
    rows = read_evidence_corpus("examples/proto_gene_evidence_corpus.csv")

    assert rows
    assert rows[0].candidate_id == "siloxane_template_01"
    assert "GENE_SI_TEMPLATE" in rows[0].expected_present_genes


@pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")
def test_proto_gene_evidence_corpus_smoke_writes_outputs(tmp_path) -> None:
    corpus = tmp_path / "corpus.csv"
    corpus.write_text(
        "candidate_id,group,molecule,expected_present_genes,expected_absent_genes,"
        "expected_covered_functions,expected_missing_functions,expected_evidence_grade,rationale\n"
        "combo,combined_minimal_proto_genome,[Si]O[Si]O[Fe]OP(=O)(O)O[Si],"
        "GENE_SI_TEMPLATE;GENE_FE_CATALYSIS;GENE_P_REPAIR,GENE_NI_CATALYSIS,"
        "TEMPLATE;POLYMERIZE;CATALYZE;SEPARATE;REPAIR,PROTECT,LINEAGE_RETAINED,"
        "expected model behavior\n",
        encoding="utf-8",
    )

    run = run_proto_gene_evidence(corpus, null_runs=3, seed=42)
    paths = write_proto_gene_evidence_outputs(run, tmp_path / "out")

    assert run.model_version == MODEL_VERSION
    assert run.summary["candidate_count"] == 1
    assert len(run.null_rows) == 3
    assert paths.evidence_summary_json.exists()
    assert paths.evidence_candidates_csv.exists()
    assert paths.null_model_csv.exists()
    assert paths.ablation_summary_csv.exists()
    assert paths.proto_gene_evidence_report_md.exists()
    assert MODEL_VERSION in paths.evidence_candidates_csv.read_text(encoding="utf-8")
    assert "Proto-gene evidence report" in paths.proto_gene_evidence_report_md.read_text(encoding="utf-8")
