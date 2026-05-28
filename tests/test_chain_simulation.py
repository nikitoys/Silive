import pytest

from silive.chain_simulation import format_chain_simulation, simulate_chain


def test_simulate_chain_uses_predicted_functions() -> None:
    result = simulate_chain(
        "Si-O-Si-O-Fe-O-Si",
        generations=5,
        runs=3,
        seed=42,
    )

    assert result.evaluation.chain == ("Si", "O", "Si", "O", "Fe", "O", "Si")
    assert result.genes == tuple(sorted(result.evaluation.predicted_functions))
    assert result.runs == 3
    assert result.generations == 5


def test_simulate_chain_passes_environment_to_evaluation() -> None:
    result = simulate_chain(
        "Si-O-Si-O-Fe-O-Si",
        environment="hydrothermal",
        generations=5,
        runs=2,
        seed=42,
    )

    assert result.evaluation.environment == "hydrothermal"
    assert result.genes == tuple(sorted(result.evaluation.predicted_functions))


def test_simulate_chain_returns_aggregate_metrics() -> None:
    result = simulate_chain(
        "Si-O-Si-O-Fe-O-Si",
        generations=5,
        runs=3,
        seed=42,
    )

    assert 0.0 <= result.survival_rate <= 1.0
    assert 0.0 <= result.code_preservation_rate <= 1.0
    assert result.avg_final_population >= 0.0
    assert result.avg_final_stability >= 0.0
    assert result.avg_best_fitness >= 0.0


def test_simulate_chain_rejects_invalid_runs_and_generations() -> None:
    with pytest.raises(ValueError, match="runs must be positive"):
        simulate_chain("Si-O-Si", runs=0)

    with pytest.raises(ValueError, match="generations must be positive"):
        simulate_chain("Si-O-Si", generations=0)


def test_format_chain_simulation_contains_bridge_fields() -> None:
    result = simulate_chain(
        "Si-O-Si-O-Fe-O-Si",
        environment="hydrothermal",
        generations=5,
        runs=2,
        seed=42,
    )
    text = format_chain_simulation(result)

    assert "chain: Si-O-Si-O-Fe-O-Si" in text
    assert "environment: hydrothermal" in text
    assert "predicted functions:" in text
    assert "missing functions:" in text
    assert "simulation:" in text
    assert "survival_rate:" in text
    assert "code_preservation_rate:" in text
