# AGENTS.md

Instructions for future Codex sessions in this repository.

## Purpose

Silive is a Python sandbox for symbolic silicon/mineral proto-life simulation, search, and reporting. It is computational only; do not add wet-lab protocols or operational synthesis instructions.

## Map

- `src/silive/`: application package.
- `src/silive/cli.py`: main CLI router.
- `pyproject.toml`: package metadata, dependencies, pytest config, and `silive = silive.cli:main`.
- `tests/`: pytest suite.
- `docs/`: feature docs.
- `docs/ai/PROJECT_OVERVIEW.md`: compact project map.
- `docs/ai/RUNBOOK.md`: setup, run, test, build notes.

## Rules

- Keep code changes small and scoped.
- Do not change model/scoring behavior, CLI commands, output schemas, or public APIs as incidental cleanup.
- Preserve optional RDKit behavior: base install should work without RDKit.
- Update README or `docs/ai/` only when the change affects setup, architecture, or developer workflow.
- Do not add secrets, tokens, credentials, private keys, or real `.env` values.
- Do not delete user files or run destructive git commands without explicit permission.

## Checks

- Normal changes: run `pytest` after `python -m pip install -e '.[dev]'`.
- CLI changes: also run `silive --help` and a relevant command smoke test.
- RDKit changes: test with `python -m pip install -e '.[chem]'` when available; otherwise state that RDKit verification was skipped.
- If a check cannot run, report the exact missing dependency or command.
