# Silive

Silive is a small Python sandbox for testing symbolic silicon/mineral proto-life models. It scores symbolic chains, optionally evaluates RDKit molecules, runs search/simulation workflows, and writes simple reports.

The project is computational only. It does not provide synthesis protocols, lab parameters, quantities, temperatures, pressures, timings, or operational experimental instructions.

## Stack

- Python `>=3.10`
- Packaging: `setuptools` via `pyproject.toml`
- CLI: `silive`, implemented in `src/silive/cli.py`
- Tests: `pytest`
- Optional plotting: `matplotlib`
- Optional chemistry layer: `rdkit-pypi`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Optional RDKit support:

```bash
python -m pip install -e '.[chem]'
```

## Continue After Clone

```bash
git clone <repo-url> Silive
cd Silive
make codex-setup
codex
```

`make codex-setup` installs the example MCP config into `~/.codex/config.toml`, backing up an existing config first. Real local configs are not committed:

- `~/.codex/config.toml` is machine-local.
- `.codex/config.toml` is ignored.
- `.serena/project.yml` is ignored.
- tracked templates live in `.codex/config.example.toml` and `.serena/project.example.yml`.

After Codex starts, check MCP status with `/mcp`, then read `AGENTS.md`, `PROJECT_GOAL.md`, and `CODEX_TASKS.md`.

## Run

Show available commands:

```bash
silive --help
```

Run one symbolic chain evaluation:

```bash
silive evaluate-chain "Si-O-Si-O-Fe-O-Si"
```

Run one Level 1 simulation:

```bash
silive simulate --generations 100 --population-limit 100 --genes POL SEP SHELL REPAIR
```

Run an environment-specific chain evaluation:

```bash
silive evaluate-chain "Si-O-Si-O-Fe-O-Si" --environment hydrothermal
```

Run an RDKit evaluation after installing `.[chem]`:

```bash
silive rdkit-evaluate "[Si]O[Si]O[Fe]O[Si]"
```

Without editable install, commands can be run from the repository root with:

```bash
PYTHONPATH=src python3 -m silive.cli --help
```

## Build

No release workflow is configured. A local package build can be checked with:

```bash
python -m pip install build
python -m build
```

## Test

```bash
pytest
```

GitHub Actions runs tests on Python 3.10, 3.11, and 3.12 and performs CLI smoke tests. RDKit commands are treated as optional in the base CI job.

## Environment

No required `.env` file is currently documented or needed for normal local use.

Do not commit real secrets, tokens, credentials, private keys, or local `.env` files.

## Documentation

- Continue after clone: read [AGENTS.md](AGENTS.md), [PROJECT_GOAL.md](PROJECT_GOAL.md), and [CODEX_TASKS.md](CODEX_TASKS.md) first.
- Developer runbook: [docs/ai/RUNBOOK.md](docs/ai/RUNBOOK.md)
- Project overview: [docs/ai/PROJECT_OVERVIEW.md](docs/ai/PROJECT_OVERVIEW.md)
- Technical TODO: [docs/ai/TODO.md](docs/ai/TODO.md)
- Decisions: [docs/ai/DECISIONS.md](docs/ai/DECISIONS.md)
- MCP notes: [docs/ai/MCP.md](docs/ai/MCP.md)
- Reusable Codex prompts: [docs/ai/PROMPTS.md](docs/ai/PROMPTS.md)

Codex/MCP config templates:

- `.codex/config.example.toml`
- `.serena/project.example.yml`
- Bootstrap script: `scripts/bootstrap-codex.sh`

Real local `.codex/config.toml` and `.serena/project.yml` files are intentionally ignored.

Feature docs:

- [RDKit layer](docs/rdkit.md)
- [RDKit search](docs/rdkit_search.md)
- [Symbolic graph](docs/symbolic_graph.md)
- [Proto-genes](docs/proto_genes.md)
- [Proto-genome](docs/proto_genome.md)
- [Proto-gene lineage](docs/proto_gene_lineage.md)
- [Reaction simulator](docs/reaction_simulator.md)
- [Evolutionary search](docs/evolutionary_search.md)
- [Hypothesis layer](docs/hypothesis_layer.md)
