from __future__ import annotations

import argparse
import sys

from . import cli as base_cli
from .proto_genes import format_rdkit_gene_scorecard
from .proto_genome import format_rdkit_genome_scorecard
from .rdkit_chemistry import RDKitUnavailableError, evaluate_rdkit_molecule
from .rdkit_cli import run_rdkit_evaluate_text
from .rdkit_search import format_rdkit_search_table, search_rdkit_candidates, write_rdkit_search_csv


def _parse_molecule_command(prog: str, args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("molecule", help="SMILES/SMARTS such as [Si]-O-[Si]-O-[Fe]-O-[Si]")
    return parser.parse_args(args)


def _parse_search_command(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="silive rdkit-search")
    parser.add_argument("input", help=".smi/.txt file with one SMILES/SMARTS candidate per line")
    parser.add_argument("--output", default="outputs/rdkit_search.csv")
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args(args)


def run_rdkit_gene_evaluate_text(molecule: str) -> str:
    try:
        evaluation = evaluate_rdkit_molecule(molecule)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    return format_rdkit_gene_scorecard(evaluation)


def run_rdkit_genome_evaluate_text(molecule: str) -> str:
    try:
        evaluation = evaluate_rdkit_molecule(molecule)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    return format_rdkit_genome_scorecard(evaluation)


def run_rdkit_search_command(args: argparse.Namespace) -> str:
    try:
        candidates = search_rdkit_candidates(args.input, top=args.top)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    write_rdkit_search_csv(candidates, args.output)
    return format_rdkit_search_table(candidates) + f"\n\nwrote {len(candidates)} candidates to {args.output}"


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "rdkit-evaluate":
        parsed = _parse_molecule_command("silive rdkit-evaluate", args[1:])
        print(run_rdkit_evaluate_text(parsed.molecule))
        return

    if args and args[0] == "rdkit-gene-evaluate":
        parsed = _parse_molecule_command("silive rdkit-gene-evaluate", args[1:])
        print(run_rdkit_gene_evaluate_text(parsed.molecule))
        return

    if args and args[0] == "rdkit-genome-evaluate":
        parsed = _parse_molecule_command("silive rdkit-genome-evaluate", args[1:])
        print(run_rdkit_genome_evaluate_text(parsed.molecule))
        return

    if args and args[0] == "rdkit-search":
        parsed = _parse_search_command(args[1:])
        print(run_rdkit_search_command(parsed))
        return

    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *args]
        base_cli.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
