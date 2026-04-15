# Protocol Notes

## Supported endpoints

- `GET /health`
- `POST /v1/messages`
- `POST /messages`

## Session id extraction

The bridge looks for these headers in order:

1. `x-claude-code-session-id`
2. `x-opencode-session-id`
3. `x-client-request-id`

If none are present, it generates a new session id.

## Prompt shaping

- Initial turns include system text and a compact transcript.
- Follow-up turns use the latest user message as the next Claude turn input.

## Response shaping

- non-stream requests return a single Anthropic-style JSON message
- stream requests return Anthropic-style SSE frames with one text block

## Compatibility limit

This bridge is intentionally minimal. It supports the core interactive text path and fixed-session continuity proof. If you need richer tool-event parity or a broader Anthropic surface, add that explicitly with tests.
