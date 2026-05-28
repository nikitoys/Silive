import importlib.util

import pytest

from silive.rdkit_chemistry import evaluate_rdkit_molecule
from silive.reaction_simulator import (
    REACTION_RULES,
    format_reaction_results,
    reaction_search,
    simulate_reactions,
    write_reaction_search_csv,
)

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def test_reaction_rules_include_required_ids() -> None:
    ids = {rule.rule_id for rule in REACTION_RULES}

    assert "RXN_SIO_GROWTH" in ids
    assert "RXN_SIO_BRANCH" in ids
    assert "RXN_FE_CENTER_ADD" in ids
    assert "RXN_NI_CENTER_ADD" in ids
    assert "RXN_P_REPAIR_BRIDGE" in ids
    assert "RXN_LABILE_BREAK" in ids
    assert "RXN_RING_CLOSURE" in ids
    assert "RXN_FRAGMENT_REJOIN" in ids


def test_simulate_reactions_returns_ranked_opportunities() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")
    results = simulate_reactions(evaluation)

    assert results
    assert results == sorted(results, key=lambda result: result.delta_score, reverse=True)
    assert any(result.reaction_id == "RXN_P_REPAIR_BRIDGE" for result in results)
    assert any("REPAIR" in result.new_functions for result in results)
    assert all(result.after_score >= 0 for result in results)


def test_format_reaction_results_contains_required_sections() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")
    text = format_reaction_results(simulate_reactions(evaluation), top=3)

    assert "source genome_score:" in text
    assert "reaction opportunities:" in text
    assert "delta_score:" in text
    assert "new_functions:" in text
    assert "risks:" in text


def test_reaction_search_and_csv(tmp_path) -> None:
    path = tmp_path / "candidates.smi"
    output = tmp_path / "reaction_search.csv"
    path.write_text("[Si]O[Si]O[Fe]O[Si] iron_chain\nnot_a_valid invalid\n", encoding="utf-8")

    rows = reaction_search(path, top=5)
    write_reaction_search_csv(rows, output)
    text = output.read_text(encoding="utf-8")

    assert rows
    assert rows[0][0] == "iron_chain"
    assert "rank,name,molecule,reaction_id" in text
    assert "product_symbolic_description" in text
