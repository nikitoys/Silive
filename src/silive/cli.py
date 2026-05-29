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
from .hypothesis_layer import default_hypothesis_inputs, write_hypothesis_report
from .model import ALL_GENES, SimulationConfig, compare_gene_sets, simulate
from .niche_search import format_niche_ranking, run_niche_search, write_niche_search_outputs
from .plot import SUPPORTED_METRICS, plot_phase_map, write_multiple_plots
from .proto_genes import detect_proto_genes, format_rdkit_gene_scorecard, proto_gene_summary
from .proto_genome import evaluate_proto_genome, format_proto_genome_evaluation, format_rdkit_genome_scorecard
from .proto_gene_lineage import (
    ProtoGeneLineageConfig,
    format_proto_gene_summary,
    run_and_write_proto_gene_lineage_search,
)
from .rdkit_chemistry import RDKitEvaluation, RDKitUnavailableError, evaluate_rdkit_molecule, format_rdkit_scorecard
from .rdkit_cli import run_rdkit_evaluate_text
from .rdkit_search import format_rdkit_search_table, search_rdkit_candidates, write_rdkit_search_csv
from .reaction_simulator import (
    format_reaction_results,
    format_reaction_search_table,
    reaction_search,
    simulate_reactions,
    write_reaction_search_csv,
)
from .study import run_repair_study, write_repair_study_outputs
from .evolutionary_search import (
    EvolutionConfig,
    format_evolution_summary,
    load_start_candidates,
    run_evolution,
    write_evolution_outputs,
)
from .sweep import SweepConfig, linspace, run_sweep, write_csv
from .symbolic_graph import (
    build_symbolic_graph,
    diff_symbolic_graphs,
    format_symbolic_graph_diff,
    format_symbolic_graph_summary,
    write_symbolic_graph_diff_json,
    write_symbolic_graph_json,
)


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


def _load_rdkit_evaluation(molecule: str):
    try:
        return evaluate_rdkit_molecule(molecule)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc


def run_rdkit_evaluate_command(args: argparse.Namespace) -> None:
    print(run_rdkit_evaluate_text(args.molecule))


def run_rdkit_gene_evaluate_text(molecule: str) -> str:
    return format_rdkit_gene_scorecard(_load_rdkit_evaluation(molecule))


def run_rdkit_gene_evaluate_command(args: argparse.Namespace) -> None:
    print(run_rdkit_gene_evaluate_text(args.molecule))


def run_rdkit_genome_evaluate_text(molecule: str) -> str:
    return format_rdkit_genome_scorecard(_load_rdkit_evaluation(molecule))


def run_rdkit_genome_evaluate_command(args: argparse.Namespace) -> None:
    print(run_rdkit_genome_evaluate_text(args.molecule))


def _format_rdkit_graph_evaluation(evaluation: RDKitEvaluation) -> str:
    graph = build_symbolic_graph(evaluation)
    gene_hits = detect_proto_genes(evaluation)
    genome = evaluate_proto_genome(gene_hits, evaluation)
    return (
        format_rdkit_scorecard(evaluation)
        + "\n\n"
        + format_symbolic_graph_summary(graph)
        + "\n\n"
        + proto_gene_summary(gene_hits)
        + "\n\n"
        + format_proto_genome_evaluation(genome)
    )


def run_rdkit_graph_evaluate_text(molecule: str) -> str:
    return _format_rdkit_graph_evaluation(_load_rdkit_evaluation(molecule))


def run_rdkit_graph_evaluate_command(args: argparse.Namespace) -> None:
    evaluation = _load_rdkit_evaluation(args.molecule)
    graph = build_symbolic_graph(evaluation)
    json_output = getattr(args, "json_output", None)
    if json_output:
        write_symbolic_graph_json(graph, json_output)
    print(_format_rdkit_graph_evaluation(evaluation))
    if json_output:
        print(f"\nwrote symbolic graph JSON to {json_output}")


def run_rdkit_graph_diff_text(parent_molecule: str, child_molecule: str) -> str:
    parent_graph = build_symbolic_graph(_load_rdkit_evaluation(parent_molecule))
    child_graph = build_symbolic_graph(_load_rdkit_evaluation(child_molecule))
    return format_symbolic_graph_diff(diff_symbolic_graphs(parent_graph, child_graph))


def run_rdkit_graph_diff_command(args: argparse.Namespace) -> None:
    parent_graph = build_symbolic_graph(_load_rdkit_evaluation(args.parent_molecule))
    child_graph = build_symbolic_graph(_load_rdkit_evaluation(args.child_molecule))
    diff = diff_symbolic_graphs(parent_graph, child_graph)
    json_output = getattr(args, "json_output", None)
    if json_output:
        write_symbolic_graph_diff_json(diff, json_output)
    print(format_symbolic_graph_diff(diff))
    if json_output:
        print(f"\nwrote symbolic graph diff JSON to {json_output}")


