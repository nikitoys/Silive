import importlib.util

import pytest

from silive.proto_genes import detect_proto_genes
from silive.proto_genome import evaluate_proto_genome, format_proto_genome_evaluation, format_rdkit_genome_scorecard
from silive.rdkit_chemistry import evaluate_rdkit_molecule

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def _genome_for(molecule: str):
    rdkit_evaluation = evaluate_rdkit_molecule(molecule)
    gene_hits = detect_proto_genes(rdkit_evaluation)
    return evaluate_proto_genome(gene_hits, rdkit_evaluation)


def test_proto_genome_detects_missing_repair_for_iron_siloxane_chain() -> None:
    genome = _genome_for("[Si]O[Si]O[Fe]O[Si]")

    assert "TEMPLATE" in genome.covered_functions
    assert "POLYMERIZE" in genome.covered_functions
    assert "CATALYZE" in genome.covered_functions
    assert "SEPARATE" in genome.covered_functions
    assert "REPAIR" in genome.missing_functions
    assert genome.minimal_viable is False
    assert genome.genome_score > 0
    assert any("P-O" in recommendation for recommendation in genome.recommendations)


def test_proto_genome_scores_fuller_candidate_with_phosphate_bridge() -> None:
    genome = _genome_for("[Si]O[Si]O[Fe]OP(=O)(O)O[Si]")

    assert "TEMPLATE" in genome.covered_functions
    assert "POLYMERIZE" in genome.covered_functions
    assert "CATALYZE" in genome.covered_functions
    assert "REPAIR" in genome.covered_functions
    assert genome.genome_score >= 0.5


def test_proto_genome_format_contains_required_sections() -> None:
    genome = _genome_for("[Si]O[Si]O[Fe]O[Si]")
    text = format_proto_genome_evaluation(genome)

    assert "minimal proto-genome coverage" in text
    assert "covered functions:" in text
    assert "missing functions:" in text
    assert "bottlenecks:" in text
    assert "recommendations:" in text
    assert "genome_score:" in text


def test_rdkit_genome_scorecard_includes_gene_and_genome_sections() -> None:
    rdkit_evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")
    text = format_rdkit_genome_scorecard(rdkit_evaluation)

    assert "molecular_validity: true" in text
    assert "proto-gene summary" in text
    assert "minimal proto-genome coverage" in text
