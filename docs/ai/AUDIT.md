# Technical Audit

## Scope

This audit is based on static repository inspection and lightweight local smoke checks. No application source code was modified.

Sources:

- repository file tree
- `README.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `src/silive/`
- `tests/`

## Findings

### README Markdown Code Fence Is Broken

In `README.md`, the RDKit example opens a fenced bash block but does not close it before `## Symbolic environments`.

Impact:

- GitHub/Markdown rendering may treat subsequent documentation as code.
- Users may miss section headings and instructions.

Evidence:

- `README.md` around the `Experimental RDKit layer` section.

### `python` Command May Not Exist Locally

The README uses `python` in setup commands. In the analyzed environment, only `python3` was available globally.

Impact:

- Fresh local setup may fail with `python: command not found` on systems where `python` is not aliased.

Evidence:

- `README.md`
- local command checks during analysis

### Global `pip` and `pytest` Were Missing in the Analyzed Environment

The current system Python had no `pip` or `pytest` module available globally.

Impact:

- Tests cannot run until a virtual environment and dependencies are installed.

Evidence:

- local command checks during analysis
- `pyproject.toml` declares `pytest` only in the `dev` extra

### RDKit Is Optional and Not Installed by `dev`

The `dev` extra installs `pytest` and `matplotlib`, but not RDKit. RDKit commands require `.[chem]`.

Impact:

- RDKit tests and commands will be skipped or fail with the expected optional-dependency message unless `.[chem]` is installed.
- CI intentionally accepts missing RDKit for RDKit command smoke tests.

Evidence:

- `pyproject.toml`
- `src/silive/rdkit_chemistry.py`
- `.github/workflows/ci.yml`
- `tests/test_rdkit_chemistry.py`

### Untracked `package-lock.json` Without `package.json`

`package-lock.json` exists in the working tree but is untracked, and no `package.json` was found.

Impact:

- It appears unrelated to the Python project.
- It may confuse dependency-management assumptions.

Evidence:

- repository file tree
- `git status --short`

### Docker and Env Templates Are Not Present

No Dockerfile, compose file, `.env`, or env example file was found.

Impact:

- There is no documented containerized setup.
- No checked-in env template exists for contributors.

Evidence:

- repository file tree

### Build Command Is Not Documented or Exercised in CI

The project has a standard `pyproject.toml`, but README and CI do not document or run `python -m build`.

Impact:

- Packaging correctness as an sdist/wheel requires verification.

Evidence:

- `pyproject.toml`
- `README.md`
- `.github/workflows/ci.yml`

### Base Dependencies Are Empty

The base package has no runtime dependencies. This appears intentional because most functionality uses the standard library and optional extras.

Risk:

- Any future non-standard runtime import must be added explicitly to `dependencies` or an appropriate extra.

Evidence:

- `pyproject.toml`
- `src/silive/` imports

### Broad CLI Module

`src/silive/cli.py` is large and contains many command handlers and parser definitions in one file.

Impact:

- This is workable for the current project, but it can become harder to maintain as command count grows.

Evidence:

- `src/silive/cli.py`
- `CODEX_TASKS.md`

## Security Notes

No obvious committed secrets were found by searching for common secret-related terms and private-key patterns.

Search terms included examples such as:

- `password`
- `secret`
- `token`
- `api_key`
- `PRIVATE KEY`
- common AWS/OpenAI-looking token prefixes

This does not prove that no secrets exist; it only means no obvious matches were found in the inspected working files.

Sources:

- repository text search during analysis

## Dependency Risks

`rdkit-pypi>=2022.9.5` may require verification on supported Python versions and platforms. CI does not install this extra, so compatibility is not continuously checked.

Sources:

- `pyproject.toml`
- `.github/workflows/ci.yml`

## Test Status

The full test suite was not run in the analyzed environment because `pytest` was not installed globally. A lightweight import and CLI help check worked with `PYTHONPATH=src`.

Observed smoke result:

- `PYTHONPATH=src python3 -m silive.cli --help` worked.
- `PYTHONPATH=src python3 -m silive.cli evaluate-chain "Si-O-Si-O-Fe-O-Si"` worked.
- RDKit evaluation failed with the expected missing-optional-dependency message.

Sources:

- local command checks during analysis
- `src/silive/cli.py`
- `src/silive/rdkit_chemistry.py`

