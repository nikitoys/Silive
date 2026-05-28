# Project task list for Silive

Use this file together with `PROJECT_GOAL.md` to understand the current project direction, implemented pipeline, and next work items.

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

1. Replace brute-force longest path with a graph algorithm that scales better for larger graphs.
2. Add explicit bridge classification:
   - siloxane bridge;
   - metal oxide bridge;
   - phosphate bridge;
   - labile bridge candidate.
3. Add graph serialization to JSON.
4. Add graph diff between parent and mutated candidate.

## Priority 4: improve evolutionary search

Current evolution mutates SMILES-like strings and sometimes creates unrealistic candidates.

Better next version:

1. Maintain a symbolic genome/motif object independent from SMILES.
2. Generate RDKit strings only when possible.
3. Track both:
   - `rdkit_valid_score`;
   - `symbolic_viability_score`.
4. Keep invalid symbolic candidates if they are useful for abstract search, but mark them clearly.

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

Output should include:

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
