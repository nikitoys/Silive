import csv
import json

from silive.chain_report import chain_score_dict, create_chain_report, format_chain_report, simulation_summary_dict


def test_chain_score_dict_contains_report_fields() -> None:
    result, _ = create_chain_report(
        "Si-O-Si-O-Fe-O-Si",
        output_dir="/tmp/silive-test-report-dict",
        environment="hydrothermal",
        generations=5,
        runs=2,
        seed=42,
    )

    score = chain_score_dict(result)

    assert score["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert score["environment"] == "hydrothermal"
    assert "properties" in score
    assert "function_scores" in score
    assert "predicted_functions" in score
    assert "missing_functions" in score
    assert "recommendations" in score
    assert "viability" in score


def test_simulation_summary_dict_contains_metrics() -> None:
    result, _ = create_chain_report(
        "Si-O-Si-O-Fe-O-Si",
        output_dir="/tmp/silive-test-report-summary",
        generations=5,
        runs=2,
        seed=42,
    )

    summary = simulation_summary_dict(result)

    assert summary["runs"] == 2
    assert summary["generations"] == 5
    assert 0.0 <= summary["survival_rate"] <= 1.0
    assert 0.0 <= summary["code_preservation_rate"] <= 1.0
    assert summary["avg_final_population"] >= 0.0


def test_create_chain_report_writes_all_outputs(tmp_path) -> None:
    result, paths = create_chain_report(
        "Si-O-Si-O-Fe-O-Si",
        output_dir=tmp_path,
        environment="hydrothermal",
        generations=5,
        runs=2,
        seed=42,
    )

    assert result.evaluation.environment == "hydrothermal"
    assert paths.chain_score_json.exists()
    assert paths.chain_score_csv.exists()
    assert paths.chain_report_txt.exists()
    assert paths.simulation_summary_csv.exists()

    payload = json.loads(paths.chain_score_json.read_text(encoding="utf-8"))
    assert payload["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert payload["environment"] == "hydrothermal"
    assert "properties" in payload
    assert "predicted_functions" in payload
    assert "missing_functions" in payload

    with paths.chain_score_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["chain"] == "Si-O-Si-O-Fe-O-Si"
    assert rows[0]["environment"] == "hydrothermal"
    assert rows[0]["viability"]

    with paths.simulation_summary_csv.open(newline="", encoding="utf-8") as handle:
        summary_rows = list(csv.DictReader(handle))
    assert len(summary_rows) == 1
    assert summary_rows[0]["survival_rate"]
    assert summary_rows[0]["code_preservation_rate"]


def test_format_chain_report_contains_required_sections(tmp_path) -> None:
    result, _ = create_chain_report(
        "Si-O-Si-O-Fe-O-Si",
        output_dir=tmp_path,
        generations=5,
        runs=2,
        seed=42,
    )

    report = format_chain_report(result)

    assert "Silive chain report" in report
    assert "Properties:" in report
    assert "Predicted functions:" in report
    assert "Missing functions:" in report
    assert "Viability class:" in report
    assert "Recommendations:" in report
    assert "simulation:" in report
