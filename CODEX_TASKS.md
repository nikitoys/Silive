# Codex Tasks

Use this file as the live project board for Codex sessions. Keep it short and current.

## Last Known Starting Point

- Baseline cleanup commit: `1098720935d0c73930fbc74db4b3fc0b21d5a5f1`.
- Project-memory restore commit: latest `docs: restore project memory and codex workflow` commit; confirm with `git log --oneline -3`.
- Latest verified checks before this restore:
  - `uv run --extra dev pytest -q` -> `74 passed, 30 skipped`.
  - `uv run --with build python -m build` -> sdist and wheel built.
  - `uv run --extra dev silive --help` -> CLI help printed.
- RDKit remains optional; base CI accepts missing RDKit for RDKit smoke commands.

## In Progress

- None.

## Backlog

- Add a CI package-build smoke check if package artifacts matter before release.
- Decide whether to add an optional RDKit CI job for `.[chem]` compatibility.
- Review whether `src/silive/cli.py` should stay as one router or split by command group once command count grows further.
- Review `src/silive/__init__.py` public exports if the package API becomes a stability target.
- Keep symbolic graph and evolutionary search scalability under review for larger candidate sets.

## Done

- Added `docs/ai/CODEX_WORKFLOW.md` with short operator commands for planning,
  approval, execution, status, stop, cancel, continue, and commit flow.
- Added proto-gene evidence framework with corpus expectations, null controls, ablation summaries, CLI, docs, and report outputs.
- Stabilized repository line endings with `.gitattributes`.
- Retired old CLI wrapper indirection; `silive.cli:main` is the stable entrypoint.
- Added symbolic graph bridge classification, JSON serialization, and graph diff.
- Added symbolic genome representation and separate RDKit-valid/symbolic-viability scoring.
- Preserved useful invalid symbolic candidates with risk flags.
- Added hypothesis/report layer.
- Cleaned baseline documentation and removed local tool configs / Node lockfile noise.
- Restored compact project memory and Codex/MCP workflow notes.
- Added Codex/MCP bootstrap workflow for post-clone setup.

## Blocked / Questions

- Should RDKit support be tested in CI or remain local/manual only?
- Is a package publish workflow planned, or is local build verification enough?
- Should Docker support exist? No Dockerfile or compose setup is currently present.
- Are generated `outputs/` only local/CI artifacts? Current baseline ignores them.

## How To Update This File

- Move active work into `In Progress`.
- Move completed work into `Done` with the relevant commit hash when known.
- Put unclear product/architecture choices in `Blocked / Questions`.
- Keep implementation details in PRs/commits; keep this file as the session handoff board.
