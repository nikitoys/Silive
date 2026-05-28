import csv

from silive.sweep import SweepConfig, classify_zone, linspace, run_sweep, write_csv


def test_linspace_includes_start_and_stop() -> None:
    assert linspace(0.0, 0.3, 4) == [0.0, 0.1, 0.2, 0.3]


def test_linspace_rejects_non_positive_steps() -> None:
    try:
        linspace(0.0, 1.0, 0)
    except ValueError as error:
        assert "steps" in str(error)
    else:
        raise AssertionError("linspace should reject non-positive steps")


def test_classify_zone_detects_dead_and_stable_life() -> None:
    assert classify_zone(0.0, 0.0, 0.0) == "dead"
    assert classify_zone(1.0, 0.95, 0.90) == "stable_life"


def test_run_sweep_returns_one_row_per_grid_point() -> None:
    rows = run_sweep(
        SweepConfig(
            mutation_rates=[0.0, 0.1],
            shell_bonuses=[0.0, 0.2],
            genes=frozenset({"POL", "SEP", "SHELL"}),
            generations=5,
            runs=2,
            seed=123,
        )
    )

    assert len(rows) == 4
    assert all("survival_rate" in row for row in rows)
    assert all("code_preservation_rate" in row for row in rows)
    assert all("zone" in row for row in rows)


def test_write_csv_creates_phase_map_file(tmp_path) -> None:
    rows = [
        {
            "mutation_rate": 0.0,
            "shell_bonus": 0.1,
            "genes": "POL+SEP+SHELL",
            "runs": 1,
            "generations": 5,
            "survival_rate": 1.0,
            "code_preservation_rate": 1.0,
            "avg_final_population": 10.0,
            "avg_final_stability": 0.9,
            "avg_best_fitness": 10.0,
            "zone": "stable_life",
        }
    ]
    output = tmp_path / "phase_map.csv"

    write_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as handle:
        loaded = list(csv.DictReader(handle))

    assert loaded[0]["zone"] == "stable_life"
    assert loaded[0]["genes"] == "POL+SEP+SHELL"
