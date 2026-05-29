from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any

ELEMENT_PATTERN = re.compile(r"\[([A-Z][a-z]?)\]|([A-Z][a-z]?)")
METAL_ELEMENTS = {"Fe", "Ni"}


@dataclass(frozen=True, slots=True)
class SymbolicMotif:
    name: str
    elements: tuple[str, ...]
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elements": list(self.elements),
            "count": self.count,
        }


@dataclass(frozen=True, slots=True)
class SymbolicGenome:
    fragments: tuple[tuple[str, ...], ...]
    motifs: tuple[SymbolicMotif, ...]
    topology_hints: tuple[str, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "fragments": [list(fragment) for fragment in self.fragments],
            "motifs": [motif.to_dict() for motif in self.motifs],
            "topology_hints": list(self.topology_hints),
        }

    def describe(self) -> str:
        fragments = ["-".join(fragment) for fragment in self.fragments if fragment]
        motif_parts = [f"{motif.name}={motif.count}" for motif in self.motifs if motif.count]
        hints = ",".join(self.topology_hints) or "none"
        return f"fragments={'+'.join(fragments) or 'empty'} | motifs={','.join(motif_parts) or 'none'} | hints={hints}"


def _tokenize_fragment(text: str) -> tuple[str, ...]:
    return tuple(match.group(1) or match.group(2) for match in ELEMENT_PATTERN.finditer(text))


def _count_window(elements: tuple[str, ...], window: tuple[str, ...]) -> int:
    if len(elements) < len(window):
        return 0
    return sum(1 for index in range(0, len(elements) - len(window) + 1) if elements[index : index + len(window)] == window)


def _count_pair(elements: tuple[str, ...], left: str, right: str) -> int:
    return sum(1 for first, second in zip(elements, elements[1:]) if {first, second} == {left, right})


def _motifs_for_fragments(fragments: tuple[tuple[str, ...], ...]) -> tuple[SymbolicMotif, ...]:
    si_o_si = sum(_count_window(fragment, ("Si", "O", "Si")) for fragment in fragments)
    fe_o = sum(_count_pair(fragment, "Fe", "O") for fragment in fragments)
    ni_o = sum(_count_pair(fragment, "Ni", "O") for fragment in fragments)
    p_o = sum(_count_pair(fragment, "P", "O") for fragment in fragments)
    return (
        SymbolicMotif("Si-O-Si", ("Si", "O", "Si"), si_o_si),
        SymbolicMotif("Fe-O", ("Fe", "O"), fe_o),
        SymbolicMotif("Ni-O", ("Ni", "O"), ni_o),
        SymbolicMotif("P-O", ("P", "O"), p_o),
    )


def _topology_hints(fragments: tuple[tuple[str, ...], ...], explicit_hints: tuple[str, ...] = tuple()) -> tuple[str, ...]:
    hints = set(explicit_hints)
    if len([fragment for fragment in fragments if fragment]) > 1:
        hints.add("fragmented")
    for fragment in fragments:
        if any(element in METAL_ELEMENTS for element in fragment):
            hints.add("metal_center")
        if "P" in fragment:
            hints.add("phosphate_bridge")
        if _count_window(fragment, ("Si", "O", "Si")) > 0:
            hints.add("siloxane_template")
    return tuple(sorted(hints))


def make_symbolic_genome(
    fragments: tuple[tuple[str, ...], ...],
    *,
    topology_hints: tuple[str, ...] = tuple(),
) -> SymbolicGenome:
    cleaned = tuple(fragment for fragment in fragments if fragment)
    return SymbolicGenome(
        fragments=cleaned,
        motifs=_motifs_for_fragments(cleaned),
        topology_hints=_topology_hints(cleaned, topology_hints),
    )


def score_symbolic_viability(genome: SymbolicGenome) -> float:
    atom_count = sum(len(fragment) for fragment in genome.fragments)
    if atom_count == 0:
        return 0.0

    motif_counts = {motif.name: motif.count for motif in genome.motifs}
    metal_bridge_count = motif_counts.get("Fe-O", 0) + motif_counts.get("Ni-O", 0)
    motif_score = min(
        0.35,
        0.16 * motif_counts.get("Si-O-Si", 0)
        + 0.10 * metal_bridge_count
        + 0.12 * motif_counts.get("P-O", 0),
    )
    topology_score = 0.0
    if "siloxane_template" in genome.topology_hints:
        topology_score += 0.10
    if "metal_center" in genome.topology_hints:
        topology_score += 0.08
    if "phosphate_bridge" in genome.topology_hints:
        topology_score += 0.08
    if "fragmented" in genome.topology_hints:
        topology_score += 0.07
    if "si_o_ring" in genome.topology_hints:
        topology_score += 0.07
    topology_score = min(0.30, topology_score)
    unique_elements = {element for fragment in genome.fragments for element in fragment}
    diversity_score = min(0.15, 0.03 * len(unique_elements))
    size_score = min(0.20, atom_count / 30)
    return round(min(1.0, motif_score + topology_score + diversity_score + size_score), 3)


