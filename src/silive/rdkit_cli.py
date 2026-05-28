from __future__ import annotations

from .rdkit_chemistry import RDKitUnavailableError, evaluate_rdkit_molecule, format_rdkit_scorecard


def run_rdkit_evaluate_text(molecule: str) -> str:
    try:
        evaluation = evaluate_rdkit_molecule(molecule)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    return format_rdkit_scorecard(evaluation)
