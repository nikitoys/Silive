# AGENTS.md

Instructions for future Codex sessions in this repository.

## Project Purpose

Silive is a Python sandbox for a simplified silicon/mineral proto-life model. It evaluates symbolic chains and optional RDKit molecular inputs, maps them to proto-life functions, runs simulations/searches, and writes reports.

Sources: `README.md`, `PROJECT_GOAL.md`, `pyproject.toml`.

## Project Map

- `src/silive/`: application package.
- `src/silive/cli.py`: main CLI router and primary entrypoint implementation.
- `pyproject.toml`: package metadata, optional dependencies, pytest config, console script `silive = silive.cli:main`.
- `tests/`: pytest suite.
- `docs/`: feature documentation.
- `docs/ai/`: AI-oriented project notes, runbook, audit, TODOs, and decision log.
- `examples/`: sample candidate inputs.
- Docker setup: TBD, no Dockerfile or compose file found.
- Env template: TBD, no `.env.example` found.

## Code Change Rules

- Keep changes small and scoped to the requested behavior.
- Prefer existing module boundaries and patterns over new abstractions.
- Do not rewrite the CLI, package structure, or public exports unless explicitly requested.
- Do not change scientific/model assumptions silently; document any scoring, heuristic, or simulation behavior change.
- Preserve optional RDKit behavior: base install should work without RDKit, and RDKit-specific code should fail with clear optional-dependency messaging.

## Testing Rules

- For normal code changes, run `pytest` after installing dev dependencies.
- If editable install is needed: `python -m pip install -e '.[dev]'`.
- If testing without install from repo root, use `PYTHONPATH=src python3 -m pytest` after pytest is available.
- For CLI changes, run at least `silive --help` and a relevant command smoke test.
- For RDKit changes, also test with `python -m pip install -e '.[chem]'` when RDKit is available; otherwise note that RDKit verification is skipped.
- If tests cannot be run because dependencies are missing, state exactly what was missing.

## Documentation Rules

- Update README only with focused, minimal edits.
- Keep `docs/ai/*.md` synchronized when architecture, setup, risks, or decisions change.
- For new decisions, add an ADR-style entry to `docs/ai/DECISIONS.md`.
- If a fact is not verified from the repository, mark it as `TBD` or `requires verification`.

## Security Rules

- Do not add secrets, API keys, credentials, tokens, private keys, or real `.env` values.
- Do not commit generated outputs that may contain sensitive local paths or experiment data unless explicitly requested.
- Treat RDKit/molecule functionality as computational simulation only; do not add lab protocols, synthesis instructions, quantities, temperatures, pressures, or operational wet-lab steps.

## Do Not Do Without Explicit Permission

- Do not modify application source code for documentation-only tasks.
- Do not delete or overwrite untracked user files.
- Do not run destructive git commands such as `git reset --hard` or `git checkout --`.
- Do not add Docker, package managers, formatters, linters, or new dependencies unless asked.
- Do not change model/scoring behavior, CLI command names, output schemas, or test expectations as incidental cleanup.

## Useful Docs

- `docs/ai/PROJECT_OVERVIEW.md`
- `docs/ai/ARCHITECTURE.md`
- `docs/ai/RUNBOOK.md`
- `docs/ai/AUDIT.md`
- `docs/ai/TODO.md`
- `docs/ai/DECISIONS.md`
