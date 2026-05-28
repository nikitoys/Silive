# Silive / Codex project manifest

This file is a handoff note for Codex or any other coding agent taking over the Silive project.

Start with `PROJECT_GOAL.md`. It is the canonical short explanation of why this project exists, what the simulator is trying to answer, and what safety boundary must be preserved.

## Project purpose

Silive is an experimental computational research toy-model for hypothetical silicon-like proto-life.

The core goal is not to prove real silicon life exists and not to provide wet-lab synthesis instructions. The goal is to build a safe software simulator that can:

1. parse candidate RDKit SMILES/SMARTS structures;
2. preserve molecular topology as a symbolic graph;
3. detect chemical proto-genes from graph motifs;
4. evaluate whether a candidate covers a minimal proto-genome;
5. simulate abstract reaction opportunities;
6. run evolutionary motif search;
7. generate safe research hypotheses and bottleneck reports.

Current pipeline:

```text
RDKit molecule
  -> atoms/bonds/rings/fragments
  -> symbolic graph
  -> proto-gene detection
  -> minimal proto-genome evaluation
  -> candidate ranking
  -> abstract reaction simulator
  -> evolutionary motif search
```

## Important safety boundary

This repository should stay in the computational / symbolic / hypothesis-generation domain.

Do not add wet-lab protocols, quantities, temperatures, pressures, synthesis procedures, step-by-step experimental instructions, or operational instructions for making chemicals. Future wet-lab related code/docs should only generate high-level, non-operational research hypotheses such as classes of materials, motifs, and environmental variables to compare.

## Main modules

### Core symbolic chemistry

- `src/silive/rdkit_chemistry.py`
  - Optional RDKit layer.
  - Parses SMILES/SMARTS.
  - Extracts atoms, bonds, rings, fragments, motifs, molecular validity, and legacy `symbolic_chain`.

- `src/silive/symbolic_graph.py`
  - Builds full topology-preserving graph representation.
  - Main types: `SymbolicNode`, `SymbolicEdge`, `SymbolicFragment`, `SymbolicGraph`.
  - Computes topology tags: `linear`, `branched`, `ring`, `network`, `fragmented`, `metal_center`, `phosphate_bridge`, `siloxane_rich`.
  - Computes graph properties: `si_o_bond_count`, `metal_o_bond_count`, `p_o_bond_count`, `ring_count`, `fragment_count`, `branching_score`, `network_score`, `backbone_length`.

### Proto-gene and proto-genome layers

- `src/silive/proto_genes.py`
  - Detects proto-gene hits from RDKit + symbolic graph.
  - Main type: `ProtoGeneHit`.
  - Current proto-genes:
    - `GENE_SI_TEMPLATE`;
    - `GENE_FE_CATALYSIS`;
    - `GENE_NI_CATALYSIS`;
    - `GENE_P_REPAIR`;
    - `GENE_SILOXANE_SHELL`;
    - `GENE_LABILE_SEPARATION`.

- `src/silive/proto_genome.py`
  - Evaluates minimal symbolic proto-genome coverage.
  - Main type: `ProtoGenomeEvaluation`.
  - Minimal functions:
    - `TEMPLATE`;
    - `POLYMERIZE`;
    - `CATALYZE`;
    - `SEPARATE`;
    - `PROTECT`;
    - `REPAIR`.

### Search and transitions

- `src/silive/rdkit_search.py`
  - Batch ranking of `.smi` / `.txt` candidate files.
  - Calculates `candidate_score` from validity, proto-genome score, critical functions, and motif bonuses.
  - Writes CSV.

- `src/silive/reaction_simulator.py`
  - Abstract symbolic transition model, not chemical synthesis.
  - Main types: `ReactionRule`, `ReactionResult`.
  - Current rules:
    - `RXN_SIO_GROWTH`;
    - `RXN_SIO_BRANCH`;
    - `RXN_FE_CENTER_ADD`;
    - `RXN_NI_CENTER_ADD`;
    - `RXN_P_REPAIR_BRIDGE`;
    - `RXN_LABILE_BREAK`;
    - `RXN_RING_CLOSURE`;
    - `RXN_FRAGMENT_REJOIN`.

