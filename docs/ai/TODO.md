# Technical TODO

## Quick Wins

- Add a CI job or local checklist step for package build: `uv run --with build python -m build`.
- Add a short note in `docs/rdkit.md` about expected skipped tests when RDKit is missing.
- Keep README examples aligned with `uv` and virtualenv workflows.

## Medium Tasks

- Decide whether optional RDKit compatibility should be continuously tested in CI.
- Add a compact command matrix for common CLI smoke tests.
- Review whether generated report/output schemas should be documented as stable or experimental.

## Larger Refactoring

- Consider splitting `src/silive/cli.py` by command group if command routing becomes hard to maintain.
- Review `src/silive/__init__.py` public exports before treating the package API as stable.
- Reassess symbolic graph and evolutionary-search algorithms on larger candidate sets.

## Questions / Unknowns

- Docker support: TBD, no Dockerfile or compose file exists.
- Package publishing: TBD, no release workflow exists.
- RDKit CI: TBD, currently optional/manual.
- Env template: TBD, no required runtime env variables are documented.
