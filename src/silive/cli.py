from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

from .chain_report import create_chain_report
from .chain_simulation import format_chain_simulation, simulate_chain
from .chemistry import (
    SUPPORTED_ENVIRONMENTS,
    evaluate_chain,
    format_scorecard,
    format_search_results,
    search_chains,
    write_chain_search_csv,
)
from .environment_sweep import (
    format_environment_ranking,
    run_environment_sweep,
    write_environment_sweep_outputs,
)
from .model import ALL_GENES, SimulationConfig, compare_gene_sets, simulate
from .niche_search import format_niche_ranking, run_niche_search, write_niche_search_outputs
from .plot import SUPPORTED_METRICS, plot_phase_map, write_multiple_plots
from .study import run_repair_study, write_repair_study_outputs
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


def _make_sweep_config(args: argparse.Namespace) -> SweepConfig:
    return SweepConfig(
        mutation_rates=linspace(args.mutation_start, args.mutation_stop, args.mutation_steps),
        shell_bonuses=linspace(args.shell_start, args.shell_stop, args.shell_steps),
        genes=frozenset(args.genes),
        generations=args.generations,
        runs=args.runs,
        population_limit=args.population_limit,
        start_population=args.start_population,
        start_sequence=args.sequence,
        gene_mutation_rate=args.gene_mutation_rate,
        seed=args.seed,
    )


def _write_sweep_outputs(args: argparse.Namespace, output: str | Path) -> list[dict]:
    rows = run_sweep(_make_sweep_config(args))
    write_csv(rows, output)
    return rows


def _print_zone_summary(rows: list[dict]) -> None:
    zones: dict[str, int] = {}
    for row in rows:
        zones[row["zone"]] = zones.get(row["zone"], 0) + 1

    print("zones:")
    for zone, count in sorted(zones.items()):
        print(f"  {zone}: {count}")


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
    rows = _write_sweep_outputs(args, args.output)
    print(f"wrote {len(rows)} phase-map rows to {args.output}")
    _print_zone_summary(rows)


def run_plot_command(args: argparse.Namespace) -> None:
    plot_phase_map(args.csv, args.output, metric=args.metric, title=args.title)
    print(f"wrote {args.metric} plot to {args.output}")