def run_rdkit_search_command(args: argparse.Namespace) -> str:
    try:
        candidates = search_rdkit_candidates(args.input, top=args.top)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    write_rdkit_search_csv(candidates, args.output)
    return format_rdkit_search_table(candidates) + f"\n\nwrote {len(candidates)} candidates to {args.output}"


def run_rdkit_search_cli_command(args: argparse.Namespace) -> None:
    print(run_rdkit_search_command(args))


def run_reaction_simulate_text(molecule: str, top: int = 10) -> str:
    evaluation = _load_rdkit_evaluation(molecule)
    return format_reaction_results(simulate_reactions(evaluation), top=top)


def run_reaction_simulate_command(args: argparse.Namespace) -> None:
    print(run_reaction_simulate_text(args.molecule, top=args.top))


def run_reaction_search_text(input_path: str, output: str, top: int = 20) -> str:
    try:
        rows = reaction_search(input_path, top=top)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    write_reaction_search_csv(rows, output)
    return format_reaction_search_table(rows) + f"\n\nwrote {len(rows)} reaction opportunities to {output}"


def run_reaction_search_command(args: argparse.Namespace) -> None:
    print(run_reaction_search_text(args.input, args.output, top=args.top))


def run_evolve_command(args: argparse.Namespace) -> str:
    start_candidates = load_start_candidates(args.input)
    config = EvolutionConfig(
        generations=args.generations,
        population_size=args.population_size,
        elite_size=args.elite_size,
        mutation_rate=args.mutation_rate,
        reaction_rate=args.reaction_rate,
        seed=args.seed,
        start_candidates=start_candidates,
    )
    try:
        run = run_evolution(config)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    write_evolution_outputs(run, args.output_dir)
    return format_evolution_summary(run) + f"\n\nwrote outputs to {args.output_dir}"


def run_evolve_cli_command(args: argparse.Namespace) -> None:
    print(run_evolve_command(args))




def run_hypothesis_report_command(args: argparse.Namespace) -> None:
    inputs = default_hypothesis_inputs(
        args.evolution_dir,
        args.output,
        rdkit_search_csv=args.rdkit_search_csv,
        reaction_search_csv=args.reaction_search_csv,
    )
    write_hypothesis_report(inputs)
    print(f"wrote hypothesis report to {inputs.output}")

def run_proto_gene_search_command(args: argparse.Namespace) -> None:
    config = ProtoGeneLineageConfig(
        mode=args.mode,
        generations=args.generations,
        population_size=args.population_size,
        rounds=args.rounds,
        runs=args.runs,
        seed=args.seed,
        environment=args.environment,
        input_path=args.input,
        seed_chain=args.seed_chain,
        retention_threshold=args.retention_threshold,
    )
    try:
        run, paths = run_and_write_proto_gene_lineage_search(config, args.output_dir)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc

    print(format_proto_gene_summary(run))
    print(f"\nwrote proto_gene_candidates_csv to {paths.proto_gene_candidates_csv}")
    print(f"wrote lineage_history_csv to {paths.lineage_history_csv}")
    print(f"wrote proto_gene_summary_json to {paths.proto_gene_summary_json}")
    print(f"wrote best_proto_gene_json to {paths.best_proto_gene_json}")
    print(f"wrote proto_gene_report_md to {paths.proto_gene_report_md}")


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


