import importlib.util

import pytest

from silive.cli import main


def test_proto_gene_search_chain_cli_writes_outputs(tmp_path, capsys) -> None:
    main(
        [
            "proto-gene-search",
            "--mode",
            "chain",
            "--seed-chain",
            "Si-O-Si-O-Fe-O-Si",
            "--rounds",
            "3",
            "--generations",
            "1",
            "--population-size",
            "2",
            "--runs",
            "1",
            "--output-dir",
            str(tmp_path),
            "--seed",
            "11",
        ]
    )

    output = capsys.readouterr().out

    assert "proto-gene lineage search" in output
    assert (tmp_path / "proto_gene_candidates.csv").exists()
    assert (tmp_path / "lineage_history.csv").exists()
    assert (tmp_path / "proto_gene_report.md").exists()


@pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")
def test_proto_gene_search_rdkit_cli_writes_outputs(tmp_path, capsys) -> None:
    input_path = tmp_path / "candidates.smi"
    input_path.write_text("[Si]O[Si] template\nnot_a_valid_smiles invalid\n", encoding="utf-8")

    main(
        [
            "proto-gene-search",
            str(input_path),
            "--mode",
            "rdkit",
            "--generations",
            "1",
            "--population-size",
            "2",
            "--output-dir",
            str(tmp_path),
            "--seed",
            "12",
        ]
    )

    output = capsys.readouterr().out

    assert "proto-gene lineage search" in output
    assert (tmp_path / "proto_gene_summary.json").exists()
    assert "safety" in (tmp_path / "proto_gene_summary.json").read_text(encoding="utf-8")
