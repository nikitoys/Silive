# Project task list for Silive

Use this file together with `PROJECT_GOAL.md` to understand the current project direction, implemented pipeline, and next work items.

## Roadmap status table

Use this table as the main progress tracker. Keep the detailed priority sections below for context and acceptance notes.

| Priority | Work item | Status | Next concrete step |
| --- | --- | --- | --- |
| P0 | Stabilize line endings with `.gitattributes` | Done | Already committed and pushed. |
| P1 | Verify current code health | Done | Keep running `pytest` before each commit; current baseline is `74 passed, 30 skipped` without RDKit. |
| P2 | Retire CLI wrapper chain | Done | Push commit `ac1a11b` if it is not on `origin/main` yet. |
| P3.1 | Replace brute-force symbolic backbone search | Done | Push commit `599871b` if it is not on `origin/main` yet. |
| P3.2 | Add explicit symbolic bridge classification | Done | Keep bridge tags/properties covered by `tests/test_symbolic_graph_core.py`. |
| P3.3 | Add symbolic graph JSON serialization | Done | Keep `SymbolicGraph.to_dict()`/JSON helpers and `rdkit-graph-evaluate --json-output` covered by tests/docs. |
| P3.4 | Add graph diff between parent and mutated candidates | Done | Keep compact diff output covered for topology tags, bridge counts, backbone length, fragments, and motif counts. |
| P4.1 | Introduce symbolic genome/motif object independent from SMILES | Done | Keep `SymbolicGenome` parsing/rendering and mutation delegation covered without RDKit. |
| P4.2 | Track `rdkit_valid_score` and `symbolic_viability_score` separately | Done | Keep separate RDKit validity and symbolic viability fields in candidate/evolution outputs. |
| P4.3 | Preserve useful invalid symbolic candidates | Done | Keep symbolic-only invalid candidates marked with risk flags and preservation reasons. |
| P5.1 | Add hypothesis/report layer | Done | Keep `src/silive/hypothesis_layer.py` and `silive hypothesis-report` covered by tests/docs. |
| P5.2 | Summarize motifs, bottlenecks, missing functions, and topology classes | Done | Keep motif, bottleneck, topology, material, environment, and source-row sections in the Markdown report. |

## First checks

Run these in a fresh environment:

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest
```

Then, if RDKit install is available:

```bash
python -m pip install -e .[chem]
pytest
silive rdkit-search examples/rdkit_candidates.smi --output outputs/rdkit_search.csv --top 20
silive rdkit-reaction-search examples/rdkit_candidates.smi --output outputs/reaction_search.csv --top 20
silive rdkit-evolve examples/rdkit_candidates.smi --generations 5 --population-size 10 --elite-size 3 --output-dir outputs/evolution --seed 42
```

## Priority 1: verify current code health

Check these likely fragility points:

1. RDKit parsing of unusual silicon/phosphate/metal strings.
2. Whether invalid SMILES always returns invalid evaluation instead of crashing.
3. Whether the single CLI router works after editable install:
   - `cli.py`.
4. Whether tests skip cleanly without RDKit.
5. Whether CI still passes with only `.[dev]` installed.

## Priority 2: cleanup task

Refactor the CLI wrappers into one clean router.

Status: done. The stable entry point is `silive.cli:main`, and old wrapper modules have been retired.

Old design:

```text
separate compatibility wrapper modules forwarding into the main CLI
```

Current design:

```text
cli.py
  handles all commands directly
```

Acceptance criteria:

- all existing commands still work;
- tests pass;
- `pyproject.toml` has a single stable entry point;
- no circular imports.

## Priority 3: improve symbolic graph quality

Possible improvements:

1. Replace brute-force longest path with a graph algorithm that scales better for larger graphs. Status: done.
2. Add explicit bridge classification. Status: done.
   - siloxane bridge;
   - metal oxide bridge;
   - phosphate bridge;
   - labile bridge candidate.
3. Add graph serialization to JSON. Status: done.
4. Add graph diff between parent and mutated candidate. Status: done.

## Priority 4: improve evolutionary search

Current evolution mutates SMILES-like strings and sometimes creates unrealistic candidates.

Better next version:

1. Maintain a symbolic genome/motif object independent from SMILES. Status: done.
2. Generate RDKit strings only when possible.
3. Track both:
   - `rdkit_valid_score`;
   - `symbolic_viability_score`. Status: done.
4. Keep invalid symbolic candidates if they are useful for abstract search, but mark them clearly. Status: done.

## Priority 5: add hypothesis/report layer

Recommended new module:

```text
src/silive/hypothesis_layer.py
```

Recommended CLI:

```bash
silive hypothesis-report outputs/evolution --output outputs/hypotheses.md
```

Inputs:

- `outputs/rdkit_search.csv`;
- `outputs/reaction_search.csv`;
- `outputs/evolution/final_population.csv`;
- `outputs/evolution/best_candidate.txt`;
- `outputs/evolution/summary.json`.

Status: done.

Output includes:

- top motif families;
- recurring bottlenecks;
- missing functions;
- promising topology classes;
- material classes to compare;
- environmental variables to compare;
- links back to the candidate rows/files that produced each observation.

## Suggested prompt for Codex

```text
Read PROJECT_GOAL.md and CODEX_TASKS.md. Inspect the current Silive repository. First run tests without RDKit and identify any failures. Then, if possible, run with RDKit. Your first task is to refactor the CLI wrapper chain into one clean command router while preserving all commands and tests.
```
