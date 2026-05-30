# Runbook

## Prerequisites

Required:

- Python `>=3.10`.

Recommended for local development:

- A virtual environment.
- `pip`.

In the analyzed environment, `python3` was available but `python`, `pip`, and `pytest` were not available globally. This is environment-specific and requires verification on each machine.

Sources:

- `pyproject.toml`
- local command checks during analysis

## Install for Development

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

The README uses `python` in examples. If `python` is not available on the target machine, use `python3` to create the virtual environment, then use `python` from the activated environment.

Sources:

- `README.md`
- `pyproject.toml`

## Install Optional Extras

Plotting only:

```bash
python -m pip install -e '.[plot]'
```

RDKit chemistry layer:

```bash
python -m pip install -e '.[chem]'
```

Development install already includes `matplotlib`, but it does not include RDKit.

Sources:

- `pyproject.toml`
- `README.md`
- `src/silive/rdkit_chemistry.py`
- `src/silive/plot.py`

## Environment Variables

No required `.env` file or env example was found.

For running without editable install, this works from the repository root:

```bash
PYTHONPATH=src python3 -m silive.cli --help
```

Sources:

- repository file tree
- `pyproject.toml`
- local command checks during analysis

## Run the CLI

After editable install:

```bash
silive --help
```

Run a symbolic chain evaluation:

```bash
silive evaluate-chain "Si-O-Si-O-Fe-O-Si"
```

Run one simulation:

```bash
silive simulate --generations 100 --population-limit 100 --genes POL SEP SHELL REPAIR
```

Run an environment-specific symbolic chain evaluation:

```bash
silive evaluate-chain "Si-O-Si-O-Fe-O-Si" --environment hydrothermal
```

Sources:

- `README.md`
- `src/silive/cli.py`

## Run RDKit Commands

Install the chemistry extra first:

```bash
python -m pip install -e '.[chem]'
```

Then run:

```bash
silive rdkit-evaluate "[Si]O[Si]O[Fe]O[Si]"
```

If RDKit is not installed, RDKit commands are expected to exit with an optional-dependency message:

```text
RDKit is not installed. Install the optional dependency with: pip install -e .[chem]
```

Sources:

- `README.md`
- `docs/rdkit.md`
- `src/silive/rdkit_chemistry.py`
- `.github/workflows/ci.yml`

## Run Tests

After installing development dependencies:

```bash
pytest
```

The CI runs tests on Python 3.10, 3.11, and 3.12.

Sources:

- `README.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`

## Smoke Runs Used by CI

CI performs:

- package install with `python -m pip install -e .[dev]`;
- `pytest`;
- symbolic smoke tests;
- optional RDKit command smoke tests where missing RDKit is accepted;
- chain search/simulation/report smoke tests;
- environment sweep and niche search smoke tests;
- `lab` and `repair-study` smoke tests;
- upload of generated `outputs/` artifacts.

Sources:

- `.github/workflows/ci.yml`

## Build Package

No explicit build command is documented in `README.md`.

Because the project uses standard `pyproject.toml` packaging with setuptools, a source/wheel build should be possible with the standard Python build frontend after installing `build`:

```bash
python -m pip install build
python -m build
```

This build command is inferred from `pyproject.toml` and requires verification because it is not documented or run by CI.

Sources:

- `pyproject.toml`
- `README.md`
- `.github/workflows/ci.yml`

## Docker

No Dockerfile or compose file was found. Docker-based local setup is not documented.

Sources:

- repository file tree

