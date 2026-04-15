# Release Checklist

## Code and docs

- [ ] `pytest tests -q`
- [ ] `python3 -m py_compile claude_opencode_bridge/*.py`
- [ ] `bash -n scripts/*.sh`

## Secret hygiene

- [ ] `bash scripts/check-no-secrets.sh`
- [ ] `git status --short`
- [ ] `git diff --cached`
- [ ] examples contain placeholders or localhost only
- [ ] no personal shell files or local configs were copied into the repo

## Publish readiness

- [ ] README explains the difference from `opencode-claude-auth`
- [ ] install, doctor, and smoke scripts are documented
- [ ] license and contributing guide are present
