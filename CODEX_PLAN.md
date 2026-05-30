# Codex Plan

Use this file as the durable planning snapshot for Codex operator commands.
Refresh it during `План` when priorities change.

## Research Focus

Silive should remain a computational sandbox for symbolic silicon/mineral
proto-life simulation, search, scoring, and reporting. Near-term work should
improve reproducibility, make heuristic assumptions explicit and testable, and
preserve the base install without RDKit.

## Nearest Tasks

### 1. Proto-Gene Evidence Calibration

- Goal: calibrate thresholds and null-enrichment cutoffs against a broader
  expected-behavior corpus.
- Expected result: clearer criteria for distinguishing promising symbolic
  candidates from null/random baselines.
- Value: directly strengthens the scientific usefulness of the model by
  reducing arbitrary heuristic behavior.
- Files likely touched: `examples/proto_gene_evidence_corpus.csv`,
  `src/silive/*proto*`, `tests/*proto*`, `docs/proto_gene_evidence.md`,
  `CODEX_TASKS.md`.
- Definition of done: corpus cases and tests cover expected behavior; docs
  explain threshold intent without wet-lab instructions.
- Main check: `uv run --extra dev pytest -q`.
- Negative checks: null/random candidates do not score too highly; base install
  still works without RDKit.
- Risk: scoring semantics could change too broadly.

### 2. Document Report And Output Schema Stability

- Goal: mark key report, JSON, and CSV outputs as stable or experimental.
- Expected result: future changes have a clear compatibility target.
- Value: protects the reproducible research workflow from accidental output
  breakage.
- Files likely touched: `docs/`, `README.md`, `CODEX_TASKS.md`.
- Definition of done: main outputs have documented stability expectations and
  compatibility notes.
- Main check: `uv run --extra dev pytest -q`.
- Negative checks: do not change schemas as a side effect; do not promise
  stability for experimental outputs.
- Risk: documenting a contract too early could constrain useful iteration.

### 3. Add CI Package Build Smoke Check

- Goal: add a CI check for `uv run --with build python -m build`.
- Expected result: package build regressions are caught automatically.
- Value: packaging is part of the reproducible command-line workflow.
- Files likely touched: `.github/workflows/ci.yml`, `README.md`,
  `docs/ai/RUNBOOK.md`, `CODEX_TASKS.md`.
- Definition of done: CI performs a package build without committing generated
  artifacts.
- Main check: `uv run --with build python -m build`.
- Negative checks: RDKit remains optional in the base CI path; `dist/` is not
  committed.
- Risk: CI runtime may increase.

### 4. Add Compact CLI Smoke Command Matrix

- Goal: document safe smoke commands for core base and RDKit-optional CLI
  workflows.
- Expected result: future sessions can verify changes with less guesswork.
- Value: improves reproducibility and reduces incomplete manual verification.
- Files likely touched: `docs/ai/RUNBOOK.md`, `README.md`, `docs/ai/TODO.md`,
  `CODEX_TASKS.md`.
- Definition of done: runbook lists compact commands, expected behavior, and
  RDKit skip policy.
- Main check: `uv run --extra dev silive --help`.
- Negative checks: avoid large generated outputs; keep RDKit commands optional.
- Risk: docs can become noisy if the matrix is too broad.

### 5. Review Package Public Exports

- Goal: decide whether `src/silive/__init__.py` exports are public API or
  experimental conveniences.
- Expected result: reduced accidental API promises before broader reuse.
- Value: helpful before API stabilization, but lower priority than research
  calibration and reproducibility.
- Files likely touched: `src/silive/__init__.py`, import tests, docs,
  `CODEX_TASKS.md`.
- Definition of done: exports are minimized or clearly documented as
  experimental.
- Main check: `uv run --extra dev pytest -q`.
- Negative checks: CLI imports keep working; public behavior is not changed
  without an explicit decision.
- Risk: import compatibility could break if existing users rely on exports.
