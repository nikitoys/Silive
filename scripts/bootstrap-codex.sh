#!/usr/bin/env bash
set -u

log() {
  printf '[codex-setup] %s\n' "$*"
}

warn() {
  printf '[codex-setup] warning: %s\n' "$*" >&2
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

run_probe() {
  local label="$1"
  shift

  log "warming ${label}"
  if command_exists timeout; then
    timeout 8s "$@" >/dev/null 2>&1
    local status=$?
    case "$status" in
      0)
        log "${label}: ok"
        ;;
      124)
        log "${label}: timed out after startup; this is acceptable for stdio MCP servers"
        ;;
      *)
        warn "${label}: command exited with status ${status}"
        ;;
    esac
  else
    warn "timeout command not found; skipping ${label} warmup to avoid hanging"
  fi
}

find_project_root() {
  local script_dir
  script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

  if [ -f "${script_dir}/../.codex/config.example.toml" ]; then
    cd -- "${script_dir}/.." && pwd
    return 0
  fi

  if command_exists git; then
    git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null && return 0
  fi

  return 1
}

main() {
  local project_root
  if ! project_root="$(find_project_root)"; then
    printf 'Could not determine project root.\n' >&2
    exit 1
  fi

  local example_config="${project_root}/.codex/config.example.toml"
  local target_dir="${HOME}/.codex"
  local target_config="${target_dir}/config.toml"

  if [ ! -f "$example_config" ]; then
    printf 'Missing example config: %s\n' "$example_config" >&2
    exit 1
  fi

  log "project root: ${project_root}"
  mkdir -p "$target_dir"

  if [ -f "$target_config" ]; then
    local stamp backup
    stamp="$(date +%Y%m%d-%H%M%S)"
    backup="${target_config}.bak.${stamp}"
    cp "$target_config" "$backup"
    log "backed up existing ${target_config} to ${backup}"
  fi

  cp "$example_config" "$target_config"
  log "installed Codex MCP config: ${target_config}"

  log "checking tools"
  local missing=0
  for tool in codex node npm npx uv uvx serena; do
    if command_exists "$tool"; then
      log "${tool}: $(command -v "$tool")"
    else
      warn "${tool}: not found"
      missing=1
    fi
  done

  if command_exists npx; then
    run_probe "context7" npx -y @upstash/context7-mcp --help
    run_probe "sequential-thinking" npx -y @modelcontextprotocol/server-sequential-thinking --help
    run_probe "playwright/browser" npx -y @playwright/mcp@latest --help
  else
    warn "npx not found; skipping Node-based MCP package warmup"
  fi

  if command_exists uvx; then
    run_probe "documents" uvx awslabs.document-loader-mcp-server@latest --help
  else
    warn "uvx not found; skipping documents MCP warmup"
  fi

  cat <<'EOF'

Next steps:
  1. Start Codex from this repository:
       codex
  2. Inside Codex, inspect MCP status:
       /mcp
  3. From the shell, if your Codex CLI supports it, try:
       codex mcp list
  4. Read project handoff docs:
       AGENTS.md
       PROJECT_GOAL.md
       CODEX_TASKS.md
       docs/ai/RUNBOOK.md
       docs/ai/MCP.md

Notes:
  - ~/.codex/config.toml is local machine config and should not be committed.
  - Project examples live in .codex/config.example.toml and .serena/project.example.yml.
  - Some stdio MCP servers wait for a client; warmup timeout is not automatically a failure.
EOF

  if [ "$missing" -ne 0 ]; then
    warn "one or more tools are missing; install them before relying on MCP"
  fi
}

main "$@"

