import csv
import random

import pytest

from silive.chemistry import (
    average_chain_properties,
    evaluate_chain,
    format_scorecard,
    format_search_results,
    mutate_chain,
    parse_chain,
    predicted_functions,
    score_functions,
    search_chains,
    write_chain_search_csv,
)


def test_parse_chain_accepts_dash_separated_elements() -> None:
    assert parse_chain("Si-O-Si-O-Fe-O-Si") == ("Si", "O", "Si", "O", "Fe", "O", "Si")


def test_parse_chain_rejects_unknown_elements() -> None:
    with pytest.raises(ValueError, match="unknown element"):
        parse_chain("Si-Xx-O")


def test_average_chain_properties_scores_silicate_chain_as_stable_template() -> None:
    properties = average_chain_properties(("Si", "O", "Si", "O", "Si"))

    assert properties["stability"] > 0.8
    assert properties["template"] > 0.7
    assert properties["catalysis"] < 0.2


def test_score_functions_maps_properties_to_proto_life_functions() -> None:
    function_scores = score_functions(
        {
            "stability": 0.8,
            "template": 0.8,
            "catalysis": 0.8,
            "repair": 0.6,
            "separation": 0.6,
        }
    )

    functions = predicted_functions(function_scores)

    assert "POL" in functions
    assert "SEP" in functions
    assert "SHELL" in functions
    assert "REPAIR" in functions
    assert "CAT" in functions


def test_evaluate_chain_returns_scorecard_fields() -> None:
    evaluation = evaluate_chain("Si-O-Si-O-Fe-O-Si")

    assert evaluation.chain == ("Si", "O", "Si", "O", "Fe", "O", "Si")
    assert set(evaluation.properties) == {"stability", "template", "catalysis", "repair", "separation"}
    assert set(evaluation.function_scores) == {"POL", "SEP", "SHELL", "REPAIR", "CAT"}
    assert "SHELL" in evaluation.predicted_functions
    assert evaluation.viability_score > 0
    assert evaluation.viability in {
        "stable_proto_life_candidate",
        "proto_life_candidate",
        "incomplete_proto_life_candidate",
        "stable_inert_candidate",
        "weak_candidate",
    }


def test_format_scorecard_includes_missing_functions_and_viability() -> None:
    scorecard = format_scorecard(evaluate_chain("Si-O-Si-O-Fe-O-Si"))

    assert "chain: Si-O-Si-O-Fe-O-Si" in scorecard
    assert "properties:" in scorecard
    assert "function scores:" in scorecard
    assert "missing functions:" in scorecard
    assert "viability:" in scorecard
    assert "viability score:" in scorecard


def test_mutate_chain_keeps_chain_valid() -> None:
    rng = random.Random(42)
    mutated = mutate_chain(("Si", "O", "Si"), rng)

    assert len(mutated) >= 2
    assert mutated != ("Si", "O", "Si")
    parse_chain(mutated)


def test_search_chains_returns_sorted_top_candidates() -> None:
    results = search_chains("Si-O-Si-O-Fe-O-Si", rounds=20, top_n=5, seed=42)

    assert len(results) == 5
    scores = [result.evaluation.viability_score for result in results]
    assert scores == sorted(scores, reverse=True)
    assert all(result.evaluation.chain for result in results)


def test_write_chain_search_csv(tmp_path) -> None:
    results = search_chains("Si-O-Si-O-Fe-O-Si", rounds=5, top_n=3, seed=42)
    output = tmp_path / "chain_search.csv"

    write_chain_search_csv(results, output)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 3
    assert rows[0]["rank"] == "1"
    assert rows[0]["chain"]
    assert rows[0]["viability_score"]


def test_format_search_results_contains_ranked_table() -> None:
    results = search_chains("Si-O-Si-O-Fe-O-Si", rounds=5, top_n=3, seed=42)
    text = format_search_results(results)

    assert "rank | score | viability" in text
    assert "Si" in text