def symbolic_genome_from_molecule(molecule: str) -> SymbolicGenome:
    fragments = tuple(_tokenize_fragment(part) for part in molecule.split("."))
    hints = ("si_o_ring",) if "1" in molecule and "[Si]" in molecule else tuple()
    return make_symbolic_genome(fragments, topology_hints=hints)


def _render_element(element: str) -> str:
    if element in {"Si", "Fe", "Ni"}:
        return f"[{element}]"
    return element


def _render_fragment(elements: tuple[str, ...], topology_hints: tuple[str, ...]) -> str:
    if "si_o_ring" in topology_hints and elements == ("Si", "O", "Si", "O"):
        return "[Si]1O[Si]O1"
    pieces: list[str] = []
    index = 0
    while index < len(elements):
        if elements[index : index + 4] == ("O", "P", "O", "O"):
            pieces.append("OP(=O)(O)")
            index += 4
            continue
        if elements[index : index + 5] == ("O", "P", "O", "O", "O"):
            pieces.append("OP(=O)(O)O")
            index += 5
            continue
        pieces.append(_render_element(elements[index]))
        index += 1
    return "".join(pieces)


def symbolic_genome_to_molecule(genome: SymbolicGenome) -> str:
    return ".".join(_render_fragment(fragment, genome.topology_hints) for fragment in genome.fragments)


def _main_fragment_index(fragments: tuple[tuple[str, ...], ...]) -> int:
    return max(range(len(fragments)), key=lambda index: len(fragments[index])) if fragments else 0


def _replace_main_fragment(genome: SymbolicGenome, fragment: tuple[str, ...], *hints: str) -> SymbolicGenome:
    fragments = list(genome.fragments or (tuple(),))
    fragments[_main_fragment_index(tuple(fragments))] = fragment
    return make_symbolic_genome(tuple(fragments), topology_hints=tuple(sorted(set(genome.topology_hints) | set(hints))))


def mutate_symbolic_genome(genome: SymbolicGenome, rng: random.Random, operators: tuple[str, ...]) -> tuple[SymbolicGenome, str]:
    operator = rng.choice(operators)
    fragments = genome.fragments or (tuple(),)
    main_index = _main_fragment_index(fragments)
    main = fragments[main_index]

    if operator == "add_si_o_unit":
        return _replace_main_fragment(genome, main + ("O", "Si")), operator
    if operator == "add_fe_o_center":
        return _replace_main_fragment(genome, main + ("O", "Fe")), operator
    if operator == "add_ni_o_center":
        return _replace_main_fragment(genome, main + ("O", "Ni")), operator
    if operator == "add_p_o_bridge":
        insertion = ("O", "P", "O", "O", "O")
        if main[-1:] == ("Si",):
            return _replace_main_fragment(genome, main[:-1] + insertion + ("Si",)), operator
        return _replace_main_fragment(genome, main + insertion), operator
    if operator == "close_si_o_ring_symbolically":
        return make_symbolic_genome((("Si", "O", "Si", "O"),), topology_hints=("si_o_ring",)), operator
    if operator == "split_labile_bridge":
        return make_symbolic_genome((*fragments, ("Si", "O")), topology_hints=genome.topology_hints), operator
    if operator == "duplicate_si_o_segment":
        for index in range(0, max(0, len(main) - 2)):
            if main[index : index + 3] == ("Si", "O", "Si"):
                return _replace_main_fragment(genome, main[: index + 3] + ("O", "Si") + main[index + 3 :]), operator
        return _replace_main_fragment(genome, main + ("O", "Si")), operator
    if operator == "remove_weak_terminal_group":
        for suffix in (("O", "Fe"), ("O", "Ni"), ("O", "Si")):
            if len(main) > len(suffix) and main[-len(suffix) :] == suffix:
                return _replace_main_fragment(genome, main[: -len(suffix)]), operator
        if len(fragments) > 1 and fragments[-1] == ("Si", "O"):
            return make_symbolic_genome(fragments[:-1], topology_hints=genome.topology_hints), operator
        return genome, operator
    return genome, operator
