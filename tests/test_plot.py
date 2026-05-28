import csv

from silive.plot import make_phase_grid, read_phase_map


def test_read_phase_map_converts_numeric_columns(tmp_path) -> None:
    csv_path = tmp_path / "phase_map.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "mutation_rate",
                "shell_bonus",
                "genes",
                "runs",
                "generations",
                "survival_rate",
                "code_preservation_rate",
                "avg_final_population",
                "avg_final_stability",
                "avg_best_fitness",
                "zone",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "mutation_rate": "0.1",
                "shell_bonus": "0.2",
                "genes": "POL+SEP+SHELL",
                "runs": "3",
                "generations": "10",
                "survival_rate": "1.0",
                "code_preservation_rate": "0.8",
                "avg_final_population": "42",
                "avg_final_stability": "0.9",
                "avg_best_fitness": "12.5",
                "zone": "proto_life",
            }
        )

    rows = read_phase_map(csv_path)

    assert rows[0]["mutation_rate"] == 0.1
    assert rows[0]["shell_bonus"] == 0.2
    assert rows[0]["runs"] == 3
    assert rows[0]["survival_rate"] == 1.0


def test_make_phase_grid_orders_axes_and_values() -> None:
    rows = [
        {"mutation_rate": 0.1, "shell_bonus": 0.2, "survival_rate": 0.5},
        {"mutation_rate": 0.0, "shell_bonus": 0.2, "survival_rate": 0.7},
        {"mutation_rate": 0.1, "shell_bonus": 0.0, "survival_rate": 0.2},
        {"mutation_rate": 0.0, "shell_bonus": 0.0, "survival_rate": 0.9},
    ]

    grid = make_phase_grid(rows, "survival_rate")

    assert grid.mutation_rates == [0.0, 0.1]
    assert grid.shell_bonuses == [0.0, 0.2]
    assert grid.values == [[0.9, 0.2], [0.7, 0.5]]


def test_make_phase_grid_rejects_unknown_metric() -> None:
    try:
        make_phase_grid([{"mutation_rate": 0.0, "shell_bonus": 0.0}], "unknown")
    except ValueError as error:
        assert "unsupported metric" in str(error)
    else:
        raise AssertionError("unknown metric should be rejected")
