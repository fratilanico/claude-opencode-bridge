# Architecture

## Summary

`claude-opencode-bridge` sits between OpenCode and Claude CLI.

- OpenCode stays the frontend.
- Claude CLI stays the model backend.
- The bridge translates between Anthropic-style HTTP and local Claude CLI session execution.

## Request path

1. OpenCode sends `POST /v1/messages` to localhost.
2. The bridge extracts a stable OpenCode session id from request headers.
3. The bridge maps that session id to a Claude session id stored on disk.
4. The bridge builds a prompt for either an initial turn or a resumed turn.
5. The bridge runs `claude --print` with either `--session-id` or `--resume`.
6. The bridge returns Anthropic-style JSON or SSE back to OpenCode.

## Why this is different from plugin-native auth

This repo does not patch OpenCode from inside the client.

Instead, it exposes a local compatibility boundary outside OpenCode. That makes it useful when authentication succeeds but the upstream Anthropic lane still behaves like a third-party app path.

## Session continuity

The session store is a JSON file on disk. The same OpenCode session id always maps to the same Claude session id unless that file is removed.

## Failure modes

- `claude` missing: health can still respond, but doctor will fail.
- `claude` unauthenticated: requests fail with a bridge API error.
- bridge not running: OpenCode cannot reach localhost and doctor fails early.
- wrong session test method: `--continue` may select a different recent session; use explicit `--session` to prove continuity.
