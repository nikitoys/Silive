from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .rdkit_chemistry import RDKitEvaluation, format_rdkit_scorecard

BACKBONE_ELEMENTS = {"Si", "O", "P", "Fe", "Ni"}
METAL_ELEMENTS = {"Fe", "Ni"}
BRIDGE_COUNT_KEYS = (
    "siloxane_bridge_count",
    "metal_oxide_bridge_count",
    "phosphate_bridge_count",
    "labile_bridge_candidate_count",
)
GRAPH_DIFF_PROPERTY_KEYS = ("backbone_length", "fragment_count")


@dataclass(frozen=True, slots=True)
class SymbolicNode:
    index: int
    element: str
    degree: int
    formal_charge: int
    is_aromatic: bool
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "element": self.element,
            "degree": self.degree,
            "formal_charge": self.formal_charge,
            "is_aromatic": self.is_aromatic,
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class SymbolicEdge:
    begin: int
    end: int
    begin_element: str
    end_element: str
    bond_type: str
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "begin": self.begin,
            "end": self.end,
            "begin_element": self.begin_element,
            "end_element": self.end_element,
            "bond_type": self.bond_type,
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class SymbolicFragment:
    fragment_id: int
    atom_indices: tuple[int, ...]
    elements: tuple[str, ...]
    is_main_fragment: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "atom_indices": list(self.atom_indices),
            "elements": list(self.elements),
            "is_main_fragment": self.is_main_fragment,
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "rings": [list(ring) for ring in self.rings],
            "fragments": [fragment.to_dict() for fragment in self.fragments],
            "motifs": dict(sorted(self.motifs.items())),
            "main_backbone": list(self.main_backbone),
            "topology_tags": list(self.topology_tags),
            "graph_properties": dict(sorted(self.graph_properties.items())),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


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
        tags.append("siloxane_bridge")
    if "O" in pair and pair & METAL_ELEMENTS:
        tags.append("metal_o_bridge")
        tags.append("metal_oxide_bridge")
        tags.append("labile_bridge_candidate")
    if pair == {"P", "O"}:
        tags.append("p_o_bridge")
        tags.append("phosphate_bridge")
        tags.append("labile_bridge_candidate")
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


def _component_nodes(adjacency: dict[int, set[int]], start: int) -> set[int]:
    seen = {start}
    queue: deque[int] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _farthest_shortest_path(adjacency: dict[int, set[int]], start: int) -> tuple[int, ...]:
    parents: dict[int, int | None] = {start: None}
    distances: dict[int, int] = {start: 0}
    queue: deque[int] = deque([start])
    farthest = start
    while queue:
        current = queue.popleft()
        if (distances[current], current) > (distances[farthest], farthest):
            farthest = current
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor not in parents:
                parents[neighbor] = current
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return _reconstruct_path(parents, farthest)


def _reconstruct_path(parents: dict[int, int | None], end: int) -> tuple[int, ...]:
    path: list[int] = []
    current: int | None = end
    while current is not None:
        path.append(current)
        current = parents[current]
    return tuple(reversed(path))


def _canonical_path(path: tuple[int, ...]) -> tuple[int, ...]:
    reversed_path = tuple(reversed(path))
    return path if path <= reversed_path else reversed_path


def _diameter_path_for_component(adjacency: dict[int, set[int]], starts: set[int]) -> tuple[int, ...]:
    remaining = set(starts)
    best: tuple[int, ...] = tuple()
    while remaining:
        component = _component_nodes(adjacency, min(remaining))
        remaining -= component
        first_path = _farthest_shortest_path(adjacency, min(component))
        second_path = _farthest_shortest_path(adjacency, first_path[-1])
        candidate = _canonical_path(second_path)
        if (len(candidate), tuple(reversed(candidate))) > (len(best), tuple(reversed(best))):
            best = candidate
    return best


def _main_backbone(nodes: tuple[SymbolicNode, ...], edges: tuple[SymbolicEdge, ...], main_atoms: set[int]) -> tuple[int, ...]:
    allowed = {node.index for node in nodes if node.element in BACKBONE_ELEMENTS and node.index in main_atoms}
    if not allowed:
        return tuple()
    return _diameter_path_for_component(_adjacency(edges, allowed), allowed)


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


def _bridge_counts(edges: tuple[SymbolicEdge, ...]) -> dict[str, int]:
    return {
        "siloxane_bridge_count": sum("siloxane_bridge" in edge.tags for edge in edges),
        "metal_oxide_bridge_count": sum("metal_oxide_bridge" in edge.tags for edge in edges),
        "phosphate_bridge_count": sum("phosphate_bridge" in edge.tags for edge in edges),
        "labile_bridge_candidate_count": sum("labile_bridge_candidate" in edge.tags for edge in edges),
    }


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
    if properties["labile_bridge_candidate_count"] > 0:
        tags.append("labile_bridge_candidate")
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
    bridge_counts = _bridge_counts(edges)
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
        "siloxane_bridge_count": float(bridge_counts["siloxane_bridge_count"]),
        "metal_oxide_bridge_count": float(bridge_counts["metal_oxide_bridge_count"]),
        "phosphate_bridge_count": float(bridge_counts["phosphate_bridge_count"]),
        "labile_bridge_candidate_count": float(bridge_counts["labile_bridge_candidate_count"]),
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


