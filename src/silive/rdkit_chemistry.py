from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .chemistry import ChainEvaluation, evaluate_chain, format_scorecard

MOTIF_NAMES = ("Si-O-Si", "Fe-O", "Ni-O", "P-O")


class RDKitUnavailableError(RuntimeError):
    """Raised when the optional RDKit dependency is not installed."""


@dataclass(frozen=True, slots=True)
class RDKitAtom:
    index: int
    symbol: str
    atomic_num: int
    formal_charge: int
    degree: int
    is_aromatic: bool


@dataclass(frozen=True, slots=True)
class RDKitBond:
    begin_atom_index: int
    end_atom_index: int
    begin_symbol: str
    end_symbol: str
    bond_type: str
    is_aromatic: bool
    is_conjugated: bool


@dataclass(frozen=True, slots=True)
class RDKitFragment:
    atom_indices: tuple[int, ...]
    elements: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RDKitEvaluation:
    source: str
    parser: str
    molecular_validity: bool
    parse_error: str | None
    atoms: tuple[RDKitAtom, ...]
    elements: tuple[str, ...]
    bonds: tuple[RDKitBond, ...]
    rings: tuple[tuple[int, ...], ...]
    fragments: tuple[RDKitFragment, ...]
    motifs: dict[str, int]
    symbolic_chain: tuple[str, ...]
    chain_evaluation: ChainEvaluation | None


def _load_rdkit() -> Any:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise RDKitUnavailableError(
            "RDKit is not installed. Install the optional dependency with: pip install -e .[chem]"
        ) from exc
    return Chem


def _parse_molecule(text: str) -> tuple[Any | None, str, str | None]:
    Chem = _load_rdkit()
    mol = Chem.MolFromSmiles(text)
    if mol is not None:
        return mol, "SMILES", None

    mol = Chem.MolFromSmarts(text)
    if mol is not None:
        return mol, "SMARTS", None

    return None, "none", "input could not be parsed as SMILES or SMARTS"


def _atoms(mol: Any) -> tuple[RDKitAtom, ...]:
    return tuple(
        RDKitAtom(
            index=atom.GetIdx(),
            symbol=atom.GetSymbol(),
            atomic_num=atom.GetAtomicNum(),
            formal_charge=atom.GetFormalCharge(),
            degree=atom.GetDegree(),
            is_aromatic=atom.GetIsAromatic(),
        )
        for atom in mol.GetAtoms()
    )


def _bonds(mol: Any) -> tuple[RDKitBond, ...]:
    return tuple(
        RDKitBond(
            begin_atom_index=bond.GetBeginAtomIdx(),
            end_atom_index=bond.GetEndAtomIdx(),
            begin_symbol=bond.GetBeginAtom().GetSymbol(),
            end_symbol=bond.GetEndAtom().GetSymbol(),
            bond_type=str(bond.GetBondType()),
            is_aromatic=bond.GetIsAromatic(),
            is_conjugated=bond.GetIsConjugated(),
        )
        for bond in mol.GetBonds()
    )


def _rings(mol: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(ring) for ring in mol.GetRingInfo().AtomRings())


def _fragments(mol: Any) -> tuple[RDKitFragment, ...]:
    Chem = _load_rdkit()
    atom_fragments = Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=False)
    atoms = mol.GetAtoms()
    return tuple(
        RDKitFragment(
            atom_indices=tuple(fragment),
            elements=tuple(atoms[index].GetSymbol() for index in fragment),
        )
        for fragment in atom_fragments
    )


def _canonical_pair(left: str, right: str) -> tuple[str, str]:
    ordered = sorted((left, right))
    return ordered[0], ordered[1]


def _count_motifs(mol: Any) -> dict[str, int]:
    counts = {name: 0 for name in MOTIF_NAMES}

    for atom in mol.GetAtoms():
        center = atom.GetSymbol()
        neighbor_symbols = [neighbor.GetSymbol() for neighbor in atom.GetNeighbors()]

        if center == "O":
            si_neighbors = sum(symbol == "Si" for symbol in neighbor_symbols)
            if si_neighbors >= 2:
                counts["Si-O-Si"] += si_neighbors * (si_neighbors - 1) // 2

    for bond in mol.GetBonds():
        pair = _canonical_pair(bond.GetBeginAtom().GetSymbol(), bond.GetEndAtom().GetSymbol())
        if pair == ("Fe", "O"):
            counts["Fe-O"] += 1
        elif pair == ("Ni", "O"):
            counts["Ni-O"] += 1
        elif pair == ("O", "P"):
            counts["P-O"] += 1

    return counts


