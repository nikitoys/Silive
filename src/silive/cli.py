from __future__ import annotations

import argparse
from itertools import combinations

from .model import ALL_GENES, SimulationConfig, compare_gene_sets, simulate
from .sweep import SweepConfig, linspace, run_sweep, write_csv


def _print_generation(record: dict) -> None:
    if record.get("extinct"):
        print(f"gen={record['generation']:03d} | population extinct")
        return

    print(
        f"gen={record['generation']:03d} | "
        f"pop={record['population']:03d} | "
        f"best={record['best_sequence']} | "
        f"genes={list(record['best_genes'])} | "
        f"stab={record['avg_stability']:.3f} | "
        f"fit={record['best_fitness']:.2f}"
    )


def run_simulate(args: argparse.Namespace) -> None:
    population, history = simulate(
        SimulationConfig(
            generations=args.generations,
            population_limit=args.population_limit,
            start_population=args.start_population,
            start_sequence=args.sequence,
            start_genes=frozenset(args.genes),
            base_mutation_rate=args.mutation_rate,
            gene_mutation_rate=args.gene_mutation_rate,
            shell_survival_bonus=args.shell_bonus,
            seed=args.seed,
        )
    )

    for record in history:
        _print_generation(record)

    if population:
        best = population[0]
        print("\nBest organism")
        print(f"sequence: {best.sequence}")
        print(f"genes:    {sorted(best.genes)}")
        print(f"energy:   {best.energy:.3f}")
        print(f"fitness:  {best.fitness():.3f}")
    else:
        print("\nResult: extinction")


def default_gene_sets() -> list[set[str]]:
    candidates: list[set[str]] = []
    for size in range(1, len(ALL_GENES) + 1):
        for combo in combinations(ALL_GENES, size):
            candidates.append(set(combo))
    return candidates


def run_compare(args: argparse.Namespace) -> None:
    results = compare_gene_sets(
        default_gene_sets(),
        generations=args.generations,
        runs=args.runs,
        seed=args.seed,
        base_mutation_rate=args.mutation_rate,
        shell_survival_bonus=args.shell_bonus,
    )

    print("genes,survival_rate,avg_final_population,avg_final_stability,avg_best_fitness")
    for row in results:
        genes = "+".join(row["genes"])
        print(
            f"{genes},{row['survival_rate']:.3f},"
            f"{row['avg_final_population']:.3f},"
            f"{row['avg_final_stability']:.3f},"
            f"{row['avg_best_fitness']:.3f}"
        )


def run_sweep_command(args: argparse.Namespace) -> None:
    mutation_rates = linspace(args.mutation_start, args.mutation_stop, args.mutation_steps)
    shell_bonuses = linspace(args.shell_start, args.shell_stop, args.shell_steps)
    rows = run_sweep(
        SweepConfig(
            mutation_rates=mutation_rates,
            shell_bonuses=shell_bonuses,
            genes=frozenset(args.genes),
            generations=args.generations,
            runs=args.runs,
            population_limit=args.population_limit,
            start_population=args.start_population,
            start_sequence=args.sequence,
            gene_mutation_rate=args.gene_mutation_rate,
            seed=args.seed,
        )
    )
    write_csv(rows, args.output)

    zones: dict[str, int] = {}
    for row in rows:
        zones[row["zone"]] = zones.get(row["zone"], 0) + 1

    print(f"wrote {len(rows)} phase-map rows to {args.output}")
    print("zones:")
    for zone, count in sorted(zones.items()):
        print(f"  {zone}: {count}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="silive")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="run one proto-life simulation")
    simulate_parser.add_argument("--generations", type=int, default=100)
    simulate_parser.add_argument("--population-limit", type=int, default=100)
    simulate_parser.add_argument("--start-population", type=int, default=10)
    simulate_parser.add_argument("--sequence", default="ABABAB")
    simulate_parser.add_argument("--genes", nargs="+", default=["POL", "SEP", "SHELL"], choices=ALL_GENES)
    simulate_parser.add_argument("--mutation-rate", type=float, default=0.08)
    simulate_parser.add_argument("--gene-mutation-rate", type=float, default=0.03)
    simulate_parser.add_argument("--shell-bonus", type=float, default=0.15)
    simulate_parser.add_argument("--seed", type=int, default=None)
    simulate_parser.set_defaults(func=run_simulate)

    compare_parser = subparsers.add_parser("compare", help="compare all non-empty gene sets")
    compare_parser.add_argument("--generations", type=int, default=100)
    compare_parser.add_argument("--runs", type=int, default=20)
    compare_parser.add_argument("--mutation-rate", type=float, default=0.08)
    compare_parser.add_argument("--shell-bonus", type=float, default=0.15)
    compare_parser.add_argument("--seed", type=int, default=None)
    compare_parser.set_defaults(func=run_compare)

    sweep_parser = subparsers.add_parser("sweep", help="export a mutation/shell phase map as CSV")
    sweep_parser.add_argument("--mutation-start", type=float, default=0.0)
    sweep_parser.add_argument("--mutation-stop", type=float, default=0.30)
    sweep_parser.add_argument("--mutation-steps", type=int, default=16)
    sweep_parser.add_argument("--shell-start", type=float, default=0.0)
    sweep_parser.add_argument("--shell-stop", type=float, default=0.40)
    sweep_parser.add_argument("--shell-steps", type=int, default=16)
    sweep_parser.add_argument("--genes", nargs="+", default=["POL", "SEP", "SHELL", "REPAIR"], choices=ALL_GENES)
    sweep_parser.add_argument("--generations", type=int, default=100)
    sweep_parser.add_argument("--runs", type=int, default=20)
    sweep_parser.add_argument("--population-limit", type=int, default=100)
    sweep_parser.add_argument("--start-population", type=int, default=10)
    sweep_parser.add_argument("--sequence", default="ABABAB")
    sweep_parser.add_argument("--gene-mutation-rate", type=float, default=0.03)
    sweep_parser.add_argument("--seed", type=int, default=None)
    sweep_parser.add_argument("--output", default="phase_map.csv")
    sweep_parser.set_defaults(func=run_sweep_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