def symbolic_graph_to_dict(graph: SymbolicGraph) -> dict[str, Any]:
    return graph.to_dict()


def symbolic_graph_to_json(graph: SymbolicGraph, *, indent: int | None = 2) -> str:
    return graph.to_json(indent=indent)


def write_symbolic_graph_json(graph: SymbolicGraph, output: str | Path, *, indent: int | None = 2) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(symbolic_graph_to_json(graph, indent=indent) + "\n", encoding="utf-8")


def _numeric_delta(parent_value: float, child_value: float) -> dict[str, float]:
    return {
        "parent": parent_value,
        "child": child_value,
        "delta": round(child_value - parent_value, 3),
    }


def _count_delta(parent_value: int, child_value: int) -> dict[str, int]:
    return {
        "parent": parent_value,
        "child": child_value,
        "delta": child_value - parent_value,
    }


def _fragment_signatures(graph: SymbolicGraph) -> list[str]:
    return sorted("-".join(fragment.elements) for fragment in graph.fragments)


def diff_symbolic_graphs(parent: SymbolicGraph, child: SymbolicGraph) -> dict[str, Any]:
    parent_tags = set(parent.topology_tags)
    child_tags = set(child.topology_tags)
    parent_fragments = set(_fragment_signatures(parent))
    child_fragments = set(_fragment_signatures(child))
    motif_keys = sorted(set(parent.motifs) | set(child.motifs))

    motif_counts = {
        key: _count_delta(parent.motifs.get(key, 0), child.motifs.get(key, 0))
        for key in motif_keys
        if parent.motifs.get(key, 0) != child.motifs.get(key, 0)
    }

    return {
        "schema_version": 1,
        "topology_tags": {
            "added": sorted(child_tags - parent_tags),
            "removed": sorted(parent_tags - child_tags),
            "unchanged": sorted(parent_tags & child_tags),
        },
        "bridge_counts": {
            key: _numeric_delta(
                parent.graph_properties.get(key, 0.0),
                child.graph_properties.get(key, 0.0),
            )
            for key in BRIDGE_COUNT_KEYS
        },
        "properties": {
            key: _numeric_delta(
                parent.graph_properties.get(key, 0.0),
                child.graph_properties.get(key, 0.0),
            )
            for key in GRAPH_DIFF_PROPERTY_KEYS
        },
        "fragments": {
            "signatures_added": sorted(child_fragments - parent_fragments),
            "signatures_removed": sorted(parent_fragments - child_fragments),
            "signatures_unchanged": sorted(parent_fragments & child_fragments),
        },
        "motif_counts": motif_counts,
    }


def symbolic_graph_diff_to_json(diff: dict[str, Any], *, indent: int | None = 2) -> str:
    return json.dumps(diff, indent=indent, sort_keys=True)


def write_symbolic_graph_diff_json(diff: dict[str, Any], output: str | Path, *, indent: int | None = 2) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(symbolic_graph_diff_to_json(diff, indent=indent) + "\n", encoding="utf-8")


def format_symbolic_graph_diff(diff: dict[str, Any]) -> str:
    lines = ["symbolic graph diff", "", "topology tags:"]
    tag_diff = diff["topology_tags"]
    for label in ("added", "removed", "unchanged"):
        values = tag_diff[label]
        lines.append(f"  {label}: {', '.join(values) if values else 'none'}")

    lines.extend(["", "bridge counts:"])
    for key, values in diff["bridge_counts"].items():
        lines.append(
            f"  {key}: parent={values['parent']:.3f}; child={values['child']:.3f}; delta={values['delta']:.3f}"
        )

    lines.extend(["", "properties:"])
    for key, values in diff["properties"].items():
        lines.append(
            f"  {key}: parent={values['parent']:.3f}; child={values['child']:.3f}; delta={values['delta']:.3f}"
        )

    lines.extend(["", "fragments:"])
    fragment_diff = diff["fragments"]
    for label in ("signatures_added", "signatures_removed", "signatures_unchanged"):
        values = fragment_diff[label]
        lines.append(f"  {label}: {', '.join(values) if values else 'none'}")

    lines.extend(["", "motif counts:"])
    if diff["motif_counts"]:
        for key, values in diff["motif_counts"].items():
            lines.append(f"  {key}: parent={values['parent']}; child={values['child']}; delta={values['delta']}")
    else:
        lines.append("  none")
    return "\n".join(lines)


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
        "siloxane_bridge_count",
        "metal_oxide_bridge_count",
        "phosphate_bridge_count",
        "labile_bridge_candidate_count",
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
