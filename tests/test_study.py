from silive.study import build_delta_rows, summarize_repair_effect


def test_build_delta_rows_compares_matching_grid_points() -> None:
    without_repair = [
        {
            "mutation_rate": 0.1,
            "shell_bonus": 0.2,
            "genes": "POL+SEP+SHELL",
            "survival_rate": 0.4,
            "code_preservation_rate": 0.3,
            "avg_final_stability": 0.6,
            "avg_best_fitness": 10.0,
            "zone": "unstable",
        }
    ]
    with_repair = [
        {
            "mutation_rate": 0.1,
            "shell_bonus": 0.2,
            "genes": "POL+REPAIR+SEP+SHELL",
            "survival_rate": 0.9,
            "code_preservation_rate": 0.8,
            "avg_final_stability": 0.85,
            "avg_best_fitness": 15.0,
            "zone": "proto_life",
        }
    ]

    rows = build_delta_rows(without_repair, with_repair)

    assert rows == [
        {
            "mutation_rate": 0.1,
            "shell_bonus": 0.2,
            "base_genes": "POL+SEP+SHELL",
            "repair_genes": "POL+REPAIR+SEP+SHELL",
            "base_zone": "unstable",
            "repair_zone": "proto_life",
            "survival_delta": 0.5,
            "code_preservation_delta": 0.5,
            "avg_final_stability_delta": 0.25,
            "avg_best_fitness_delta": 5.0,
            "zone_improvement": 2,
        }
    ]


def test_summarize_repair_effect_counts_positive_changes() -> None:
    rows = [
        {
            "survival_delta": 0.5,
            "code_preservation_delta": 0.2,
            "zone_improvement": 1,
        },
        {
            "survival_delta": -0.1,
            "code_preservation_delta": 0.0,
            "zone_improvement": 0,
        },
    ]

    summary = summarize_repair_effect(rows)

    assert summary["points"] == 2
    assert summary["positive_survival_points"] == 1
    assert summary["positive_code_points"] == 1
    assert summary["improved_zone_points"] == 1
    assert summary["avg_survival_delta"] == 0.2
    assert summary["avg_code_preservation_delta"] == 0.1
    assert summary["max_survival_delta"] == 0.5