- `src/silive/evolutionary_search.py`
  - Abstract evolutionary motif search.
  - Main types: `EvolutionConfig`, `EvolutionCandidate`, `EvolutionRun`.
  - Mutates motif strings, applies abstract reaction opportunities, evaluates via RDKit/proto-genome pipeline, writes run outputs.

### CLI wrappers

The CLI has grown by wrappers to avoid repeatedly modifying the older main CLI.

Current entry point in `pyproject.toml`:

```toml
[project.scripts]
silive = "silive.cli_with_evolution:main"
```

Wrapper chain:

```text
cli_with_evolution.py
  -> cli_with_reactions.py
    -> cli_with_rdkit.py
      -> cli.py
```

This works, but a future cleanup could merge these wrappers into one clean command router.

## Main CLI commands

Install base dev environment:

```bash
python -m pip install -e .[dev]
```

Install RDKit-enabled environment:

```bash
python -m pip install -e .[chem]
```

Run tests:

```bash
pytest
```

RDKit / symbolic commands:

```bash
silive rdkit-evaluate "[Si]O[Si]O[Fe]O[Si]"
silive rdkit-gene-evaluate "[Si]O[Si]O[Fe]O[Si]"
silive rdkit-genome-evaluate "[Si]O[Si]O[Fe]O[Si]"
silive rdkit-graph-evaluate "[Si]O[Si]O[Fe]OP(=O)(O)O[Si]"
```

Batch search:

```bash
silive rdkit-search examples/rdkit_candidates.smi --output outputs/rdkit_search.csv --top 20
```

Reaction simulator:

```bash
silive rdkit-reaction-simulate "[Si]O[Si]O[Fe]O[Si]" --top 10
silive rdkit-reaction-search examples/rdkit_candidates.smi --output outputs/reaction_search.csv --top 20
```

Evolutionary search:

```bash
silive rdkit-evolve examples/rdkit_candidates.smi \
  --generations 20 \
  --population-size 30 \
  --elite-size 5 \
  --output-dir outputs/evolution \
  --seed 42
```

## Example inputs and outputs

- `examples/rdkit_candidates.smi`
  - Small candidate file with Si/O, Fe/O, Ni/O, phosphate, ring, fragmented, and invalid examples.

Common output directories:

- `outputs/rdkit_search.csv`
- `outputs/reaction_search.csv`
- `outputs/evolution/evolution_history.csv`
- `outputs/evolution/final_population.csv`
- `outputs/evolution/best_candidate.txt`
- `outputs/evolution/summary.json`

## Docs already present

- `PROJECT_GOAL.md`
- `docs/proto_genes.md`
- `docs/proto_genome.md`
- `docs/rdkit_search.md`
- `docs/symbolic_graph.md`
- `docs/reaction_simulator.md`
- `docs/evolutionary_search.md`

## Tests

RDKit-dependent tests are designed to skip when RDKit is not installed.

Important test files:

- `tests/test_rdkit_chemistry.py`
- `tests/test_proto_genes.py`
- `tests/test_proto_genome.py`
- `tests/test_rdkit_search.py`
- `tests/test_symbolic_graph.py`
- `tests/test_reaction_simulator.py`
- `tests/test_evolutionary_search.py`

## CI pattern

The GitHub Actions workflow installs `.[dev]`, not `.[chem]`, so RDKit may be absent. RDKit commands are smoke-tested with shell `if command; then ... else ... fi` blocks, so CI should not fail merely because RDKit is absent.

## Known limitations

1. RDKit symbolic structures are very simplified and often chemically unrealistic.
2. `symbolic_chain` is legacy and loses topology; prefer `SymbolicGraph`.
3. Reaction simulator does not generate valid product SMILES; it generates symbolic product descriptions.
4. Evolutionary search mutates strings and symbolic descriptions; it is not a realistic chemistry generator.
5. CLI wrapper chain should eventually be refactored into one clean command router.
6. Scores are heuristic and should be interpreted as ranking/debugging aids, not scientific proof.

## Recommended next step

Add a safe hypothesis layer that reads outputs from RDKit search, reaction search, and evolution, then produces high-level research hypotheses without operational wet-lab instructions.

Suggested next module:

```text
src/silive/hypothesis_layer.py
```

Suggested command:

```bash
silive hypothesis-report outputs/evolution --output outputs/hypotheses.md
```
