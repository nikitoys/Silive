import importlib.util

import pytest

from silive.rdkit_chemistry import evaluate_rdkit_molecule, format_rdkit_scorecard

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def test_graph_motifs_and_symbolic_scorecard() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")

    assert evaluation.molecular_validity is True
    assert evaluation.parser == "SMILES"
    assert evaluation.elements == ("Si", "O", "Si", "O", "Fe", "O", "Si")
    assert len(evaluation.atoms) == 7
    assert len(evaluation.bonds) == 6
    assert evaluation.rings == ()
    assert len(evaluation.fragments) == 1
    assert evaluation.motifs["Si-O-Si"] == 1
    assert evaluation.motifs["Fe-O"] == 2
    assert evaluation.motifs["Ni-O"] == 0
    assert evaluation.motifs["P-O"] == 0
    assert evaluation.symbolic_chain == ("Si", "O", "Si", "O", "Fe", "O", "Si")
    assert evaluation.chain_evaluation is not None


def test_scorecard_includes_required_sections() -> None:
    text = format_rdkit_scorecard(evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]"))

    assert "molecular_validity: true" in text
    assert "atoms:" in text
    assert "bonds:" in text
    assert "rings:" in text
    assert "fragments:" in text
    assert "motifs:" in text
    assert "symbolic chain: Si-O-Si-O-Fe-O-Si" in text
    assert "symbolic scorecard:" in text
