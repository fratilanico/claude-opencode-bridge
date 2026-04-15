#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${HOME}/.local/share/claude-opencode-bridge"
VENV_DIR="${INSTALL_ROOT}/venv"
STATE_DIR="${HOME}/.claude-opencode-bridge"
BACKUP_DIR="${STATE_DIR}/backups"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
PLIST_PATH="${LAUNCH_AGENTS_DIR}/com.claude-opencode-bridge.plist"
OPENCODE_CONFIG_DIR="${HOME}/.config/opencode"
OPENCODE_CONFIG_FILE="${OPENCODE_CONFIG_DIR}/opencode.json"
BRIDGE_URL="http://127.0.0.1:7411"

mkdir -p "${INSTALL_ROOT}" "${STATE_DIR}" "${BACKUP_DIR}" "${LAUNCH_AGENTS_DIR}" "${OPENCODE_CONFIG_DIR}"

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip >/dev/null
"${VENV_DIR}/bin/pip" install "${REPO_ROOT}" >/dev/null

if [[ -f "${OPENCODE_CONFIG_FILE}" && ! -f "${BACKUP_DIR}/opencode.json.before-bridge" ]]; then
  cp "${OPENCODE_CONFIG_FILE}" "${BACKUP_DIR}/opencode.json.before-bridge"
fi

if [[ ! -f "${OPENCODE_CONFIG_FILE}" ]]; then
  printf '{}\n' > "${OPENCODE_CONFIG_FILE}"
fi

OPENCODE_CONFIG_FILE="${OPENCODE_CONFIG_FILE}" BRIDGE_URL="${BRIDGE_URL}" python3 - <<'PYEOF'
import json
import os
from pathlib import Path

config_path = Path(os.environ["OPENCODE_CONFIG_FILE"])
bridge_url = os.environ["BRIDGE_URL"]
data = json.loads(config_path.read_text())

provider = data.setdefault("provider", {})
anthropic = provider.setdefault("anthropic", {})
options = anthropic.setdefault("options", {})
options["baseURL"] = bridge_url
options["apiKey"] = "local-bridge-key"

config_path.write_text(json.dumps(data, indent=2) + "\n")
PYEOF

cat > "${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.claude-opencode-bridge</string>
  <key>ProgramArguments</key>
  <array>
    <string>${VENV_DIR}/bin/claude-opencode-bridge</string>
    <string>--host</string>
    <string>127.0.0.1</string>
    <string>--port</string>
    <string>7411</string>
    <string>--session-store</string>
    <string>${STATE_DIR}/sessions.json</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME}</string>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/bridge.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/bridge.err</string>
</dict>
</plist>
EOF

launchctl unload "${PLIST_PATH}" 2>/dev/null || true
launchctl load "${PLIST_PATH}"

printf 'Installed Claude OpenCode Bridge at %s\n' "${BRIDGE_URL}"
printf 'Next step: bash scripts/doctor.sh\n'
