from silive.model import (
    CAT_WEAK_PAIR_BONUS,
    NO_SEP_SEPARATION_CHANCE,
    SHELL_SURVIVAL_BONUS,
    ProtoLife,
    SimulationConfig,
    compare_gene_sets,
    simulate,
)


def test_ab_pair_is_more_stable_than_ad_pair() -> None:
    organism = ProtoLife(sequence="AB", genes=set())

    assert organism.pair_stability("A", "B") > organism.pair_stability("A", "D")


def test_shell_adds_survival_bonus_without_overpowering() -> None:
    bare = ProtoLife(sequence="ADADAD", genes=set())
    shelled = ProtoLife(sequence="ADADAD", genes={"SHELL"})

    assert shelled.survival_chance() == bare.survival_chance() + SHELL_SURVIVAL_BONUS
    assert shelled.survival_chance() < bare.survival_chance() * 2


def test_cat_only_slightly_stabilizes_weak_pairs() -> None:
    raw = ProtoLife(sequence="AD", genes=set())
    catalyzed = ProtoLife(sequence="AD", genes={"CAT"})

    assert catalyzed.pair_stability("A", "D") == raw.pair_stability("A", "D") + CAT_WEAK_PAIR_BONUS


def test_sep_is_critical_for_separation() -> None:
    no_sep = ProtoLife(sequence="ABABAB", genes=set())
    with_sep = ProtoLife(sequence="ABABAB", genes={"SEP"})

    assert no_sep.separation_chance() == NO_SEP_SEPARATION_CHANCE
    assert with_sep.separation_chance() > no_sep.separation_chance() * 10


def test_pol_increases_copy_probability_but_has_energy_cost() -> None:
    slow = ProtoLife(sequence="ABABAB", genes=set())
    fast = ProtoLife(sequence="ABABAB", genes={"POL"})

    assert fast.copy_probability() > slow.copy_probability()
    assert fast.copy_energy_cost() > slow.copy_energy_cost()


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
