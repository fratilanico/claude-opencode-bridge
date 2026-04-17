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
- stream requests forward real Claude `stream_event` message frames as Anthropic SSE

## Tool-use compatibility

For streamed tool-use blocks, the bridge supports two compatibility layers:

1. direct Claude tool-use schema normalization when native tool-use blocks appear
2. transport-only parsing of Claude XML-like `<function_calls>` intent when built-in tools are disabled

This avoids runtime failures caused by mismatched field names such as `file_path` versus `filePath`.

## Transport-only tool intent

In transport-only mode, Claude emits tool intent inside assistant text as:

```xml
<function_calls>
  <invoke name="Read">
    <parameter name="file_path">/path/file.md</parameter>
  </invoke>
</function_calls>
```

The bridge parses that markup, strips it from user-visible text, translates parameter names, and emits OpenCode-native tool-use events instead.

## Compatibility limit

This bridge is intentionally minimal. It supports the core interactive text path and fixed-session continuity proof. If you need richer tool-event parity or a broader Anthropic surface, add that explicitly with tests.
