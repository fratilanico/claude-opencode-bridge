# Contributing

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .[dev]
pytest tests -q
```

## Rules

- keep examples placeholder-only or localhost-only
- do not commit secrets, tokens, or personal machine state
- preserve the macOS-first install path unless a new design expands scope
- keep changes small and testable

## Before opening a pull request

```bash
pytest tests -q
python3 -m py_compile claude_opencode_bridge/*.py
bash -n scripts/*.sh
bash scripts/check-no-secrets.sh
```
