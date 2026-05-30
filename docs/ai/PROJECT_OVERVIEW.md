# Project Overview

Silive is a Python package for symbolic silicon/mineral proto-life simulations. It scores symbolic chains, optionally evaluates RDKit molecular inputs, runs search/simulation workflows, and writes reports.

## Stack

- Python `>=3.10`
- `setuptools` package defined by `pyproject.toml`
- CLI entrypoint: `silive = silive.cli:main`
- Tests: `pytest`
- Optional extras:
  - `dev`: `pytest`, `matplotlib`
  - `plot`: `matplotlib`
  - `chem`: `rdkit-pypi`

Sources: `pyproject.toml`, `README.md`, `src/silive/cli.py`.

## Direction

See `PROJECT_GOAL.md` for the research goal, minimal proto-life functions, motif interpretations, and successful baseline definition.

## Project Map

- `src/silive/model.py`: Level 1 proto-life simulation.
- `src/silive/chemistry.py`: symbolic chain parsing, scoring, mutation, search.
- `src/silive/cli.py`: main command router.
- `src/silive/rdkit_chemistry.py`: optional RDKit molecule parsing/evaluation.
- `src/silive/symbolic_graph.py`: topology extraction, graph JSON, graph diff.
- `src/silive/proto_genes.py` and `src/silive/proto_genome.py`: motif and minimal function scoring.
- `src/silive/reaction_simulator.py` and `src/silive/evolutionary_search.py`: abstract reaction/evolution workflows.
- `src/silive/hypothesis_layer.py`: Markdown report generation from search outputs.
- `tests/`: pytest coverage for the main modules.
- `docs/`: feature documentation.
- `CODEX_TASKS.md`: live task board for Codex sessions.
- `docs/ai/MCP.md`: MCP/tooling notes.
- `docs/ai/PROMPTS.md`: reusable Codex prompts.
- `examples/rdkit_candidates.smi`: sample candidate input.

Sources: `src/silive/`, `tests/`, `docs/`, `examples/`.

## Not Found

- Dockerfile or compose file: TBD.
- Required `.env` or `.env.example`: TBD.
- `requirements.txt`: not used; dependencies are in `pyproject.toml`.
