import json

from silive.cli import main
from silive.hypothesis_layer import default_hypothesis_inputs, write_hypothesis_report


def _write_fixture_outputs(tmp_path):
    evolution_dir = tmp_path / "evolution"
    evolution_dir.mkdir()
    (tmp_path / "rdkit_search.csv").write_text(
        "rank,name,molecule,score,rdkit_valid_score,symbolic_viability_score,molecular_validity,"
        "covered_functions,missing_functions,detected_genes,symbolic_chain,topology_tags,"
        "backbone_length,ring_count,fragment_count,network_score,branching_score,viability,risk_flags,preservation_reason\n"
        "1,combo,[Si]O[Si]O[Fe]OP(=O)(O)O[Si],0.800,1.000,0.700,true,"
        "TEMPLATE;CATALYZE,PROTECT;REPAIR,GENE_SI_TEMPLATE;GENE_FE_CATALYSIS,Si-O-Si,"
        "siloxane_rich;metal_center;phosphate_bridge,7.000,0.000,1.000,0.500,0.100,strong,,rdkit_validated\n",
        encoding="utf-8",
    )
    (tmp_path / "reaction_search.csv").write_text(
        "rank,name,molecule,reaction_id,reaction_name,before_score,after_score,delta_score,new_functions,risks,product_symbolic_description\n"
        "1,combo,[Si]O[Si],RXN_P_REPAIR_BRIDGE,repair,0.400,0.600,0.200,REPAIR,labile,[Si]O[Si] product\n",
        encoding="utf-8",
    )
    (evolution_dir / "final_population.csv").write_text(
        "candidate_id,parent_id,generation,molecule,symbolic_description,mutations,applied_reactions,"
        "candidate_score,rdkit_valid_score,symbolic_viability_score,genome_score,covered_functions,"
        "missing_functions,detected_genes,topology_tags,viability,risk_flags,preservation_reason\n"
        "g1_c1,g0_c1,1,[Si]O[Si],symbolic,add_si_o_unit,,0.500,1.000,0.450,0.400,"
        "TEMPLATE,PROTECT,GENE_SI_TEMPLATE,siloxane_rich,partial_candidate,,rdkit_validated\n",
        encoding="utf-8",
    )
    (evolution_dir / "best_candidate.txt").write_text("best evolutionary candidate\ncandidate_id: g1_c1\n", encoding="utf-8")
    (evolution_dir / "summary.json").write_text(
        json.dumps({"best_candidate_id": "g1_c1", "best_candidate_score": 0.5, "best_viability": "partial_candidate"}),
        encoding="utf-8",
    )
    return evolution_dir


def test_write_hypothesis_report_summarizes_outputs(tmp_path) -> None:
    evolution_dir = _write_fixture_outputs(tmp_path)
    output = tmp_path / "hypotheses.md"

    report = write_hypothesis_report(default_hypothesis_inputs(evolution_dir, output))

    assert output.exists()
    assert "# Silive hypothesis report" in report
    assert "## Top motif families" in report
    assert "GENE_SI_TEMPLATE: 2" in report
    assert "## Recurring bottlenecks and missing functions" in report
    assert "PROTECT" in report
    assert "## Material classes to compare" in report
    assert "Siloxane-rich Si/O scaffolds" in report
    assert "source_row=1" in report


def test_hypothesis_report_cli_writes_markdown(tmp_path, capsys) -> None:
    evolution_dir = _write_fixture_outputs(tmp_path)
    output = tmp_path / "reports" / "hypotheses.md"

    main(["hypothesis-report", str(evolution_dir), "--output", str(output)])

    captured = capsys.readouterr()
    assert "wrote hypothesis report" in captured.out
    assert output.exists()
    assert "## Reaction opportunities" in output.read_text(encoding="utf-8")
