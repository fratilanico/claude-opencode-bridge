opencode() {
  local bridge_url="http://127.0.0.1:7411"
  local opencode_bin="${OPENCODE_BIN:-$HOME/.opencode/bin/opencode}"

  if ! lsof -iTCP:7411 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    launchctl kickstart -k "gui/$(id -u)/com.claude-opencode-bridge" >/tmp/claude-opencode-bridge.start 2>/tmp/claude-opencode-bridge.err || true
    sleep 2
  fi

  if ! lsof -iTCP:7411 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    echo "[claude-opencode-bridge] localhost:7411 is not listening"
    return 1
  fi

  ANTHROPIC_BASE_URL="${bridge_url}" "${opencode_bin}" "$@"
}
