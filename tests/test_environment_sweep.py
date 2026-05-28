import csv
import json

from silive.environment_sweep import (
    ENVIRONMENT_SWEEP_ORDER,
    environment_sweep_payload,
    environment_sweep_row,
    format_environment_ranking,
    run_environment_sweep,
    write_environment_sweep_outputs,
)


def test_environment_sweep_order_includes_none_and_all_environments() -> None:
    assert ENVIRONMENT_SWEEP_ORDER == (None, "hydrothermal", "dry_hot", "acidic", "alkaline", "cold")


def test_run_environment_sweep_returns_one_result_per_environment() -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)

    assert len(sweep.results) == 6
    assert [result.evaluation.environment for result in sweep.results] == list(ENVIRONMENT_SWEEP_ORDER)
    assert len(sweep.ranking) == 6


def test_environment_sweep_row_contains_requested_fields() -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)
    row = environment_sweep_row(sweep.results[0])

    assert row["environment"] == "none"
    assert row["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert "stability" in row
    assert "template" in row
    assert "catalysis" in row
    assert "repair" in row
    assert "separation" in row
    assert "POL" in row
    assert "SEP" in row
    assert "SHELL" in row
    assert "REPAIR" in row
    assert "CAT" in row
    assert "predicted_functions" in row
    assert "missing_functions" in row
    assert "viability" in row
    assert "viability_score" in row
    assert "survival_rate" in row
    assert "code_preservation_rate" in row
    assert "avg_final_population" in row


def test_environment_sweep_ranking_sorted_by_viability_and_survival() -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)
    ranking_keys = [
        (
            result.evaluation.viability_score,
            result.survival_rate,
            result.code_preservation_rate,
            result.avg_final_population,
        )
        for result in sweep.ranking
    ]

    assert ranking_keys == sorted(ranking_keys, reverse=True)


def test_environment_sweep_payload_contains_environments_and_ranking() -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)
    payload = environment_sweep_payload(sweep)

    assert payload["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert len(payload["environments"]) == 6
    assert len(payload["ranking"]) == 6


def test_write_environment_sweep_outputs(tmp_path) -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)
    paths = write_environment_sweep_outputs(sweep, tmp_path)

    assert paths.environment_sweep_csv.exists()
    assert paths.environment_sweep_json.exists()

    with paths.environment_sweep_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert rows[0]["environment"] == "none"
    assert rows[0]["survival_rate"]

    payload = json.loads(paths.environment_sweep_json.read_text(encoding="utf-8"))
    assert payload["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert len(payload["environments"]) == 6
    assert len(payload["ranking"]) == 6


def test_format_environment_ranking_contains_ranking_table() -> None:
    sweep = run_environment_sweep("Si-O-Si-O-Fe-O-Si", generations=5, runs=2, seed=42)
    text = format_environment_ranking(sweep)

    assert "rank | environment | viability_score | survival_rate" in text
    assert "hydrothermal" in text
    assert "none" in text
