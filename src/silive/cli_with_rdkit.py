from __future__ import annotations

import argparse
import sys

from . import cli as base_cli
from .rdkit_cli import run_rdkit_evaluate_text


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "rdkit-evaluate":
        parser = argparse.ArgumentParser(prog="silive rdkit-evaluate")
        parser.add_argument("molecule", help="SMILES/SMARTS such as [Si]-O-[Si]-O-[Fe]-O-[Si]")
        parsed = parser.parse_args(args[1:])
        print(run_rdkit_evaluate_text(parsed.molecule))
        return

    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *args]
        base_cli.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
