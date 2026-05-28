import importlib.util

import pytest

from silive.proto_genes import covered_functions, detect_proto_genes, missing_functions, proto_gene_summary
from silive.rdkit_chemistry import evaluate_rdkit_molecule

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def _by_id(hits):
    return {hit.gene_id: hit for hit in hits}


def test_detect_proto_genes_from_siloxane_iron_chain() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")
    hits = _by_id(detect_proto_genes(evaluation))

    assert hits["GENE_SI_TEMPLATE"].present is True
    assert hits["GENE_FE_CATALYSIS"].present is True
    assert hits["GENE_NI_CATALYSIS"].present is False
    assert hits["GENE_P_REPAIR"].present is False
    assert hits["GENE_LABILE_SEPARATION"].present is True

    assert "POL" in hits["GENE_SI_TEMPLATE"].functions
    assert "CAT" in hits["GENE_FE_CATALYSIS"].functions
    assert "SEP" in hits["GENE_LABILE_SEPARATION"].functions


def test_proto_gene_summary_reports_covered_and_missing_functions() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]O[Si]O[Fe]O[Si]")
    hits = detect_proto_genes(evaluation)
    summary = proto_gene_summary(hits)

    assert "detected genes:" in summary
    assert "GENE_SI_TEMPLATE" in summary
    assert "GENE_FE_CATALYSIS" in summary
    assert "absent genes:" in summary
    assert "GENE_P_REPAIR" in summary
    assert "covered functions:" in summary
    assert "missing functions:" in summary
    assert "REPAIR" in missing_functions(hits)
    assert "POL" in covered_functions(hits)
    assert "CAT" in covered_functions(hits)


def test_phosphate_bridge_detects_repair_gene() -> None:
    evaluation = evaluate_rdkit_molecule("[Si]OP(=O)(O)O[Si]")
    hits = _by_id(detect_proto_genes(evaluation))

    assert hits["GENE_P_REPAIR"].present is True
    assert "REPAIR" in hits["GENE_P_REPAIR"].functions