def _mol_fragments(mol: Any) -> tuple[tuple[int, ...], ...]:
    Chem = _load_rdkit()
    return tuple(tuple(fragment) for fragment in Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=False))


def _symbolic_chain(mol: Any) -> tuple[str, ...]:
    fragments = _mol_fragments(mol)
    if fragments:
        largest = max(fragments, key=len)
        return tuple(mol.GetAtomWithIdx(index).GetSymbol() for index in largest)
    return tuple(atom.GetSymbol() for atom in mol.GetAtoms())


def evaluate_rdkit_molecule(text: str) -> RDKitEvaluation:
    mol, parser, parse_error = _parse_molecule(text)
    if mol is None:
        return RDKitEvaluation(
            source=text,
            parser=parser,
            molecular_validity=False,
            parse_error=parse_error,
            atoms=(),
            elements=(),
            bonds=(),
            rings=(),
            fragments=(),
            motifs={name: 0 for name in MOTIF_NAMES},
            symbolic_chain=(),
            chain_evaluation=None,
        )

    atoms = _atoms(mol)
    chain = _symbolic_chain(mol)
    chain_evaluation: ChainEvaluation | None = None
    if len(chain) >= 2:
        try:
            chain_evaluation = evaluate_chain(chain)
        except ValueError:
            chain_evaluation = None

    return RDKitEvaluation(
        source=text,
        parser=parser,
        molecular_validity=True,
        parse_error=None,
        atoms=atoms,
        elements=tuple(atom.symbol for atom in atoms),
        bonds=_bonds(mol),
        rings=_rings(mol),
        fragments=_fragments(mol),
        motifs=_count_motifs(mol),
        symbolic_chain=chain,
        chain_evaluation=chain_evaluation,
    )


def format_rdkit_scorecard(evaluation: RDKitEvaluation) -> str:
    lines = [
        f"source: {evaluation.source}",
        f"parser: {evaluation.parser}",
        f"molecular_validity: {str(evaluation.molecular_validity).lower()}",
    ]

    if evaluation.parse_error:
        lines.append(f"parse_error: {evaluation.parse_error}")
        return "\n".join(lines)

    lines.extend(["", "atoms:"])
    for atom in evaluation.atoms:
        lines.append(
            f"  {atom.index}: {atom.symbol} "
            f"(Z={atom.atomic_num}, charge={atom.formal_charge}, degree={atom.degree}, aromatic={atom.is_aromatic})"
        )

    lines.append("")
    lines.append("elements: " + ("-".join(evaluation.elements) if evaluation.elements else "none"))

    lines.extend(["", "bonds:"])
    if evaluation.bonds:
        for bond in evaluation.bonds:
            lines.append(
                f"  {bond.begin_atom_index}:{bond.begin_symbol} - "
                f"{bond.end_atom_index}:{bond.end_symbol} "
                f"({bond.bond_type}, aromatic={bond.is_aromatic}, conjugated={bond.is_conjugated})"
            )
    else:
        lines.append("  none")

    lines.extend(["", "rings:"])
    if evaluation.rings:
        for ring in evaluation.rings:
            lines.append("  " + "-".join(str(index) for index in ring))
    else:
        lines.append("  none")

    lines.extend(["", "fragments:"])
    for index, fragment in enumerate(evaluation.fragments, start=1):
        lines.append(f"  {index}: atoms={list(fragment.atom_indices)} elements={'-'.join(fragment.elements)}")

    lines.extend(["", "motifs:"])
    for name in MOTIF_NAMES:
        lines.append(f"  {name}: {evaluation.motifs[name]}")

    lines.append("")
    lines.append("symbolic chain: " + ("-".join(evaluation.symbolic_chain) if evaluation.symbolic_chain else "none"))

    if evaluation.chain_evaluation is not None:
        lines.extend(["", "symbolic scorecard:", format_scorecard(evaluation.chain_evaluation)])
    else:
        lines.extend(["", "symbolic scorecard: unavailable"])

    return "\n".join(lines)
