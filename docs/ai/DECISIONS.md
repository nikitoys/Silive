# Decisions

ADR-style log for durable project/process decisions.

## ADR Template

### ADR-N: Title

- Date: YYYY-MM-DD
- Status: proposed | accepted | superseded | rejected
- Context:
  - What problem or tradeoff is being addressed?
- Decision:
  - What was decided?
- Consequences:
  - Positive outcomes.
  - Tradeoffs and follow-up work.

## ADR-001: Keep Project Memory In Documentation

- Date: 2026-05-30
- Status: accepted
- Context:
  - Cleanup commit `1098720935d0c73930fbc74db4b3fc0b21d5a5f1` removed bulky AI/project-management documents.
  - After clone, future Codex sessions still need project intent, task state, decisions, MCP notes, and prompts.
- Decision:
  - Keep compact project memory in `AGENTS.md`, `PROJECT_GOAL.md`, `CODEX_TASKS.md`, and `docs/ai/`.
  - Do not commit real local `.codex/config.toml` or `.serena/project.yml`; commit example files instead.
- Consequences:
  - New sessions can resume without relying on hidden local state.
  - Documentation must be maintained as part of project changes.

## ADR-002: Cleanup Baseline Keeps Code Untouched

- Date: 2026-05-30
- Status: accepted
- Context:
  - The repository needed a clean first-push baseline without tool caches, local configs, or duplicated docs.
- Decision:
  - Cleanup removed local tool configs, empty Node lockfile noise, and bulky duplicate AI docs while preserving application code and tests.
- Consequences:
  - Baseline is cleaner for push.
  - Some useful project memory had to be restored later in compact form.
