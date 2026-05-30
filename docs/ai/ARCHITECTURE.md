# Architecture

## High-Level Pipeline

The intended project pipeline is:

```text
symbolic chain or RDKit molecule
  -> parsed atoms / bonds / rings / fragments
  -> symbolic graph with topology tags
  -> proto-gene motif detection
  -> minimal proto-genome coverage scoring
  -> batch candidate ranking
  -> abstract reaction opportunity scoring
  -> evolutionary motif search
  -> hypothesis/report layer
```

Sources:

- `PROJECT_GOAL.md`
- `CODEX_TASKS.md`
- `src/silive/cli.py`

## Entrypoints

The installed console command is:

```text
silive = silive.cli:main
```

The main CLI implementation is `src/silive/cli.py`.

Important CLI functions:

- `build_parser()`: builds all subcommands.
- `main()`: parses arguments and dispatches to the selected command handler.

The file also supports module execution because it has:

```python
if __name__ == "__main__":
    main()
```

Sources:

- `pyproject.toml`
- `src/silive/cli.py`

## Main Modules

### Core Simulation

- `src/silive/model.py`: Level 1 symbolic proto-life simulation, gene sets, simulation config, population simulation.
- `src/silive/sweep.py`: mutation/shell phase-map sweep logic.
- `src/silive/study.py`: repair-gene comparison study.
- `src/silive/plot.py`: phase-map CSV reading and plotting with optional `matplotlib`.

Sources:

- `PROJECT_GOAL.md`
- `src/silive/model.py`
- `src/silive/sweep.py`
- `src/silive/study.py`
- `src/silive/plot.py`

### Symbolic Chemistry

- `src/silive/chemistry.py`: parses and evaluates symbolic element chains; applies environment modifiers; mutates/searches chains.
- `src/silive/chain_simulation.py`: bridges symbolic chain evaluation into Level 1 simulation.
- `src/silive/chain_report.py`: writes JSON/CSV/TXT reports for a chain.
- `src/silive/environment_sweep.py`: evaluates/simulates a chain across environments.
- `src/silive/niche_search.py`: searches chain/environment pairs.

Sources:

- `README.md`
- `PROJECT_GOAL.md`
- `src/silive/chemistry.py`
- `src/silive/chain_simulation.py`
- `src/silive/chain_report.py`
- `src/silive/environment_sweep.py`
- `src/silive/niche_search.py`

### RDKit and Graph Layers

- `src/silive/rdkit_chemistry.py`: optional RDKit parsing and molecule evaluation. Raises `RDKitUnavailableError` when RDKit is missing.
- `src/silive/rdkit_cli.py`: small text wrapper around RDKit evaluation.
- `src/silive/rdkit_search.py`: ranks RDKit candidates from `.smi` or text files.
- `src/silive/symbolic_graph.py`: builds symbolic graph topology, formats summaries, writes JSON, compares graph diffs.
- `src/silive/symbolic_genome.py`: symbolic genome/motif representation independent from SMILES-like strings.

Sources:

- `docs/rdkit.md`
- `docs/rdkit_search.md`
- `docs/symbolic_graph.md`
- `PROJECT_GOAL.md`
- `src/silive/rdkit_chemistry.py`
- `src/silive/rdkit_cli.py`
- `src/silive/rdkit_search.py`
- `src/silive/symbolic_graph.py`
- `src/silive/symbolic_genome.py`

### Proto-Gene, Proto-Genome, Evolution, Reports

- `src/silive/proto_genes.py`: detects proto-gene motifs from RDKit/symbolic graph features.
- `src/silive/proto_genome.py`: scores minimal proto-genome function coverage.
- `src/silive/proto_gene_lineage.py`: searches heritable proto-gene motifs in symbolic-chain or RDKit modes.
- `src/silive/reaction_simulator.py`: scores abstract reaction opportunities.
- `src/silive/evolutionary_search.py`: mutation/selection search over motif candidates.
- `src/silive/hypothesis_layer.py`: reads search/evolution outputs and writes a Markdown hypothesis report.

Sources:

- `docs/proto_genes.md`
- `docs/proto_genome.md`
- `docs/proto_gene_lineage.md`
- `docs/reaction_simulator.md`
- `docs/evolutionary_search.md`
- `docs/hypothesis_layer.md`
- `PROJECT_GOAL.md`
- `src/silive/proto_genes.py`
- `src/silive/proto_genome.py`
- `src/silive/proto_gene_lineage.py`
- `src/silive/reaction_simulator.py`
- `src/silive/evolutionary_search.py`
- `src/silive/hypothesis_layer.py`

## CLI Command Groups

Base symbolic commands:

- `simulate`
- `compare`
- `sweep`
- `plot`
- `lab`
- `repair-study`
- `evaluate-chain`
- `search-chain`
- `chain-simulate`
- `chain-report`
- `environment-sweep`
- `niche-search`

RDKit/graph/search commands:

- `rdkit-evaluate`
- `rdkit-gene-evaluate`
- `rdkit-genome-evaluate`
- `rdkit-graph-evaluate`
- `rdkit-graph-diff`
- `rdkit-search`
- `rdkit-reaction-simulate`
- `rdkit-reaction-search`
- `rdkit-evolve`

Reporting/search commands:

- `proto-gene-search`
- `hypothesis-report`

Sources:

- `src/silive/cli.py`
- `README.md`
- `.github/workflows/ci.yml`

## Test Architecture

The test suite is in `tests/` and maps closely to modules in `src/silive/`.

Examples:

- `tests/test_model.py` tests `src/silive/model.py`.
- `tests/test_chemistry.py` tests `src/silive/chemistry.py`.
- `tests/test_rdkit_chemistry.py` tests optional RDKit behavior and skips when RDKit is not installed.
- `tests/test_symbolic_graph*.py` test graph functionality.

Pytest configuration is embedded in `pyproject.toml`:

- `pythonpath = ["src"]`
- `testpaths = ["tests"]`

Sources:

- `pyproject.toml`
- `tests/`

