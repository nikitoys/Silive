import importlib.util

import pytest

from silive.rdkit_search import (
    candidate_rows,
    parse_candidate_file,
    search_rdkit_candidates,
    write_rdkit_search_csv,
)

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def test_parse_candidate_file_ignores_comments_and_reads_names(tmp_path) -> None:
    path = tmp_path / "candidates.smi"
    path.write_text(
        "# comment\n\n[Si]O[Si] template\n[Fe]O\nnot_a_valid invalid\n",
        encoding="utf-8",
    )

    assert parse_candidate_file(path) == [
        ("[Si]O[Si]", "template"),
        ("[Fe]O", "candidate_4"),
        ("not_a_valid", "invalid"),
    ]


def test_search_rdkit_candidates_ranks_valid_candidates(tmp_path) -> None:
    path = tmp_path / "candidates.smi"
    path.write_text(
        "[Si]O[Si] template\n[Si]O[Si]O[Fe]OP(=O)(O)O[Si] combo\nnot_a_valid invalid\n",
        encoding="utf-8",
    )

    candidates = search_rdkit_candidates(path, top=3)

    assert len(candidates) == 3
    assert candidates[0].name == "combo"
    assert candidates[0].candidate_score >= candidates[1].candidate_score
    assert candidates[-1].name == "invalid"
    assert candidates[-1].candidate_score == 0.0


def test_candidate_rows_and_csv_output(tmp_path) -> None:
    path = tmp_path / "candidates.smi"
    output = tmp_path / "out" / "rdkit_search.csv"
    path.write_text("[Si]O[Si]O[Fe]OP(=O)(O)O[Si] combo\n", encoding="utf-8")

    candidates = search_rdkit_candidates(path, top=1)
    rows = candidate_rows(candidates)
    write_rdkit_search_csv(candidates, output)

    assert rows[0]["rank"] == "1"
    assert rows[0]["name"] == "combo"
    assert rows[0]["molecular_validity"] == "true"
    assert "TEMPLATE" in rows[0]["covered_functions"]
    assert "GENE_SI_TEMPLATE" in rows[0]["detected_genes"]
    assert output.exists()
    assert "rank,name,molecule,score" in output.read_text(encoding="utf-8")
