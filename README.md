# Claude OpenCode Bridge

Local Anthropic-compatible bridge for OpenCode backed by first-party Claude CLI sessions.

## Why this exists

This repo packages a different architecture from `opencode-claude-auth`.

- `opencode-claude-auth` is a plugin-native auth and request-transform path inside OpenCode.
- `claude-opencode-bridge` is a standalone localhost bridge daemon outside OpenCode.

Use this when the plugin-native Anthropic path is authenticated but still behaves like a third-party lane, and you need full interactive OpenCode sessions backed by local Claude CLI resume.

## What it does

- exposes a local Anthropic-style HTTP endpoint for OpenCode
- maps OpenCode sessions to stable Claude CLI sessions
- uses `claude --print` plus `--resume` for multi-turn continuity
- returns Anthropic-style JSON or SSE back to OpenCode
- ships with macOS install, uninstall, doctor, and smoke scripts

## What it does not do

- it does not provide Claude credentials
- it does not replace OpenCode as the frontend
- it does not manage non-Anthropic providers
- it does not include any private config, secrets, or environment files

## Requirements

- macOS
- Python 3.10+
- Claude CLI installed and authenticated
- OpenCode installed locally

## Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .[dev]

bash scripts/install-macos.sh
bash scripts/doctor.sh
bash scripts/smoke-session.sh saffron
```

## OpenCode config note

OpenCode expects a non-empty Anthropic API key even when talking to a local bridge. This repo uses the literal dummy value `local-bridge-key` for that compatibility requirement. It is not a credential.

See `examples/opencode.json` for the exact provider shape.

## Repo structure

```text
claude_opencode_bridge/   Python package
scripts/                  macOS operational scripts
tests/                    unit and integration-style tests
docs/                     architecture and troubleshooting
examples/                 sanitized example config files
skills/                   reusable skill for this bridge pattern
```

## Verification

```bash
pytest tests -q
python3 -m py_compile claude_opencode_bridge/*.py
bash -n scripts/*.sh
bash scripts/check-no-secrets.sh
```

## Security

- No env files are required for the default install path.
- No secrets belong in this repo.
- All examples are localhost-only or placeholder-only.

See `SECURITY.md` and `docs/release-checklist.md` before publishing changes.
