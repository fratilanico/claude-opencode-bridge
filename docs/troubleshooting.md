# Troubleshooting

## Bridge health fails

Check:

```bash
curl -fsS http://127.0.0.1:7411/health
```

If that fails, restart launchd:

```bash
launchctl kickstart -k gui/$(id -u)/com.claude-opencode-bridge
```

## Direct Claude CLI works but OpenCode fails

Run:

```bash
bash scripts/doctor.sh
```

Common causes:

- OpenCode config is not pointing Anthropic at localhost
- OpenCode config uses an empty `apiKey`
- a different wrapper or plugin path is still active

## Session continuity looks wrong

Do not use `--continue` as the proof method. It may resume the most recent session, not the exact one you intended.

Use the explicit `--session <id>` path instead.

## Local config rollback

If you used `scripts/install-macos.sh`, uninstall can restore the backed-up `opencode.json` if the backup file still exists.
