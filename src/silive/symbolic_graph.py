from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from .rdkit_chemistry import RDKitEvaluation, format_rdkit_scorecard

BACKBONE_ELEMENTS = {"Si", "O", "P", "Fe", "Ni"}
METAL_ELEMENTS = {"Fe", "Ni"}


@dataclass(frozen=True, slots=True)
class SymbolicNode:
    index: int
    element: str
    degree: int
    formal_charge: int
    is_aromatic: bool
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SymbolicEdge:
    begin: int
    end: int
    begin_element: str
    end_element: str
    bond_type: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SymbolicFragment:
    fragment_id: int
    atom_indices: tuple[int, ...]
    elements: tuple[str, ...]
    is_main_fragment: bool


@dataclass(frozen=True, slots=True)
class SymbolicGraph:
    nodes: tuple[SymbolicNode, ...]
    edges: tuple[SymbolicEdge, ...]
    rings: tuple[tuple[int, ...], ...]
    fragments: tuple[SymbolicFragment, ...]
    motifs: dict[str, int]
    main_backbone: tuple[int, ...]
    topology_tags: tuple[str, ...]
    graph_properties: dict[str, float]


def _node_tags(element: str, degree: int, formal_charge: int, is_aromatic: bool) -> tuple[str, ...]:
    tags: list[str] = []
    if element == "Si":
        tags.append("silicon")
    if element == "O":
        tags.append("oxygen")
    if element in METAL_ELEMENTS:
        tags.append("metal_center")
    if element == "P":
        tags.append("phosphorus")
    if degree <= 1:
        tags.append("terminal")
    if degree >= 3:
        tags.append("branch_point")
    if formal_charge:
        tags.append("charged")
    if is_aromatic:
        tags.append("aromatic")
    return tuple(tags)


def _edge_tags(left: str, right: str, bond_type: str) -> tuple[str, ...]:
    pair = {left, right}
    tags: list[str] = []
    if pair == {"Si", "O"}:
        tags.append("si_o_bridge")
    if "O" in pair and pair & METAL_ELEMENTS:
        tags.append("metal_o_bridge")
    if pair == {"P", "O"}:
        tags.append("p_o_bridge")
    if bond_type.upper() == "SINGLE":
        tags.append("single")
    elif bond_type.upper() == "DOUBLE":
        tags.append("double")
    return tuple(tags)


def _adjacency(edges: tuple[SymbolicEdge, ...], allowed: set[int] | None = None) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if allowed is not None and (edge.begin not in allowed or edge.end not in allowed):
            continue
        graph[edge.begin].add(edge.end)
        graph[edge.end].add(edge.begin)
    return graph


def _longest_path_for_component(adjacency: dict[int, set[int]], starts: set[int]) -> tuple[int, ...]:
    best: tuple[int, ...] = tuple()
    for start in starts:
        queue: deque[tuple[int, tuple[int, ...]]] = deque([(start, (start,))])
        while queue:
            current, path = queue.popleft()
            if len(path) > len(best):
                best = path
            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor not in path:
                    queue.append((neighbor, (*path, neighbor)))
    return best


def _main_backbone(nodes: tuple[SymbolicNode, ...], edges: tuple[SymbolicEdge, ...], main_atoms: set[int]) -> tuple[int, ...]:
    allowed = {node.index for node in nodes if node.element in BACKBONE_ELEMENTS and node.index in main_atoms}
    if not allowed:
        return tuple()
    return _longest_path_for_component(_adjacency(edges, allowed), allowed)


def _bond_counts(edges: tuple[SymbolicEdge, ...]) -> tuple[int, int, int]:
    si_o = 0
    metal_o = 0
    p_o = 0
    for edge in edges:
        pair = {edge.begin_element, edge.end_element}
        if pair == {"Si", "O"}:
            si_o += 1
        if "O" in pair and pair & METAL_ELEMENTS:
            metal_o += 1
        if pair == {"P", "O"}:
            p_o += 1
    return si_o, metal_o, p_o


def _topology_tags(
    nodes: tuple[SymbolicNode, ...],
    edges: tuple[SymbolicEdge, ...],
    rings: tuple[tuple[int, ...], ...],
    fragments: tuple[SymbolicFragment, ...],
    properties: dict[str, float],
) -> tuple[str, ...]:
    tags: list[str] = []
    branch_nodes = [node for node in nodes if node.degree >= 3]
    if properties["fragment_count"] > 1:
        tags.append("fragmented")
    if rings:
        tags.append("ring")
    if branch_nodes:
        tags.append("branched")
    if properties["network_score"] >= 0.45:
        tags.append("network")
    if not rings and not branch_nodes and properties["fragment_count"] <= 1:
        tags.append("linear")
    if properties["metal_o_bond_count"] > 0:
        tags.append("metal_center")
    if properties["p_o_bond_count"] > 0:
        tags.append("phosphate_bridge")
    if properties["si_o_bond_count"] >= 2:
        tags.append("siloxane_rich")
    return tuple(tags)


