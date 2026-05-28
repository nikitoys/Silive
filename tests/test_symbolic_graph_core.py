from silive.rdkit_chemistry import RDKitAtom, RDKitBond, RDKitEvaluation, RDKitFragment
from silive.symbolic_graph import build_symbolic_graph


def _atom(index: int, symbol: str, degree: int) -> RDKitAtom:
    atomic_nums = {"O": 8, "P": 15, "Si": 14, "Fe": 26}
    return RDKitAtom(
        index=index,
        symbol=symbol,
        atomic_num=atomic_nums[symbol],
        formal_charge=0,
        degree=degree,
        is_aromatic=False,
    )


def _bond(left: int, right: int, left_symbol: str, right_symbol: str) -> RDKitBond:
    return RDKitBond(
        begin_atom_index=left,
        end_atom_index=right,
        begin_symbol=left_symbol,
        end_symbol=right_symbol,
        bond_type="SINGLE",
        is_aromatic=False,
        is_conjugated=False,
    )


def _evaluation(atoms: tuple[RDKitAtom, ...], bonds: tuple[RDKitBond, ...]) -> RDKitEvaluation:
    return RDKitEvaluation(
        source="synthetic",
        parser="test",
        molecular_validity=True,
        parse_error=None,
        atoms=atoms,
        elements=tuple(atom.symbol for atom in atoms),
        bonds=bonds,
        rings=(),
        fragments=(RDKitFragment(tuple(atom.index for atom in atoms), tuple(atom.symbol for atom in atoms)),),
        motifs={"Si-O-Si": 0, "Fe-O": 0, "Ni-O": 0, "P-O": 0},
        symbolic_chain=tuple(atom.symbol for atom in atoms),
        chain_evaluation=None,
    )


def test_main_backbone_uses_graph_diameter_path() -> None:
    atoms = (
        _atom(0, "Si", 1),
        _atom(1, "O", 2),
        _atom(2, "Si", 3),
        _atom(3, "O", 2),
        _atom(4, "Si", 1),
        _atom(5, "O", 1),
    )
    bonds = (
        _bond(0, 1, "Si", "O"),
        _bond(1, 2, "O", "Si"),
        _bond(2, 3, "Si", "O"),
        _bond(3, 4, "O", "Si"),
        _bond(2, 5, "Si", "O"),
    )

    graph = build_symbolic_graph(_evaluation(atoms, bonds))

    assert graph.main_backbone == (0, 1, 2, 3, 4)
    assert graph.graph_properties["backbone_length"] == 5.0


def test_bridge_classifications_are_explicit() -> None:
    atoms = (
        _atom(0, "Si", 1),
        _atom(1, "O", 3),
        _atom(2, "Fe", 1),
        _atom(3, "P", 1),
    )
    bonds = (
        _bond(0, 1, "Si", "O"),
        _bond(1, 2, "O", "Fe"),
        _bond(1, 3, "O", "P"),
    )

    graph = build_symbolic_graph(_evaluation(atoms, bonds))
    edge_tags = {tag for edge in graph.edges for tag in edge.tags}

    assert {"siloxane_bridge", "metal_oxide_bridge", "phosphate_bridge"} <= edge_tags
    assert "labile_bridge_candidate" in edge_tags
    assert "labile_bridge_candidate" in graph.topology_tags
    assert graph.graph_properties["siloxane_bridge_count"] == 1.0
    assert graph.graph_properties["metal_oxide_bridge_count"] == 1.0
    assert graph.graph_properties["phosphate_bridge_count"] == 1.0
    assert graph.graph_properties["labile_bridge_candidate_count"] == 2.0
