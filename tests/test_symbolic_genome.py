import random

from silive.evolutionary_search import (
    EvolutionCandidate,
    MUTATION_OPERATORS,
    mutate_genome,
    mutate_molecule,
    write_candidates_csv,
)
from silive.symbolic_genome import (
    make_symbolic_genome,
    mutate_symbolic_genome,
    score_symbolic_viability,
    symbolic_genome_from_molecule,
    symbolic_genome_to_molecule,
)


def test_symbolic_genome_parses_motifs_without_rdkit() -> None:
    genome = symbolic_genome_from_molecule("[Si]O[Si]O[Fe].O[Ni]")

    assert genome.fragments == (("Si", "O", "Si", "O", "Fe"), ("O", "Ni"))
    assert genome.to_dict()["schema_version"] == 1
    assert {motif.name: motif.count for motif in genome.motifs} == {
        "Si-O-Si": 1,
        "Fe-O": 1,
        "Ni-O": 1,
        "P-O": 0,
    }
    assert "fragmented" in genome.topology_hints
    assert "metal_center" in genome.topology_hints


def test_symbolic_genome_renders_phosphate_and_ring_forms() -> None:
    phosphate = make_symbolic_genome((("Si", "O", "P", "O", "O", "O", "Si"),))
    ring = make_symbolic_genome((("Si", "O", "Si", "O"),), topology_hints=("si_o_ring",))

    assert symbolic_genome_to_molecule(phosphate) == "[Si]OP(=O)(O)O[Si]"
    assert symbolic_genome_to_molecule(ring) == "[Si]1O[Si]O1"
    assert "phosphate_bridge" in phosphate.topology_hints
    assert "si_o_ring" in ring.topology_hints


def test_symbolic_mutation_operates_on_genome_object() -> None:
    genome = symbolic_genome_from_molecule("[Si]O[Si]")
    mutated, operator = mutate_symbolic_genome(genome, random.Random(1), ("add_fe_o_center",))

    assert operator == "add_fe_o_center"
    assert mutated.fragments == (("Si", "O", "Si", "O", "Fe"),)
    assert symbolic_genome_to_molecule(mutated) == "[Si]O[Si]O[Fe]"
    assert "metal_center" in mutated.topology_hints


def test_evolutionary_mutation_delegates_to_symbolic_genome() -> None:
    genome = symbolic_genome_from_molecule("[Si]O[Si]")
    mutated_genome, operator = mutate_genome(genome, random.Random(1))
    mutated_molecule, molecule_operator = mutate_molecule("[Si]O[Si]", random.Random(1))

    assert operator in MUTATION_OPERATORS
    assert molecule_operator == operator
    assert mutated_molecule == symbolic_genome_to_molecule(mutated_genome)


def test_symbolic_viability_score_is_independent_from_rdkit() -> None:
    empty = symbolic_genome_from_molecule("not_a_symbolic_candidate")
    simple = symbolic_genome_from_molecule("[Si]O[Si]")
    richer = symbolic_genome_from_molecule("[Si]O[Si]O[Fe]OP(=O)(O)O[Si]")

    assert score_symbolic_viability(empty) == 0.0
    assert 0.0 < score_symbolic_viability(simple) < score_symbolic_viability(richer) <= 1.0


def test_evolution_csv_tracks_rdkit_and_symbolic_scores(tmp_path) -> None:
    candidate = EvolutionCandidate(
        candidate_id="c1",
        parent_id=None,
        molecule="[Si]O[Si]",
        symbolic_description="symbolic",
        generation=0,
        mutations=tuple(),
        applied_reactions=tuple(),
        candidate_score=0.4,
        rdkit_valid_score=1.0,
        symbolic_viability_score=0.32,
        genome_score=0.5,
        covered_functions=("TEMPLATE",),
        missing_functions=("CATALYZE",),
        detected_genes=("GENE_SI_TEMPLATE",),
        topology_tags=("linear",),
        viability="partial_candidate",
        risk_flags=("rdkit_invalid", "symbolic_only", "requires_chemical_validation"),
        preservation_reason="preserved_for_symbolic_motif_search",
    )

    output = tmp_path / "population.csv"
    write_candidates_csv([candidate], output)
    text = output.read_text(encoding="utf-8")

    assert "rdkit_valid_score" in text
    assert "symbolic_viability_score" in text
    assert "1.000,0.320" in text
    assert "rdkit_invalid;symbolic_only;requires_chemical_validation" in text
    assert "preserved_for_symbolic_motif_search" in text


def test_invalid_symbolic_candidate_is_marked_for_preservation() -> None:
    from silive.rdkit_chemistry import RDKitEvaluation
    from silive.rdkit_search import (
        candidate_risk_flags,
        classify_viability,
        preservation_reason,
        symbolic_viability_score,
    )
    from silive.proto_genome import ProtoGenomeEvaluation

    invalid_evaluation = RDKitEvaluation(
        source="[Si]O[Si]O[Fe]",
        parser="none",
        molecular_validity=False,
        parse_error="synthetic invalid",
        atoms=tuple(),
        elements=tuple(),
        bonds=tuple(),
        rings=tuple(),
        fragments=tuple(),
        motifs={},
        symbolic_chain=tuple(),
        chain_evaluation=None,
    )
    genome = ProtoGenomeEvaluation(
        covered_functions=tuple(),
        missing_functions=("TEMPLATE", "POLYMERIZE", "CATALYZE", "SEPARATE", "PROTECT", "REPAIR"),
        gene_hits=[],
        minimal_viable=False,
        bottlenecks=tuple(),
        recommendations=tuple(),
        genome_score=0.0,
    )
    symbolic_score = symbolic_viability_score("[Si]O[Si]O[Fe]")

    assert symbolic_score >= 0.25
    assert classify_viability(0.0, genome, 0.0, symbolic_score) == "symbolic_only_invalid_candidate"
    assert candidate_risk_flags(invalid_evaluation, symbolic_score) == (
        "rdkit_invalid",
        "symbolic_only",
        "requires_chemical_validation",
    )
    assert preservation_reason(invalid_evaluation, symbolic_score) == "preserved_for_symbolic_motif_search"
