# Project Goal

Silive is a computational toy model for exploring whether symbolic silicon/mineral motif systems can be scored as minimal proto-life-like pipelines.

The practical goal is a reproducible command-line research workflow:

```text
candidate symbolic chain or RDKit molecule
  -> graph/topology features
  -> proto-gene motif detection
  -> minimal proto-genome coverage score
  -> search/evolution/ranking outputs
  -> report explaining promising motif families and missing functions
```

## Current Direction

The project should make heuristic assumptions explicit and testable. A candidate is interesting when it can cover or approximate these model functions:

- `TEMPLATE`: stores or repeats a structural pattern.
- `POLYMERIZE`: extends a chain, scaffold, or network.
- `CATALYZE`: contains a catalytic-center-like motif.
- `SEPARATE`: can release a copied fragment or split a labile part.
- `PROTECT`: has a shell/matrix/network feature that improves persistence.
- `REPAIR`: has a bridge or motif that can stabilize/correct defects.

Current motif interpretations include:

- `Si-O-Si` repeats as template/scaffold and polymer-growth signal.
- longer Si/O chains or networks as persistence/growth signal.
- Si/O rings or dense networks as protection/stability signal.
- `Fe-O` or `Ni-O` centers as catalysis signal.
- `P-O` bridges as repair/defect-stabilization signal.
- labile bridges, terminal handles, or separated fragments as separation/copy-release signal.

## Implemented Baseline

The current codebase includes:

- Level 1 symbolic simulator.
- Level 2 symbolic chain scoring.
- RDKit parsing as an optional layer.
- symbolic graph extraction and diffing.
- proto-gene and proto-genome scoring.
- candidate search, reaction scoring, evolutionary search.
- hypothesis/report generation.
- pytest coverage and GitHub Actions smoke tests.

## Successful Starting Point

A clean starting point means:

- `README.md` explains install, run, build, test, and env expectations.
- `AGENTS.md`, `CODEX_TASKS.md`, and `docs/ai/*` preserve enough project memory for future Codex sessions.
- base tests pass without RDKit.
- RDKit remains optional and clearly documented.
- no real secrets, local machine configs, caches, or generated outputs are committed.
