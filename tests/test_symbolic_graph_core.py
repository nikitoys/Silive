import json

from silive.rdkit_chemistry import RDKitAtom, RDKitBond, RDKitEvaluation, RDKitFragment
from silive.symbolic_graph import (
    build_symbolic_graph,
    diff_symbolic_graphs,
    format_symbolic_graph_diff,
    symbolic_graph_diff_to_json,
    symbolic_graph_to_json,
    write_symbolic_graph_diff_json,
    write_symbolic_graph_json,
)


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


def _evaluation(
    atoms: tuple[RDKitAtom, ...],
    bonds: tuple[RDKitBond, ...],
    motifs: dict[str, int] | None = None,
) -> RDKitEvaluation:
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
        motifs=motifs or {"Si-O-Si": 0, "Fe-O": 0, "Ni-O": 0, "P-O": 0},
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


def test_symbolic_graph_serializes_to_stable_json(tmp_path) -> None:
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
    payload = graph.to_dict()

    assert payload["schema_version"] == 1
    assert payload["nodes"][0] == {
        "index": 0,
        "element": "Si",
        "degree": 1,
        "formal_charge": 0,
        "is_aromatic": False,
        "tags": ["silicon", "terminal"],
    }
    assert payload["edges"][1]["tags"] == ["metal_o_bridge", "metal_oxide_bridge", "labile_bridge_candidate", "single"]
    assert payload["fragments"][0]["is_main_fragment"] is True
    assert payload["main_backbone"] == [2, 1, 3]
    assert payload["topology_tags"] == ["branched", "metal_center", "phosphate_bridge", "labile_bridge_candidate"]
    assert payload["graph_properties"]["labile_bridge_candidate_count"] == 2.0

    json_payload = json.loads(symbolic_graph_to_json(graph))
    assert json_payload == payload

    output = tmp_path / "graphs" / "candidate.json"
    write_symbolic_graph_json(graph, output)
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_symbolic_graph_diff_tracks_compact_topology_changes(tmp_path) -> None:
    parent_graph = build_symbolic_graph(
        _evaluation(
            (
                _atom(0, "Si", 1),
                _atom(1, "O", 2),
                _atom(2, "Si", 1),
            ),
            (
                _bond(0, 1, "Si", "O"),
                _bond(1, 2, "O", "Si"),
            ),
            motifs={"Si-O-Si": 1, "Fe-O": 0, "Ni-O": 0, "P-O": 0},
        )
    )
    child_graph = build_symbolic_graph(
        _evaluation(
            (
                _atom(0, "Si", 1),
                _atom(1, "O", 3),
                _atom(2, "Fe", 1),
                _atom(3, "P", 1),
            ),
            (
                _bond(0, 1, "Si", "O"),
                _bond(1, 2, "O", "Fe"),
                _bond(1, 3, "O", "P"),
            ),
            motifs={"Si-O-Si": 0, "Fe-O": 1, "Ni-O": 0, "P-O": 1},
        )
    )

    diff = diff_symbolic_graphs(parent_graph, child_graph)

    assert diff["schema_version"] == 1
    assert diff["topology_tags"]["added"] == ["branched", "labile_bridge_candidate", "metal_center", "phosphate_bridge"]
    assert diff["topology_tags"]["removed"] == ["linear", "siloxane_rich"]
    assert diff["bridge_counts"]["siloxane_bridge_count"] == {"parent": 2.0, "child": 1.0, "delta": -1.0}
    assert diff["bridge_counts"]["metal_oxide_bridge_count"] == {"parent": 0.0, "child": 1.0, "delta": 1.0}
    assert diff["bridge_counts"]["phosphate_bridge_count"] == {"parent": 0.0, "child": 1.0, "delta": 1.0}
    assert diff["properties"]["backbone_length"] == {"parent": 3.0, "child": 3.0, "delta": 0.0}
    assert diff["fragments"]["signatures_added"] == ["Si-O-Fe-P"]
    assert diff["fragments"]["signatures_removed"] == ["Si-O-Si"]
    assert diff["motif_counts"] == {
        "Fe-O": {"parent": 0, "child": 1, "delta": 1},
        "P-O": {"parent": 0, "child": 1, "delta": 1},
        "Si-O-Si": {"parent": 1, "child": 0, "delta": -1},
    }

    text = format_symbolic_graph_diff(diff)
    assert "symbolic graph diff" in text
    assert "metal_oxide_bridge_count: parent=0.000; child=1.000; delta=1.000" in text
    assert json.loads(symbolic_graph_diff_to_json(diff)) == diff

    output = tmp_path / "graphs" / "diff.json"
    write_symbolic_graph_diff_json(diff, output)
    assert json.loads(output.read_text(encoding="utf-8")) == diff
