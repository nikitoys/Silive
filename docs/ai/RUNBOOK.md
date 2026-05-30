# Runbook

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Optional RDKit support:

```bash
python -m pip install -e '.[chem]'
```

No required `.env` file was found. Do not commit real local secrets or `.env` files.

Sources: `README.md`, `pyproject.toml`, repository file tree.

## Run

```bash
silive --help
silive evaluate-chain "Si-O-Si-O-Fe-O-Si"
silive simulate --generations 100 --population-limit 100 --genes POL SEP SHELL REPAIR
```

Without editable install:

```bash
PYTHONPATH=src python3 -m silive.cli --help
```

Sources: `src/silive/cli.py`, `README.md`.

## Test

```bash
pytest
```

RDKit-specific tests require the `chem` extra. In the base CI job, missing RDKit is accepted for RDKit command smoke tests.

Sources: `pyproject.toml`, `.github/workflows/ci.yml`, `tests/`.

## Build

No release workflow is configured. To verify package build locally:

```bash
python -m pip install build
python -m build
```

This command is inferred from the standard `pyproject.toml` build backend and should be verified before release.

Sources: `pyproject.toml`.