def run_lab_command(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "phase_map.csv"

    rows = _write_sweep_outputs(args, csv_path)
    plot_paths = write_multiple_plots(
        csv_path,
        output_dir,
        metrics=("survival_rate", "code_preservation_rate"),
    )

    print(f"wrote {len(rows)} phase-map rows to {csv_path}")
    for path in plot_paths:
        print(f"wrote plot to {path}")
    _print_zone_summary(rows)


def run_repair_study_command(args: argparse.Namespace) -> None:
    config = _make_sweep_config(args)
    result = run_repair_study(config)
    paths = write_repair_study_outputs(result, args.output_dir)

    for label, path in paths.items():
        print(f"wrote {label} to {path}")

    print("summary:")
    for key, value in result.summary.items():
        print(f"  {key}: {value}")


def run_evaluate_chain_command(args: argparse.Namespace) -> None:
    evaluation = evaluate_chain(args.chain, environment=args.environment)
    print(format_scorecard(evaluation))


def run_search_chain_command(args: argparse.Namespace) -> None:
    results = search_chains(
        args.seed_chain,
        rounds=args.rounds,
        top_n=args.top,
        seed=args.random_seed,
        max_length=args.max_length,
        environment=args.environment,
    )
    write_chain_search_csv(results, args.output)
    print(format_search_results(results))
    print(f"\nwrote {len(results)} candidates to {args.output}")


def run_chain_simulate_command(args: argparse.Namespace) -> None:
    result = simulate_chain(
        args.chain,
        environment=args.environment,
        generations=args.generations,
        runs=args.runs,
        seed=args.seed,
        start_sequence=args.sequence,
        population_limit=args.population_limit,
        start_population=args.start_population,
        base_mutation_rate=args.mutation_rate,
        gene_mutation_rate=args.gene_mutation_rate,
        shell_survival_bonus=args.shell_bonus,
    )
    print(format_chain_simulation(result))


def run_chain_report_command(args: argparse.Namespace) -> None:
    _, paths = create_chain_report(
        args.chain,
        output_dir=args.output_dir,
        environment=args.environment,
        generations=args.generations,
        runs=args.runs,
        seed=args.seed,
        start_sequence=args.sequence,
        population_limit=args.population_limit,
        start_population=args.start_population,
        base_mutation_rate=args.mutation_rate,
        gene_mutation_rate=args.gene_mutation_rate,
        shell_survival_bonus=args.shell_bonus,
    )
    print(f"wrote chain_score_json to {paths.chain_score_json}")
    print(f"wrote chain_score_csv to {paths.chain_score_csv}")
    print(f"wrote chain_report_txt to {paths.chain_report_txt}")
    print(f"wrote simulation_summary_csv to {paths.simulation_summary_csv}")


def run_environment_sweep_command(args: argparse.Namespace) -> None:
    sweep = run_environment_sweep(
        args.chain,
        generations=args.generations,
        runs=args.runs,
        seed=args.seed,
        start_sequence=args.sequence,
        population_limit=args.population_limit,
        start_population=args.start_population,
        base_mutation_rate=args.mutation_rate,
        gene_mutation_rate=args.gene_mutation_rate,
        shell_survival_bonus=args.shell_bonus,
    )
    paths = write_environment_sweep_outputs(sweep, args.output_dir)
    print(format_environment_ranking(sweep))
    print(f"\nwrote environment_sweep_csv to {paths.environment_sweep_csv}")
    print(f"wrote environment_sweep_json to {paths.environment_sweep_json}")


def run_niche_search_command(args: argparse.Namespace) -> None:
    search = run_niche_search(
        args.seed_chain,
        rounds=args.rounds,
        top_n=args.top,
        seed=args.random_seed,
        max_length=args.max_length,
        generations=args.generations,
        runs=args.runs,
        start_sequence=args.sequence,
        population_limit=args.population_limit,
        start_population=args.start_population,
        base_mutation_rate=args.mutation_rate,
        gene_mutation_rate=args.gene_mutation_rate,
        shell_survival_bonus=args.shell_bonus,
    )
    paths = write_niche_search_outputs(search, args.output_dir)
    print(format_niche_ranking(search))
    print(f"\nwrote niche_search_csv to {paths.niche_search_csv}")
    print(f"wrote niche_search_json to {paths.niche_search_json}")


def _add_sweep_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mutation-start", type=float, default=0.0)
    parser.add_argument("--mutation-stop", type=float, default=0.30)
    parser.add_argument("--mutation-steps", type=int, default=16)
    parser.add_argument("--shell-start", type=float, default=0.0)
    parser.add_argument("--shell-stop", type=float, default=0.40)
    parser.add_argument("--shell-steps", type=int, default=16)
    parser.add_argument("--genes", nargs="+", default=["POL", "SEP", "SHELL", "REPAIR"], choices=ALL_GENES)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--population-limit", type=int, default=100)
    parser.add_argument("--start-population", type=int, default=10)
    parser.add_argument("--sequence", default="ABABAB")
    parser.add_argument("--gene-mutation-rate", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=None)


def _add_environment_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--environment",
        choices=SUPPORTED_ENVIRONMENTS,
        default=None,
        help="symbolic environment modifier",
    )


