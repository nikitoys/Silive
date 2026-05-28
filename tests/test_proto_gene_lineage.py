import importlib.util
import json

import pytest

from silive.proto_gene_lineage import (
    SAFETY_DISCLAIMER,
    ProtoGeneLineageConfig,
    chain_candidate,
    format_proto_gene_report,
    rdkit_candidate,
    run_proto_gene_lineage_search,
    write_proto_gene_outputs,
)


def _bounded(values) -> bool:
    return all(0.0 <= value <= 1.0 for value in values)


def test_chain_template_score_prefers_siloxane_rich_candidate() -> None:
    rich = chain_candidate("Si-O-Si-O-Si", candidate_id="rich", runs=1, seed=1)
    weak = chain_candidate("C-H-C-H-C", candidate_id="weak", runs=1, seed=1)

    assert rich.metrics.template_score > weak.metrics.template_score
    assert _bounded(
        [
            rich.metrics.template_score,
            rich.metrics.copyability_score,
            rich.metrics.separation_score,
            rich.metrics.survival_score,
            rich.metrics.function_retention_rate,
            rich.metrics.proto_gene_score,
        ]
    )


def test_chain_lineage_run_is_deterministic_with_seed() -> None:
    config = ProtoGeneLineageConfig(
        mode="chain",
        seed_chain="Si-O-Si-O-Fe-O-Si",
        generations=2,
        population_size=3,
        rounds=5,
        runs=1,
        seed=42,
        environment="hydrothermal",
    )

    first = run_proto_gene_lineage_search(config)
    second = run_proto_gene_lineage_search(config)

    assert [row.motif for row in first.ranked_candidates] == [row.motif for row in second.ranked_candidates]
    assert [row.event_labels for row in first.lineage_history] == [row.event_labels for row in second.lineage_history]
    assert first.summary["lineage_steps"] == second.summary["lineage_steps"]


def test_lineage_depth_increases_when_functions_are_retained() -> None:
    config = ProtoGeneLineageConfig(
        mode="chain",
        seed_chain="Si-O-Si-O-Si-O-Si",
        generations=1,
        population_size=2,
        rounds=3,
        runs=1,
        seed=5,
    )

    run = run_proto_gene_lineage_search(config)

    assert run.best_candidate is not None
    assert run.best_candidate.metrics.lineage_depth >= 1
    assert any("function_retained" in node.event_labels for node in run.lineage_history)


def test_chain_lineage_outputs_expected_files(tmp_path) -> None:
    config = ProtoGeneLineageConfig(
        mode="chain",
        seed_chain="Si-O-Si-O-Fe-O-Si",
        generations=1,
        population_size=2,
        rounds=3,
        runs=1,
        seed=7,
    )
    run = run_proto_gene_lineage_search(config)
    paths = write_proto_gene_outputs(run, tmp_path)

    assert paths.proto_gene_candidates_csv.exists()
    assert paths.lineage_history_csv.exists()
    assert paths.proto_gene_summary_json.exists()
    assert paths.best_proto_gene_json.exists()
    assert paths.proto_gene_report_md.exists()
    assert "proto_gene_score" in paths.proto_gene_candidates_csv.read_text(encoding="utf-8")
    assert "function_retention_rate" in paths.lineage_history_csv.read_text(encoding="utf-8")
    assert SAFETY_DISCLAIMER in paths.proto_gene_report_md.read_text(encoding="utf-8")
    assert json.loads(paths.proto_gene_summary_json.read_text(encoding="utf-8"))["safety"] == SAFETY_DISCLAIMER


def test_extinction_reported_when_retention_threshold_cannot_be_met() -> None:
    config = ProtoGeneLineageConfig(
        mode="chain",
        seed_chain="C-H-C-H-C",
        generations=1,
        population_size=2,
        rounds=2,
        runs=1,
        seed=3,
        retention_threshold=1.01,
    )

    run = run_proto_gene_lineage_search(config)

    assert run.summary["extinct"] is True
    assert not run.ranked_candidates
    assert "No candidate survived" in format_proto_gene_report(run)


pytestmark_rdkit = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


@pytestmark_rdkit
def test_rdkit_fragmented_candidate_improves_separation_score() -> None:
    fragmented = rdkit_candidate("[Si]O[Si].[Fe]O", candidate_id="fragmented")
    linear = rdkit_candidate("[Si]O[Si]O[Fe]", candidate_id="linear")

    assert fragmented.metrics.separation_score > linear.metrics.separation_score


@pytestmark_rdkit
def test_rdkit_ring_candidate_improves_survival_score() -> None:
    ring = rdkit_candidate("[Si]1O[Si]O1", candidate_id="ring")
    linear = rdkit_candidate("[Si]O[Si]", candidate_id="linear")

    assert ring.metrics.survival_score > linear.metrics.survival_score


@pytestmark_rdkit
def test_rdkit_invalid_candidate_is_marked_invalid_without_crashing() -> None:
    candidate = rdkit_candidate("not_a_valid_smiles", candidate_id="bad")

    assert candidate.molecular_validity is False
    assert candidate.viability == "invalid_or_unusable"
    assert candidate.parse_error
