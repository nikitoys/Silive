import csv
import json

import pytest

from silive.niche_search import (
    format_niche_ranking,
    niche_candidate_row,
    niche_candidate_sort_key,
    niche_search_payload,
    run_niche_search,
    write_niche_search_outputs,
)


def test_run_niche_search_returns_top_chain_environment_pairs() -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=2,
        top_n=4,
        generations=3,
        runs=1,
        seed=42,
    )

    assert search.seed_chain == ("Si", "O", "Si", "O", "Fe", "O", "Si")
    assert len(search.candidates) >= 6
    assert len(search.top_candidates) == 4
    assert all(candidate.simulation.evaluation.chain == candidate.chain for candidate in search.top_candidates)


def test_niche_search_rejects_invalid_rounds_and_top() -> None:
    with pytest.raises(ValueError, match="rounds must be positive"):
        run_niche_search("Si-O-Si", rounds=0)

    with pytest.raises(ValueError, match="top_n must be positive"):
        run_niche_search("Si-O-Si", top_n=0)


def test_niche_candidates_are_sorted_by_requested_metrics() -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=2,
        top_n=8,
        generations=3,
        runs=1,
        seed=42,
    )
    keys = [niche_candidate_sort_key(candidate) for candidate in search.top_candidates]

    assert keys == sorted(keys, reverse=True)


def test_niche_candidate_row_contains_requested_fields() -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=1,
        top_n=2,
        generations=3,
        runs=1,
        seed=42,
    )
    row = niche_candidate_row(search.top_candidates[0])

    assert "chain" in row
    assert "environment" in row
    assert "viability_score" in row
    assert "survival_rate" in row
    assert "code_preservation_rate" in row
    assert "avg_final_population" in row
    assert "predicted_functions" in row
    assert "missing_functions" in row
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


def test_niche_search_payload_contains_top_candidates() -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=1,
        top_n=3,
        generations=3,
        runs=1,
        seed=42,
    )
    payload = niche_search_payload(search)

    assert payload["seed_chain"] == "Si-O-Si-O-Fe-O-Si"
    assert payload["candidate_count"] >= 6
    assert len(payload["top_candidates"]) == 3


def test_write_niche_search_outputs(tmp_path) -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=1,
        top_n=3,
        generations=3,
        runs=1,
        seed=42,
    )
    paths = write_niche_search_outputs(search, tmp_path)

    assert paths.niche_search_csv.exists()
    assert paths.niche_search_json.exists()

    with paths.niche_search_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert rows[0]["rank"] == "1"
    assert rows[0]["chain"]
    assert rows[0]["environment"]
    assert rows[0]["viability_score"]

    payload = json.loads(paths.niche_search_json.read_text(encoding="utf-8"))
    assert payload["seed_chain"] == "Si-O-Si-O-Fe-O-Si"
    assert len(payload["top_candidates"]) == 3


def test_format_niche_ranking_contains_top_n_table() -> None:
    search = run_niche_search(
        "Si-O-Si-O-Fe-O-Si",
        rounds=1,
        top_n=3,
        generations=3,
        runs=1,
        seed=42,
    )
    text = format_niche_ranking(search)

    assert "rank | score | survival | code | population" in text
    assert "Si" in text
    assert "hydrothermal" in text or "none" in text
