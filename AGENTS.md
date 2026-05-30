# AGENTS.md

Instructions for future Codex sessions in this repository.

## Start Here

Read these first, in order:

1. `README.md` for install/run/test basics.
2. `PROJECT_GOAL.md` for the research direction and success criteria.
3. `docs/ai/CODEX_WORKFLOW.md` for operator commands and One-Task Loop rules.
4. `CODEX_COMMANDS.md` for the short operator command cheat sheet.
5. `CODEX_PLAN.md` for the current planning snapshot.
6. `CODEX_CURRENT.md` for the active task state.
7. `CODEX_SESSION_LOG.md` for recent One-Task Loop cycles.
8. `CODEX_TASKS.md` for current work state.
9. `docs/ai/RUNBOOK.md` for commands.
10. `docs/ai/MCP.md` if MCP tools are needed.

## Purpose

Silive is a Python sandbox for symbolic silicon/mineral proto-life simulation, search, and reporting. It is computational only; do not add wet-lab protocols, synthesis steps, quantities, temperatures, pressures, timings, or operational experimental instructions.

## Project Map

- `src/silive/`: application package.
- `src/silive/cli.py`: main CLI router.
- `pyproject.toml`: package metadata, extras, pytest config, and `silive = silive.cli:main`.
- `tests/`: pytest suite.
- `docs/`: feature docs.
- `docs/ai/`: Codex workflow, TODOs, MCP notes, prompts, and decisions.
- `examples/rdkit_candidates.smi`: sample RDKit candidate input.

## Work Rules

- Keep code changes small and scoped.
- Prefer existing module boundaries and test style.
- Do not change model/scoring behavior, CLI commands, output schemas, or public APIs as incidental cleanup.
- Preserve optional RDKit behavior: base install should work without RDKit.
- Do not add secrets, tokens, credentials, private keys, or real `.env` values.
- Do not delete project-memory docs unless the useful content is moved elsewhere.
- Do not run destructive git commands or push without explicit permission.

## Documentation Rules

- Update `CODEX_TASKS.md` whenever task status changes.
- Update `docs/ai/TODO.md` when adding or retiring technical follow-up work.
- Add ADR entries to `docs/ai/DECISIONS.md` for durable project/process decisions.
- Update `docs/ai/MCP.md` when adding, removing, or troubleshooting MCP usage.
- After changing Codex/MCP workflow, update `scripts/bootstrap-codex.sh`, `docs/ai/MCP.md`, and `README.md` together.
- Keep `PROJECT_GOAL.md` high-level and stable; do not turn it into a changelog.
- Mark unverified facts as `TBD` or `requires verification`.

## Checks

- Normal changes: `uv run --extra dev pytest -q`.
- Build check: `uv run --with build python -m build`.
- CLI smoke: `uv run --extra dev silive --help`.
- RDKit changes: test with `.[chem]` when available; otherwise state that RDKit verification was skipped.
- If a check cannot run, report the exact missing dependency or command.

## MCP Notes

- Use MCP only when it helps. Do not commit real machine-specific `.codex/config.toml` or `.serena/project.yml`.
- Keep examples in `.codex/config.example.toml` and `.serena/project.example.yml`.
- `make codex-setup` runs `scripts/bootstrap-codex.sh` to install the example config into `~/.codex/config.toml`.
- Record MCP setup issues or useful workflows in `docs/ai/MCP.md`.
