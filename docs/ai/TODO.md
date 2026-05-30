# TODO

## Quick Wins

- Fix the broken fenced code block in `README.md` near the RDKit example.
  - Source: `README.md`.
- Decide whether to remove, commit, or ignore untracked `package-lock.json`.
  - Source: repository file tree and `git status --short`.
- Add a note to README that `python3` may be needed before virtualenv activation on systems without a `python` command.
  - Source: `README.md` and local command checks.
- Run tests in a fresh virtual environment with `python -m pip install -e '.[dev]'`.
  - Source: `README.md`, `pyproject.toml`, `.github/workflows/ci.yml`.
- Add an explicit local build verification command to docs if packaging is important.
  - Source: `pyproject.toml`, `README.md`.

## Medium Tasks

- Add a documented optional RDKit test path, including expected skip/failure behavior when RDKit is missing.
  - Source: `pyproject.toml`, `docs/rdkit.md`, `.github/workflows/ci.yml`.
- Add CI job or manual checklist for `.[chem]` compatibility if RDKit functionality is important.
  - Source: `pyproject.toml`, `.github/workflows/ci.yml`.
- Consider splitting `src/silive/cli.py` into command-focused modules if command count continues growing.
  - Source: `src/silive/cli.py`, `CODEX_TASKS.md`.
- Add packaging smoke check in CI, for example build sdist/wheel.
  - Source: `pyproject.toml`, `.github/workflows/ci.yml`.
- Add contributor setup notes for environments without global `pip` or `python`.
  - Source: local command checks, `README.md`.

## Large Refactoring

- Reassess CLI module organization around command groups: simulation, symbolic chemistry, RDKit, graph, reports.
  - Source: `src/silive/cli.py`.
- Review whether public exports in `src/silive/__init__.py` should remain broad or become more focused.
  - Source: `src/silive/__init__.py`.
- Evaluate whether optional RDKit functionality should have a separate integration-test workflow.
  - Source: `pyproject.toml`, `.github/workflows/ci.yml`, `tests/test_rdkit_*.py`.
- Review the symbolic graph and evolutionary search algorithms for scalability on larger candidate sets.
  - Source: `CODEX_TASKS.md`, `src/silive/symbolic_graph.py`, `src/silive/evolutionary_search.py`.

## Questions / Unknowns

- Should `package-lock.json` exist in this repository?
  - Source: repository file tree.
- Is RDKit support required in CI, or intentionally optional only?
  - Source: `pyproject.toml`, `.github/workflows/ci.yml`.
- Should the project support Docker-based setup?
  - Source: Docker files not found.
- Are generated `outputs/` intended to be ignored, cleaned, or archived only in CI?
  - Source: `.github/workflows/ci.yml`, `.gitignore`.
- Is `python` acceptable in docs, or should all setup commands use `python3` until virtualenv activation?
  - Source: `README.md`, local command checks.
- Is wheel/sdist publication planned?
  - Source: `pyproject.toml`; publishing config not found.