def _add_chain_simulation_arguments(parser: argparse.ArgumentParser, *, include_seed: bool = True) -> None:
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--runs", type=int, default=20)
    if include_seed:
        parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--sequence", default="ABABAB")
    parser.add_argument("--population-limit", type=int, default=100)
    parser.add_argument("--start-population", type=int, default=10)
    parser.add_argument("--mutation-rate", type=float, default=0.08)
    parser.add_argument("--gene-mutation-rate", type=float, default=0.03)
    parser.add_argument("--shell-bonus", type=float, default=0.15)


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
    _add_sweep_arguments(sweep_parser)
    sweep_parser.add_argument("--output", default="phase_map.csv")
    sweep_parser.set_defaults(func=run_sweep_command)

    plot_parser = subparsers.add_parser("plot", help="plot a phase-map CSV as a PNG heatmap")
    plot_parser.add_argument("csv")
    plot_parser.add_argument("--metric", choices=SUPPORTED_METRICS, default="survival_rate")
    plot_parser.add_argument("--output", default="phase_map.png")
    plot_parser.add_argument("--title", default=None)
    plot_parser.set_defaults(func=run_plot_command)

    lab_parser = subparsers.add_parser("lab", help="run sweep and create default phase-map plots")
    _add_sweep_arguments(lab_parser)
    lab_parser.add_argument("--output-dir", default="outputs")
    lab_parser.set_defaults(func=run_lab_command)

    repair_study_parser = subparsers.add_parser(
        "repair-study",
        help="compare phase maps with and without REPAIR",
    )
    _add_sweep_arguments(repair_study_parser)
    repair_study_parser.add_argument("--output-dir", default="outputs/repair_study")
    repair_study_parser.set_defaults(func=run_repair_study_command)

    evaluate_chain_parser = subparsers.add_parser(
        "evaluate-chain",
        help="evaluate a concrete symbolic element chain against proto-life functions",
    )
    evaluate_chain_parser.add_argument("chain", help="element chain such as Si-O-Si-O-Fe-O-Si")
    _add_environment_argument(evaluate_chain_parser)
    evaluate_chain_parser.set_defaults(func=run_evaluate_chain_command)

    search_chain_parser = subparsers.add_parser(
        "search-chain",
        help="mutate a symbolic element chain and search for better proto-life candidates",
    )
    search_chain_parser.add_argument("--seed", dest="seed_chain", required=True, help="seed chain such as Si-O-Si-O-Fe-O-Si")
    search_chain_parser.add_argument("--rounds", type=int, default=500)
    search_chain_parser.add_argument("--top", type=int, default=10)
    search_chain_parser.add_argument("--random-seed", type=int, default=None)
    search_chain_parser.add_argument("--max-length", type=int, default=16)
    search_chain_parser.add_argument("--output", default="chain_search.csv")
    _add_environment_argument(search_chain_parser)
    search_chain_parser.set_defaults(func=run_search_chain_command)

    chain_simulate_parser = subparsers.add_parser(
        "chain-simulate",
        help="evaluate a symbolic chain and simulate its predicted proto-life functions",
    )
    chain_simulate_parser.add_argument("chain", help="element chain such as Si-O-Si-O-Fe-O-Si")
    _add_environment_argument(chain_simulate_parser)
    _add_chain_simulation_arguments(chain_simulate_parser)
    chain_simulate_parser.set_defaults(func=run_chain_simulate_command)

    chain_report_parser = subparsers.add_parser(
        "chain-report",
        help="write JSON/CSV/TXT report for one symbolic chain",
    )
    chain_report_parser.add_argument("chain", help="element chain such as Si-O-Si-O-Fe-O-Si")
    chain_report_parser.add_argument("--output-dir", default="outputs/chain_report")
    _add_environment_argument(chain_report_parser)
    _add_chain_simulation_arguments(chain_report_parser)
    chain_report_parser.set_defaults(func=run_chain_report_command)

    environment_sweep_parser = subparsers.add_parser(
        "environment-sweep",
        help="evaluate and simulate one symbolic chain across all environments",
    )
    environment_sweep_parser.add_argument("chain", help="element chain such as Si-O-Si-O-Fe-O-Si")
    environment_sweep_parser.add_argument("--output-dir", default="outputs/env_sweep")
    _add_chain_simulation_arguments(environment_sweep_parser)
    environment_sweep_parser.set_defaults(func=run_environment_sweep_command)

    niche_search_parser = subparsers.add_parser(
        "niche-search",
        help="search best chain + environment niches",
    )
    niche_search_parser.add_argument("--seed", dest="seed_chain", required=True, help="seed chain such as Si-O-Si-O-Fe-O-Si")
    niche_search_parser.add_argument("--output-dir", default="outputs/niche_search")
    niche_search_parser.add_argument("--rounds", type=int, default=100)
    niche_search_parser.add_argument("--top", type=int, default=10)
    niche_search_parser.add_argument("--random-seed", type=int, default=None)
    niche_search_parser.add_argument("--max-length", type=int, default=16)
    _add_chain_simulation_arguments(niche_search_parser, include_seed=False)
    niche_search_parser.set_defaults(func=run_niche_search_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
