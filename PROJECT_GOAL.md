# Project goal: Silive / silicon-like proto-life simulator

Silive is a computational toy model for exploring whether a silicon/mineral motif system can be described as a minimal proto-life-like pipeline.

The project goal is to build a program that can take candidate symbolic chains or RDKit molecules, convert them into graph/topology features, detect proto-gene-like motifs, score whether the candidate covers a minimal proto-genome, and then use search/evolution/reporting tools to find which motif families are most promising.

In one sentence:

```text
Silive searches for minimal silicon/mineral motif graphs that can store a pattern,
grow, catalyze transitions, separate fragments, persist as a structure, and repair defects.
```

## Main research question

Silive is trying to answer this software question:

```text
Given a symbolic chain or molecular graph, how close is it to a minimal functional
proto-genome made from silicon/mineral motifs?
```

The project does not need to start from a complete living cell. It starts from a smaller question: which combinations of motifs can cover the basic functions that a proto-life-like system would need.

## Minimal functions to track

A candidate is interesting when it covers as many of these functions as possible:

| Function | Meaning in the model |
| --- | --- |
| `TEMPLATE` | stores or repeats a structural pattern |
| `POLYMERIZE` | extends a chain, scaffold, or network |
| `CATALYZE` | contains a catalytic-center-like motif |
| `SEPARATE` | can release a copied fragment or split a labile part |
| `PROTECT` | has a shell/matrix/network feature that improves persistence |
| `REPAIR` | has a bridge or motif that can stabilize/correct defects |

These functions are model targets. The code should make them measurable, searchable, and comparable across candidates.

## Current pipeline

The intended project pipeline is:

```text
symbolic chain or RDKit molecule
  ↓
parsed atoms / bonds / rings / fragments
  ↓
symbolic graph with topology tags
  ↓
proto-gene motif detection
  ↓
minimal proto-genome coverage scoring
  ↓
batch candidate ranking
  ↓
abstract reaction opportunity scoring
  ↓
evolutionary motif search
  ↓
hypothesis/report layer
```

## Current motif interpretation

Current motif rules are heuristics used by the scoring layers:

| Motif / topology | Interpretation in Silive |
| --- | --- |
| `Si-O-Si` repeats | template/scaffold and polymer-growth signal |
| longer Si/O chain or network | stronger persistence and growth potential |
| Si/O ring or dense Si/O network | protection/shell/stability signal |
| `Fe-O` or `Ni-O` center | catalytic-center signal |
| `P-O` bridge | repair/defect-stabilization signal |
| labile bridge, terminal handle, or separated fragment | separation/copy-release signal |

The immediate engineering goal is to keep these assumptions explicit in code and reports, so they can be inspected and changed later.

## What is already implemented

The repository already has the main computational chain:

```text
Level 1 symbolic simulator
  → Level 2 symbolic chemistry
  → RDKit parsing
  → symbolic graph extraction
  → proto-gene detection
  → proto-genome scoring
  → candidate search
  → reaction opportunity scoring
  → evolutionary search
```

Implemented pieces:

- `src/silive/model.py`: Level 1 symbolic proto-organism simulation.
- `src/silive/chemistry.py`: Level 2 symbolic chain scoring.
- `src/silive/chain_simulation.py`: bridge from symbolic chemistry into Level 1 simulations.
- `src/silive/chain_report.py`: report package for a concrete symbolic chain.
- `src/silive/environment_sweep.py`: compare one chain across supported symbolic environments.
- `src/silive/niche_search.py`: search chain/environment pairs.
- `src/silive/rdkit_chemistry.py`: parse RDKit candidates into atoms, bonds, rings, and fragments.
- `src/silive/symbolic_graph.py`: preserve graph topology such as branches, rings, fragments, networks, and backbones.
- `src/silive/proto_genes.py`: detect proto-gene motifs from graph/candidate features.
- `src/silive/proto_genome.py`: score minimal functional coverage.
- `src/silive/rdkit_search.py`: rank candidate files.
- `src/silive/reaction_simulator.py`: score abstract reaction opportunities.
- `src/silive/evolutionary_search.py`: mutate/select symbolic or RDKit motif candidates.
- `src/silive/cli.py`: current command router for the main CLI commands.

## CLI capabilities already present

The current command set covers:

- symbolic chain evaluation;
- symbolic chain search;
- chain simulation;
- chain report generation;
- environment sweeps;
- niche search;
- RDKit candidate evaluation;
- RDKit proto-gene/proto-genome evaluation;
- symbolic graph evaluation;
- RDKit batch search;
- reaction simulation/search;
- evolutionary search.

## What still needs to be done

The next useful work is engineering and reporting work, not a new manifesto.

1. **Clean CLI architecture**
   - Keep `src/silive/cli.py` as the stable entry point.
   - Remove or retire old wrapper indirection once compatibility is confirmed.
   - Ensure all commands stay available through the same router.

2. **Improve symbolic graph quality**
   - Replace brute-force backbone/longest-path logic with a better graph algorithm.
   - Add explicit bridge classifications: siloxane, metal oxide, phosphate, labile bridge candidate.
   - Add graph JSON serialization.
   - Add graph diff between parent and mutated candidates.

3. **Improve evolutionary search**
   - Introduce a symbolic genome/motif object independent from SMILES strings.
   - Generate RDKit strings only when possible.
   - Track both `rdkit_valid_score` and `symbolic_viability_score`.
   - Keep useful invalid symbolic candidates, but mark them clearly.

4. **Add hypothesis/report layer**
   - Read search/evolution outputs.
   - Summarize recurring motif families.
   - Identify missing functions and bottlenecks.
   - Identify promising topology classes.
   - Compare material/environment classes at a high level.
   - Link every conclusion back to candidate rows/files.

Possible future command:

```bash
silive hypothesis-report outputs/evolution --output outputs/hypotheses.md
```

## Desired end state

The desired result is a reproducible command-line research pipeline:

```text
candidate motifs in
  → graph/features/proto-genes/proto-genome score
  → ranked candidates and evolved variants
  → report explaining which motif families work best and why
```

The value of the project is not one hard-coded candidate. The value is the pipeline for testing many motif assumptions, comparing them consistently, and showing what functions are missing from each candidate.
