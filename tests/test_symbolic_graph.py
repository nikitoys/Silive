import importlib.util

import pytest

from silive.proto_genes import detect_proto_genes
from silive.proto_genome import evaluate_proto_genome
from silive.rdkit_chemistry import evaluate_rdkit_molecule
from silive.symbolic_graph import build_symbolic_graph, format_symbolic_graph_summary

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def test_linear_si_o_si_graph() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]")
    graph = build_symbolic_graph(evaluation)

    assert "linear" in graph.topology_tags
    assert "siloxane_rich" in graph.topology_tags
    assert graph.graph_properties["si_o_bond_count"] == 2.0
    assert graph.graph_properties["backbone_length"] == 3.0
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


def test_branched_phosphate_candidate_graph() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]OP(=O)(O)O[Si]")
    graph = build_symbolic_graph(evaluation)

    assert "branched" in graph.topology_tags
    assert "phosphate_bridge" in graph.topology_tags
    assert graph.graph_properties["p_o_bond_count"] >= 4.0
    assert graph.graph_properties["branching_score"] > 0


def test_ring_candidate_graph() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]1O[Si]O1")
    graph = build_symbolic_graph(evaluation)

    assert "ring" in graph.topology_tags
    assert graph.graph_properties["ring_count"] == 1.0
    assert graph.graph_properties["network_score"] > 0


def test_fragmented_candidate_graph() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si].[Fe]O")
    graph = build_symbolic_graph(evaluation)

    assert "fragmented" in graph.topology_tags
    assert graph.graph_properties["fragment_count"] == 2.0
    assert len(graph.fragments) == 2


def test_symbolic_graph_integrates_with_proto_genome() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]1O[Si]O1")
    hits = detect_proto_genes(evaluation)
    genome = evaluate_proto_genome(hits, evaluation)

    assert "GENE_SILOXANE_SHELL" in {hit.gene_id for hit in hits if hit.present}
    assert "PROTECT" in genome.covered_functions


def test_symbolic_graph_summary_contains_required_sections() -> None:
    text = format_symbolic_graph_summary(build_symbolic_graph(evaluate_rdkit_molecule("[Si]O[Si]")))

    assert "symbolic graph summary" in text
    assert "topology tags:" in text
    assert "graph properties:" in text
    assert "main backbone:" in text
    assert "fragments:" in text
