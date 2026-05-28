from silive.model import ProtoLife, SimulationConfig, compare_gene_sets, simulate


def test_ab_pair_is_more_stable_than_ad_pair() -> None:
    organism = ProtoLife(sequence="AB", genes=set())

    assert organism.pair_stability("A", "B") > organism.pair_stability("A", "D")


def test_shell_increases_survival_chance() -> None:
    bare = ProtoLife(sequence="ABABAB", genes=set())
    shelled = ProtoLife(sequence="ABABAB", genes={"SHELL"})

    assert shelled.survival_chance() >= bare.survival_chance()


def test_pol_increases_copy_probability() -> None:
    slow = ProtoLife(sequence="ABABAB", genes=set())
    fast = ProtoLife(sequence="ABABAB", genes={"POL"})

    assert fast.copy_probability() > slow.copy_probability()


def test_repair_lowers_mutation_rate() -> None:
    raw = ProtoLife(sequence="ABABAB", genes=set())
    repaired = ProtoLife(sequence="ABABAB", genes={"REPAIR"})

    assert repaired.mutation_rate() < raw.mutation_rate()


def test_simulation_is_reproducible_with_seed() -> None:
    config = SimulationConfig(generations=10, seed=42)

    _, first_history = simulate(config)
    _, second_history = simulate(config)

    assert first_history == second_history


def test_compare_gene_sets_returns_ranked_rows() -> None:
    rows = compare_gene_sets(
        [{"POL", "SEP", "SHELL"}, {"POL"}],
        generations=5,
        runs=2,
        seed=123,
    )

    assert len(rows) == 2
    assert all("survival_rate" in row for row in rows)
