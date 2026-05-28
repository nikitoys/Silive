from __future__ import annotations

import argparse
import sys

from . import cli_with_rdkit as previous_cli
from .rdkit_chemistry import RDKitUnavailableError, evaluate_rdkit_molecule
from .reaction_simulator import (
    format_reaction_results,
    format_reaction_search_table,
    reaction_search,
    simulate_reactions,
    write_reaction_search_csv,
)


def _load_evaluation(molecule: str):
    try:
        return evaluate_rdkit_molecule(molecule)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc


def _parse_reaction_simulate(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="silive rdkit-reaction-simulate")
    parser.add_argument("molecule", help="SMILES/SMARTS candidate")
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args(args)


def _parse_reaction_search(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="silive rdkit-reaction-search")
    parser.add_argument("input", help=".smi/.txt file with one SMILES/SMARTS candidate per line")
    parser.add_argument("--output", default="outputs/reaction_search.csv")
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args(args)


def run_reaction_simulate_text(molecule: str, top: int = 10) -> str:
    evaluation = _load_evaluation(molecule)
    return format_reaction_results(simulate_reactions(evaluation), top=top)


def run_reaction_search_text(input_path: str, output: str, top: int = 20) -> str:
    try:
        rows = reaction_search(input_path, top=top)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    write_reaction_search_csv(rows, output)
    return format_reaction_search_table(rows) + f"\n\nwrote {len(rows)} reaction opportunities to {output}"


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)

    if args and args[0] == "rdkit-reaction-simulate":
        parsed = _parse_reaction_simulate(args[1:])
        print(run_reaction_simulate_text(parsed.molecule, top=parsed.top))
        return

    if args and args[0] == "rdkit-reaction-search":
        parsed = _parse_reaction_search(args[1:])
        print(run_reaction_search_text(parsed.input, parsed.output, top=parsed.top))
        return

    previous_cli.main(args)


if __name__ == "__main__":
    main()
