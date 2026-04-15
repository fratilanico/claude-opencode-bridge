#!/usr/bin/env bash
set -euo pipefail

MODEL="${CLAUDE_OPENCODE_BRIDGE_MODEL:-anthropic/claude-sonnet-4-6}"
WORD="${1:-saffron}"

extract_session_id() {
  python3 - <<'PYEOF'
import json
import sys

for raw in sys.stdin:
    line = raw.strip()
    if not line.startswith("{"):
        continue
    try:
        payload = json.loads(line)
    except Exception:
        continue
    session_id = payload.get("sessionID")
    if session_id:
        print(session_id)
        break
PYEOF
}

first_output="$(opencode run "Remember the word ${WORD}. Reply only: ok" -m "${MODEL}" --format json --title bridge-smoke 2>&1)"
session_id="$(printf '%s\n' "${first_output}" | extract_session_id)"

if [[ -z "${session_id}" ]]; then
  printf 'FAIL: could not extract session id from first run\n' >&2
  exit 1
fi

second_output="$(opencode run "What word did I ask you to remember? Reply with the word only." -m "${MODEL}" --format json --session "${session_id}" 2>&1)"
third_output="$(opencode run "Repeat the remembered word only." -m "${MODEL}" --format json --session "${session_id}" 2>&1)"

printf '%s\n' "${second_output}" | grep -F '"text":"'"${WORD}"'"' >/dev/null || {
  printf 'FAIL: second turn did not return %s\n' "${WORD}" >&2
  exit 1
}

printf '%s\n' "${third_output}" | grep -F '"text":"'"${WORD}"'"' >/dev/null || {
  printf 'FAIL: third turn did not return %s\n' "${WORD}" >&2
  exit 1
}

printf 'OK: fixed-session continuity verified for %s (%s)\n' "${WORD}" "${session_id}"
