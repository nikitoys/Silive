# Codex Prompts

Copy and adapt these prompts for future sessions.

## Primary Project Analysis

```text
Inspect this repository without changing files. Identify the stack, entrypoints, package/test/build commands, key modules, documentation, CI, ignored files, and potential risks. Summarize what to read first and what checks are available.
```

## Cleanup Project

```text
Prepare this repository for a clean baseline. First verify git status is clean. Then identify temporary files, local tool configs, generated artifacts, duplicate docs, and missing .gitignore entries. Show a cleanup plan before editing. Do not change application logic. After safe cleanup, run available tests/build/smoke checks and commit with a clear chore message. Do not push.
```

## Restore Project Memory

```text
Restore compact project memory without reverting cleanup. Read deleted docs from the previous commit, extract unique useful context, and update AGENTS.md, PROJECT_GOAL.md, CODEX_TASKS.md, docs/ai/TODO.md, docs/ai/DECISIONS.md, docs/ai/MCP.md, docs/ai/PROMPTS.md, and example MCP configs. Do not commit real local configs or secrets.
```

## Verify Run

```text
Run the available safe checks for this Python project: tests, package build, and CLI smoke help. Use commands documented in README/RUNBOOK/pyproject/CI. If dependencies are missing, report exactly what failed and do not claim success.
```

## Update Documentation

```text
Update documentation only for the current change. Keep README concise. Update CODEX_TASKS.md for task state, docs/ai/TODO.md for follow-up work, docs/ai/DECISIONS.md for durable decisions, and docs/ai/MCP.md for MCP workflow changes. Do not add long duplicate AI docs.
```

## Safe Refactor

```text
Make a small, behavior-preserving refactor. Read the relevant tests and modules first. Do not change public CLI commands, output schemas, model assumptions, or optional RDKit behavior unless explicitly requested. Run pytest and a relevant CLI smoke test before summarizing.
```

