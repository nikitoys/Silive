# Decisions

This file is an ADR-style decision log for future technical decisions.

No project decisions were made as part of this documentation pass. The entries below are templates to use when a decision is made.

## ADR Template

### ADR-N: Title

Status: proposed | accepted | superseded | rejected

Date: YYYY-MM-DD

Context:

- What problem or tradeoff is being addressed?
- What files, modules, or workflows are affected?
- What constraints matter?

Decision:

- What was decided?

Consequences:

- Positive outcomes.
- Negative outcomes or tradeoffs.
- Follow-up work.

Sources:

- `path/to/source`

## ADR-001: Documentation Snapshot

Status: accepted

Date: 2026-05-30

Context:

- The repository needed AI-readable project documentation derived from static analysis.
- The task explicitly required no application code or business logic changes.

Decision:

- Add `docs/ai/` documentation files covering overview, architecture, runbook, audit, TODOs, and this decision log.

Consequences:

- Future agents and developers have a concise orientation layer.
- The documentation must be kept in sync as project structure, dependencies, and workflows change.

Sources:

- `README.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `PROJECT_GOAL.md`
- `CODEX_TASKS.md`
- `src/silive/`
- `tests/`

