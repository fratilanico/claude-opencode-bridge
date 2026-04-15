# Claude OpenCode Bridge

## Identity
- **Repo:** `claude-opencode-bridge`
- **Purpose:** Route OpenCode Anthropic traffic through a local first-party Claude CLI bridge on macOS.
- **Owner:** Open source
- **Status:** active
- **Live URL:** not deployed

## Tech Stack
- Python 3
- `aiohttp`
- pytest
- macOS launchd
- OpenCode CLI
- Claude CLI

## First Steps (for new agents)
1. Read `README.md`.
2. Read `docs/architecture.md`.
3. Run `bash scripts/check-no-secrets.sh` before any release or publish step.

## Constraints
- Never commit secrets, personal configs, or machine-specific credentials.
- Keep examples placeholder-only or localhost-only.
- Preserve non-Anthropic OpenCode providers.
- Treat this as a macOS-first project unless cross-platform support is explicitly added.

## Testing
- Run: `pytest tests -q`
- Run: `python3 -m py_compile claude_opencode_bridge/*.py`
- Run: `bash -n scripts/*.sh`

## Architecture
- `claude_opencode_bridge/` contains the reusable bridge package.
- `scripts/` contains install, uninstall, doctor, smoke, and release checks.
- `docs/` contains architecture, protocol, troubleshooting, and release guidance.
- `skills/` contains the reusable skill for the bridge pattern.

## Do NOT
- Do not copy local `opencode.json`, `.zshrc`, or credential files into the repo.
- Do not hard-code private IPs, tokens, API keys, or internal service URLs.
- Do not expand scope into generic multi-backend infrastructure without a separate design pass.
