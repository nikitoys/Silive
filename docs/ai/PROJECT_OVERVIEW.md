# Project Overview

## Summary

Silive is a Python sandbox for exploring a simplified silicon/mineral proto-life model. It evaluates symbolic chains and optional RDKit molecular inputs, maps them to proto-life functions, runs simulations/searches, and generates reports.

Sources:

- `README.md`
- `PROJECT_GOAL.md`
- `CODEX_TASKS.md`
- `pyproject.toml`

## Stack

- Language: Python.
- Required Python version: `>=3.10`.
- Packaging/build backend: `setuptools.build_meta`.
- Project layout: `src/` package layout.
- CLI framework: Python standard library `argparse`.
- Test framework: `pytest`.
- Plotting dependency: optional `matplotlib`.
- Chemistry dependency: optional `rdkit-pypi`.
- CI: GitHub Actions.

Sources:

- `pyproject.toml`
- `src/silive/cli.py`
- `.github/workflows/ci.yml`
- `src/silive/plot.py`
- `src/silive/rdkit_chemistry.py`

## Package Metadata

Package name: `silive`.

Current version: `0.1.0`.

Description from package metadata: `Level 1 chemical-logical simulator for silicon-like proto-life`.

Runtime dependencies are empty in the base package. Optional dependency groups are:

- `dev`: `pytest>=8.0`, `matplotlib>=3.8`.
- `plot`: `matplotlib>=3.8`.
- `chem`: `rdkit-pypi>=2022.9.5`.

Sources:

- `pyproject.toml`

## Main Capabilities

The project currently includes:

- Level 1 symbolic proto-organism simulation.
- Level 2 symbolic chain scoring.
- Chain simulation/report generation.
- Environment sweep and niche search.
- Optional RDKit molecule parsing and scoring.
- Symbolic graph extraction and graph diff.
- Proto-gene and proto-genome scoring.
- Batch RDKit candidate search.
- Abstract reaction scoring.
- Evolutionary motif search.
- Hypothesis/report generation.

Sources:

- `README.md`
- `PROJECT_GOAL.md`
- `CODEX_TASKS.md`
- `src/silive/cli.py`
- `src/silive/__init__.py`

## Repository Shape

Top-level project files:

- `README.md`: user-facing project overview and CLI examples.
- `pyproject.toml`: packaging, dependencies, console script, pytest config.
- `.github/workflows/ci.yml`: CI test and smoke-run workflow.
- `.gitignore`, `.gitattributes`: repository metadata.
- `PROJECT_GOAL.md`: project intent and pipeline.
- `CODEX_TASKS.md`: roadmap/status notes.

Main directories:

- `src/silive`: application package.
- `tests`: pytest suite.
- `docs`: feature documentation.
- `examples`: sample candidate input files.

Sources:

- repository file tree
- `pyproject.toml`
- `.github/workflows/ci.yml`

## Not Found

The following were not found during analysis:

- `Dockerfile`.
- Docker Compose files.
- `requirements.txt`.
- `package.json`.
- `.env` or env example files.

Sources:

- repository file tree