def _add_rdkit_molecule_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("molecule", help="SMILES/SMARTS such as [Si]-O-[Si]-O-[Fe]-O-[Si]")


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

    rdkit_evaluate_parser = subparsers.add_parser("rdkit-evaluate", help="evaluate an RDKit SMILES/SMARTS molecule")
    _add_rdkit_molecule_argument(rdkit_evaluate_parser)
    rdkit_evaluate_parser.set_defaults(func=run_rdkit_evaluate_command)

    rdkit_gene_parser = subparsers.add_parser("rdkit-gene-evaluate", help="detect proto-genes in an RDKit molecule")
    _add_rdkit_molecule_argument(rdkit_gene_parser)
    rdkit_gene_parser.set_defaults(func=run_rdkit_gene_evaluate_command)

    rdkit_genome_parser = subparsers.add_parser("rdkit-genome-evaluate", help="evaluate proto-genome coverage")
    _add_rdkit_molecule_argument(rdkit_genome_parser)
    rdkit_genome_parser.set_defaults(func=run_rdkit_genome_evaluate_command)

    rdkit_graph_parser = subparsers.add_parser(
        "rdkit-graph-evaluate",
        help="evaluate RDKit molecule, symbolic graph, proto-genes, and proto-genome",
    )
    _add_rdkit_molecule_argument(rdkit_graph_parser)
    rdkit_graph_parser.add_argument(
        "--json-output",
        default=None,
        help="optional path for machine-readable symbolic graph JSON",
    )
    rdkit_graph_parser.set_defaults(func=run_rdkit_graph_evaluate_command)

    rdkit_graph_diff_parser = subparsers.add_parser(
        "rdkit-graph-diff",
        help="compare symbolic graph properties between parent and mutated RDKit molecules",
    )
    rdkit_graph_diff_parser.add_argument("parent_molecule", help="parent SMILES/SMARTS candidate")
    rdkit_graph_diff_parser.add_argument("child_molecule", help="mutated child SMILES/SMARTS candidate")
    rdkit_graph_diff_parser.add_argument(
        "--json-output",
        default=None,
        help="optional path for machine-readable symbolic graph diff JSON",
    )
    rdkit_graph_diff_parser.set_defaults(func=run_rdkit_graph_diff_command)

    rdkit_search_parser = subparsers.add_parser("rdkit-search", help="rank RDKit SMILES/SMARTS candidates from a file")
    rdkit_search_parser.add_argument("input", help=".smi/.txt file with one SMILES/SMARTS candidate per line")
    rdkit_search_parser.add_argument("--output", default="outputs/rdkit_search.csv")
    rdkit_search_parser.add_argument("--top", type=int, default=20)
    rdkit_search_parser.set_defaults(func=run_rdkit_search_cli_command)

    reaction_simulate_parser = subparsers.add_parser(
        "rdkit-reaction-simulate",
        help="simulate abstract reaction opportunities for one RDKit candidate",
    )
    reaction_simulate_parser.add_argument("molecule", help="SMILES/SMARTS candidate")
    reaction_simulate_parser.add_argument("--top", type=int, default=10)
    reaction_simulate_parser.set_defaults(func=run_reaction_simulate_command)

    reaction_search_parser = subparsers.add_parser(
        "rdkit-reaction-search",
        help="rank abstract reaction opportunities for RDKit candidates from a file",
    )
    reaction_search_parser.add_argument("input", help=".smi/.txt file with one SMILES/SMARTS candidate per line")
    reaction_search_parser.add_argument("--output", default="outputs/reaction_search.csv")
    reaction_search_parser.add_argument("--top", type=int, default=20)
    reaction_search_parser.set_defaults(func=run_reaction_search_command)

    evolve_parser = subparsers.add_parser("rdkit-evolve", help="run abstract evolutionary motif search")
    evolve_parser.add_argument("input", nargs="?", default=None, help="optional .smi/.txt file with start candidates")
    evolve_parser.add_argument("--generations", type=int, default=20)
    evolve_parser.add_argument("--population-size", type=int, default=30)
    evolve_parser.add_argument("--elite-size", type=int, default=5)
    evolve_parser.add_argument("--mutation-rate", type=float, default=0.75)
    evolve_parser.add_argument("--reaction-rate", type=float, default=0.50)
    evolve_parser.add_argument("--output-dir", default="outputs/evolution")
    evolve_parser.add_argument("--seed", type=int, default=None)
    evolve_parser.set_defaults(func=run_evolve_cli_command)

    proto_gene_parser = subparsers.add_parser(
        "proto-gene-search",
        help="search abstract heritable silicon/mineral proto-gene motifs",
    )
    proto_gene_parser.add_argument("input", nargs="?", default=None, help="optional RDKit .smi/.txt input file")
    proto_gene_parser.add_argument("--mode", choices=("chain", "rdkit"), default="rdkit")
    proto_gene_parser.add_argument("--seed-chain", default=None, help="symbolic chain seed for --mode chain")
    proto_gene_parser.add_argument("--rounds", type=int, default=200)
    proto_gene_parser.add_argument("--generations", type=int, default=10)
    proto_gene_parser.add_argument("--population-size", type=int, default=20)
    proto_gene_parser.add_argument("--runs", type=int, default=10)
    proto_gene_parser.add_argument("--output-dir", default="outputs/proto_gene_search")
    proto_gene_parser.add_argument("--seed", type=int, default=None)
    proto_gene_parser.add_argument("--retention-threshold", type=float, default=0.60)
    _add_environment_argument(proto_gene_parser)
    proto_gene_parser.set_defaults(func=run_proto_gene_search_command)

    hypothesis_parser = subparsers.add_parser(
        "hypothesis-report",
        help="write a Markdown hypothesis report from RDKit/evolution outputs",
    )
    hypothesis_parser.add_argument("evolution_dir", help="directory containing final_population.csv and summary.json")
    hypothesis_parser.add_argument("--output", default="outputs/hypotheses.md")
    hypothesis_parser.add_argument("--rdkit-search-csv", default=None, help="optional rdkit_search.csv path")
    hypothesis_parser.add_argument("--reaction-search-csv", default=None, help="optional reaction_search.csv path")
    hypothesis_parser.set_defaults(func=run_hypothesis_report_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
