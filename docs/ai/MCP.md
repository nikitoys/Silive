# MCP Notes

Do not commit real local MCP config files with machine-specific paths or secrets. Use examples only.

## Bootstrap

Use the bootstrap script after clone:

```bash
make codex-setup
```

It runs `scripts/bootstrap-codex.sh`, which:

- finds the project root from any working directory;
- creates `~/.codex`;
- copies `.codex/config.example.toml` to `~/.codex/config.toml`;
- backs up an existing `~/.codex/config.toml`;
- checks `codex`, `node`, `npm`, `npx`, `uv`, `uvx`, and `serena`;
- warms the configured MCP packages where possible.

Some stdio MCP servers wait for a client; a warmup timeout is not automatically a failure.

Verify from the shell if supported:

```bash
codex mcp list
```

Verify inside Codex:

```text
/mcp
```

## context7

- Purpose: fetch current library/framework/API documentation.
- Needed for this project: optional; useful when changing dependencies, Python packaging, pytest, or external libraries.
- Example config: see `.codex/config.example.toml`.
- Check startup: run Codex with the example adapted locally, then ask for library docs through the available MCP tools.
- Known issues: uses `npx`; requires Node/npm network access.
- Do not store: tokens, private registry credentials, local absolute paths.

## browser / Playwright MCP

- Purpose: browser automation and screenshots for UI/web tasks.
- Needed for this project: usually not needed; Silive is currently a CLI/Python project.
- Example config: see `.codex/config.example.toml`.
- Check startup: verify the browser MCP appears in the tool list.
- Known issues: may download browser assets and requires a working Playwright environment.
- Do not store: browser profiles, cookies, credentials, session data.

## sequential-thinking

- Purpose: structured reasoning for complex planning/debugging.
- Needed for this project: optional; useful for multi-step architecture or cleanup tasks.
- Example config: see `.codex/config.example.toml`.
- Check startup: verify the sequential-thinking MCP appears in the tool list.
- Known issues: uses `npx`; requires Node/npm network access.
- Do not store: private prompts containing secrets.

## documents

- Purpose: load and inspect external documents/PDFs/datasets when needed.
- Needed for this project: optional; useful only if future work brings in papers or external specs.
- Example config: see `.codex/config.example.toml`.
- Check startup: verify the documents MCP appears in the tool list.
- Known issues: example uses `uvx`; requires uv and network access.
- Do not store: private documents, credentials, or absolute local file paths.

## serena

- Purpose: semantic code navigation and project memory.
- Needed for this project: optional but useful for symbol-aware code analysis.
- Example config: `.codex/config.example.toml`; project template: `.serena/project.example.yml`.
- Check startup: run Codex with local config and verify Serena tools are available.
- Known issues:
  - Real `.serena/project.yml`, `.serena/project.local.yml`, cache, and memories are local state and ignored.
  - The example project file should be copied/adapted locally if Serena is used.
- Do not store: local cache, memories with private data, absolute machine paths.

## Repository Rules

- Commit `.codex/config.example.toml`, not `.codex/config.toml`.
- Commit `.serena/project.example.yml`, not `.serena/project.yml`.
- Keep real local credentials, cache, histories, and private memories out of git.
- When changing MCP workflow, update `scripts/bootstrap-codex.sh`, this file, and `README.md`.
