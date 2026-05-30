.PHONY: codex-setup test build run-help

codex-setup:
	./scripts/bootstrap-codex.sh

test:
	uv run --extra dev pytest -q

build:
	uv run --with build python -m build

run-help:
	uv run --extra dev silive --help

