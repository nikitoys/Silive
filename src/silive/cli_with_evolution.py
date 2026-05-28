from __future__ import annotations

import argparse
import sys

from . import cli_with_reactions as previous_cli
from .evolutionary_search import (
    EvolutionConfig,
    format_evolution_summary,
    load_start_candidates,
    run_evolution,
    write_evolution_outputs,
)


def _parse_evolve(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="silive rdkit-evolve")
    parser.add_argument("input", nargs="?", default=None, help="optional .smi/.txt file with start candidates")
    parser.add_argument("--generations", type=int, default=20)
    parser.add_argument("--population-size", type=int, default=30)
    parser.add_argument("--elite-size", type=int, default=5)
    parser.add_argument("--mutation-rate", type=float, default=0.75)
    parser.add_argument("--reaction-rate", type=float, default=0.50)
    parser.add_argument("--output-dir", default="outputs/evolution")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args(args)


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
    run = run_evolution(config)
    write_evolution_outputs(run, args.output_dir)
    return format_evolution_summary(run) + f"\n\nwrote outputs to {args.output_dir}"


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "rdkit-evolve":
        parsed = _parse_evolve(args[1:])
        print(run_evolve_command(parsed))
        return
    previous_cli.main(args)


if __name__ == "__main__":
    main()
