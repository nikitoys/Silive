import importlib.util

import pytest

from silive.evolutionary_search import (
    EvolutionConfig,
    format_best_candidate,
    load_start_candidates,
    mutate_molecule,
    run_evolution,
    write_evolution_outputs,
)

pytestmark = pytest.mark.skipif(importlib.util.find_spec("rdkit") is None, reason="RDKit is not installed")


def test_load_start_candidates_from_file(tmp_path) -> None:
    path = tmp_path / "start.smi"
    path.write_text("# comment\n[Si]O[Si] template\n[Si]O[Si]O[Fe] iron\n", encoding="utf-8")

    assert load_start_candidates(path) == ("[Si]O[Si]", "[Si]O[Si]O[Fe]")


def test_mutate_molecule_returns_operator() -> None:
    import random

    mutated, operator = mutate_molecule("[Si]O[Si]", random.Random(1))

    assert operator
    assert isinstance(mutated, str)
    assert mutated


def test_run_evolution_produces_history_and_best_candidate() -> None:
    config = EvolutionConfig(
        generations=2,
        population_size=6,
        elite_size=2,
        mutation_rate=1.0,
        reaction_rate=0.5,
        seed=42,
        start_candidates=("[Si]O[Si]", "[Si]O[Si]O[Fe]"),
    )

    run = run_evolution(config)

    assert run.history
    assert len(run.final_population) == 6
    assert run.best_candidate.candidate_score >= run.final_population[-1].candidate_score
    assert run.summary["best_candidate_id"] == run.best_candidate.candidate_id
    assert "best evolutionary candidate" in format_best_candidate(run.best_candidate)


def test_write_evolution_outputs(tmp_path) -> None:
    config = EvolutionConfig(
        generations=1,
        population_size=4,
        elite_size=1,
        mutation_rate=1.0,
        reaction_rate=0.5,
        seed=7,
        start_candidates=("[Si]O[Si]", "[Si]O[Si]O[Fe]"),
    )
    run = run_evolution(config)
    write_evolution_outputs(run, tmp_path)

    assert (tmp_path / "evolution_history.csv").exists()
    assert (tmp_path / "final_population.csv").exists()
    assert (tmp_path / "best_candidate.txt").exists()
    assert (tmp_path / "summary.json").exists()
    assert "candidate_score" in (tmp_path / "final_population.csv").read_text(encoding="utf-8")
    assert "interpretation:" in (tmp_path / "best_candidate.txt").read_text(encoding="utf-8")
