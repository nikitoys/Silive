# Project goal: Silive / silicon-like proto-life simulator

Silive is a safe computational research toy-model for exploring hypothetical silicon-like proto-life.

The goal is not to prove that silicon life exists. The goal is not to provide wet-lab synthesis instructions. The goal is to build a software system that helps ask a constrained research question:

```text
What minimal set of chemical motifs could behave like proto-genes / a proto-genome in a silicon-mineral system?
```

## Core idea

Silive treats a candidate molecule or mineral-polymer graph as interesting when it can cover a minimal functional set:

| Function | Meaning |
| --- | --- |
| `TEMPLATE` | storage/copying of structure |
| `POLYMERIZE` | growth or extension of a chain/network |
| `CATALYZE` | catalytic center |
| `SEPARATE` | separation of copy or fragment |
| `PROTECT` | shell, matrix, persistence, or stability |
| `REPAIR` | correction or stabilization of defects |

The project is therefore searching for minimal chemical proto-genomes, not full living cells.

## Current conceptual pipeline

```text
RDKit molecule / SMILES / SMARTS
  ↓
atoms, bonds, rings, fragments
  ↓
symbolic graph
  ↓
proto-gene detection
  ↓
minimal proto-genome evaluation
  ↓
candidate ranking
  ↓
abstract reaction simulator
  ↓
evolutionary motif search
  ↓
safe research hypotheses
```

## Proto-gene intuition

Current motif-to-function assumptions are heuristic:

| Motif / topology | Functional interpretation |
| --- | --- |
| `Si-O-Si` | template, scaffold, polymer growth |
| `Fe-O` or `Ni-O` | catalytic center |
| `P-O` | repair bridge / defect stabilization |
| Si/O ring or dense Si-O network | protection, shell, stability |
| labile bridge, terminal handle, or separated fragment | separation / copy release |

These are not claims of real chemistry. They are scoring assumptions for computational exploration.

## What Silive is trying to answer

Silive tries to compare candidate structures and ask:

```text
Which structures are closest to a minimal functional system that can store form,
grow, catalyze transitions, separate fragments, protect itself, and repair defects?
```

It does this through heuristic graph analysis, proto-gene detection, proto-genome scoring, batch search, abstract reaction simulation, and evolutionary search.

## Current implementation status

The repository currently contains the main chain:

```text
RDKit → symbolic graph → proto-genes → proto-genome
      → batch search → reaction simulator → evolutionary search
```

Important modules:

- `rdkit_chemistry.py` parses RDKit candidates and extracts atoms/bonds/rings/fragments.
- `symbolic_graph.py` preserves topology: branching, rings, fragments, networks, and backbones.
- `proto_genes.py` maps chemical motifs to proto-gene hits.
- `proto_genome.py` evaluates minimal functional coverage.
- `rdkit_search.py` ranks candidate files.
- `reaction_simulator.py` models abstract motif transitions.
- `evolutionary_search.py` mutates and selects symbolic/RDKit candidates.

## Safety boundary

Silive must remain a computational and symbolic research tool.

Allowed:

- graph analysis;
- symbolic motif scoring;
- abstract reaction opportunities;
- evolutionary search over motifs;
- high-level research hypotheses;
- comparison of broad classes of mineral-polymer motifs.

Not allowed in this project:

- wet-lab protocols;
- synthesis procedures;
- operational chemical instructions;
- quantities, concentrations, temperatures, pressures, or times for experiments;
- purification or preparation steps.

Future wet-lab-related output should stay at the level of safe, non-operational hypotheses: what motif classes, topology classes, and environmental variables might be worth comparing in legitimate research.

## Next strategic step

The next useful layer is a safe hypothesis report:

```text
search/evolution outputs
  → recurring motifs
  → bottlenecks
  → missing functions
  → promising topology classes
  → high-level, non-operational research hypotheses
```

Possible command:

```bash
silive hypothesis-report outputs/evolution --output outputs/hypotheses.md
```

This report should summarize what the computational search suggests, without turning it into laboratory instructions.
