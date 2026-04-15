#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${HOME}/.local/share/claude-opencode-bridge"
STATE_DIR="${HOME}/.claude-opencode-bridge"
BACKUP_FILE="${STATE_DIR}/backups/opencode.json.before-bridge"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
PLIST_PATH="${LAUNCH_AGENTS_DIR}/com.claude-opencode-bridge.plist"
OPENCODE_CONFIG_DIR="${HOME}/.config/opencode"
OPENCODE_CONFIG_FILE="${OPENCODE_CONFIG_DIR}/opencode.json"

launchctl unload "${PLIST_PATH}" 2>/dev/null || true
rm -f "${PLIST_PATH}"
rm -rf "${INSTALL_ROOT}"

if [[ -f "${BACKUP_FILE}" ]]; then
  cp "${BACKUP_FILE}" "${OPENCODE_CONFIG_FILE}"
  printf 'Restored OpenCode config backup.\n'
else
  printf 'No OpenCode config backup found; leaving current config in place.\n'
fi

printf 'Removed Claude OpenCode Bridge launchd service and installed package.\n'
