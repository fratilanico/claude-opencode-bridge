#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

BRIDGE_URL="${CLAUDE_OPENCODE_BRIDGE_URL:-http://127.0.0.1:7411}"
MODEL="${CLAUDE_OPENCODE_BRIDGE_MODEL:-anthropic/claude-sonnet-4-6}"

command -v claude >/dev/null 2>&1 || fail 'claude CLI is not installed'
pass 'claude CLI is available'

command -v curl >/dev/null 2>&1 || fail 'curl is not installed'
pass 'curl is available'

command -v opencode >/dev/null 2>&1 || fail 'opencode is not installed'
pass 'opencode is available'

curl -fsS "${BRIDGE_URL}/health" >/tmp/claude-opencode-bridge-health.json 2>/tmp/claude-opencode-bridge-health.err || fail 'bridge health endpoint did not respond'
pass 'bridge health endpoint responded'

CLAUDE_OUT="$(env -u ANTHROPIC_BASE_URL claude --print -p "Reply exactly: ok" 2>&1 || true)"
[[ "${CLAUDE_OUT}" == *"ok"* ]] || fail 'direct Claude CLI did not return ok'
pass 'direct Claude CLI returned ok'

RUN_OUT="$(opencode run "reply exactly pong" -m "${MODEL}" --format default 2>&1 || true)"
[[ "${RUN_OUT}" == *"pong"* ]] || fail 'OpenCode bridge run did not return pong'
pass 'OpenCode bridge run returned pong'

printf 'OK: Claude OpenCode Bridge verified end-to-end\n'