def build_symbolic_graph(evaluation: RDKitEvaluation) -> SymbolicGraph:
    nodes = tuple(
        SymbolicNode(
            index=atom.index,
            element=atom.symbol,
            degree=atom.degree,
            formal_charge=atom.formal_charge,
            is_aromatic=atom.is_aromatic,
            tags=_node_tags(atom.symbol, atom.degree, atom.formal_charge, atom.is_aromatic),
        )
        for atom in evaluation.atoms
    )
    edges = tuple(
        SymbolicEdge(
            begin=bond.begin_atom_index,
            end=bond.end_atom_index,
            begin_element=bond.begin_symbol,
            end_element=bond.end_symbol,
            bond_type=bond.bond_type,
            tags=_edge_tags(bond.begin_symbol, bond.end_symbol, bond.bond_type),
        )
        for bond in evaluation.bonds
    )

    if evaluation.fragments:
        largest = max(evaluation.fragments, key=lambda fragment: len(fragment.atom_indices))
        main_atoms = set(largest.atom_indices)
    else:
        main_atoms = {node.index for node in nodes}

    fragments = tuple(
        SymbolicFragment(
            fragment_id=index,
            atom_indices=fragment.atom_indices,
            elements=fragment.elements,
            is_main_fragment=set(fragment.atom_indices) == main_atoms,
        )
        for index, fragment in enumerate(evaluation.fragments, start=1)
    )

    si_o_bond_count, metal_o_bond_count, p_o_bond_count = _bond_counts(edges)
    branch_count = sum(1 for node in nodes if node.degree >= 3)
    ring_count = len(evaluation.rings)
    fragment_count = len(fragments)
    backbone = _main_backbone(nodes, edges, main_atoms)
    branching_score = min(1.0, branch_count / max(1, len(nodes)))
    network_score = min(1.0, 0.18 * si_o_bond_count + 0.22 * ring_count + 0.18 * branch_count)
    properties = {
        "si_o_bond_count": float(si_o_bond_count),
        "metal_o_bond_count": float(metal_o_bond_count),
        "p_o_bond_count": float(p_o_bond_count),
        "ring_count": float(ring_count),
        "fragment_count": float(fragment_count),
        "branching_score": round(branching_score, 3),
        "network_score": round(network_score, 3),
        "backbone_length": float(len(backbone)),
    }

    return SymbolicGraph(
        nodes=nodes,
        edges=edges,
        rings=evaluation.rings,
        fragments=fragments,
        motifs=dict(evaluation.motifs),
        main_backbone=backbone,
        topology_tags=_topology_tags(nodes, edges, evaluation.rings, fragments, properties),
        graph_properties=properties,
    )


def format_symbolic_graph_summary(graph: SymbolicGraph) -> str:
    lines = [
        "symbolic graph summary",
        "",
        "topology tags:",
        "  " + (", ".join(graph.topology_tags) if graph.topology_tags else "none"),
        "",
        "graph properties:",
    ]
    for key in (
        "si_o_bond_count",
        "metal_o_bond_count",
        "p_o_bond_count",
        "ring_count",
        "fragment_count",
        "branching_score",
        "network_score",
        "backbone_length",
    ):
        value = graph.graph_properties.get(key, 0.0)
        lines.append(f"  {key}: {value:.3f}")

    lines.extend(["", "main backbone:"])
    if graph.main_backbone:
        by_index = {node.index: node.element for node in graph.nodes}
        atoms = [f"{index}:{by_index.get(index, '?')}" for index in graph.main_backbone]
        lines.append("  " + " - ".join(atoms))
    else:
        lines.append("  none")

    lines.extend(["", "fragments:"])
    if graph.fragments:
        for fragment in graph.fragments:
            label = "main" if fragment.is_main_fragment else "side"
            lines.append(
                f"  {fragment.fragment_id}: {label}; atoms={list(fragment.atom_indices)}; elements={'-'.join(fragment.elements)}"
            )
    else:
        lines.append("  none")
    return "\n".join(lines)


def format_rdkit_graph_scorecard(evaluation: RDKitEvaluation) -> str:
    return format_rdkit_scorecard(evaluation) + "\n\n" + format_symbolic_graph_summary(build_symbolic_graph(evaluation))
