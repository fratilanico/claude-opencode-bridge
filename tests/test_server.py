import json
import sys

import pytest
from aiohttp.test_utils import TestClient, TestServer

from claude_opencode_bridge.server import (
    ClaudeRunResult,
    create_app,
    translate_tool_input,
)


async def make_client(app):
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    return client


def test_create_app_returns_aiohttp_application(tmp_path):
    app = create_app(session_store_path=tmp_path / "sessions.json")
    assert app is not None


@pytest.mark.asyncio
async def test_health_returns_bridge_status(tmp_path):
    app = create_app(session_store_path=tmp_path / "sessions.json")
    client = await make_client(app)

    try:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert "claude_bin" in data
        assert "session_store" in data
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_messages_endpoint_streams_anthropic_events(tmp_path):
    calls = []

    async def fake_stream_runner(prompt, claude_session_id, resume, model):
        calls.append(
            {
                "prompt": prompt,
                "claude_session_id": claude_session_id,
                "resume": resume,
                "model": model,
            }
        )
        yield {
            "type": "stream_event",
            "event": {
                "type": "message_start",
                "message": {
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "model": model,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            },
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "ok"},
            },
        }
        yield {
            "type": "stream_event",
            "event": {"type": "content_block_stop", "index": 0},
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }
        yield {"type": "stream_event", "event": {"type": "message_stop"}}
        yield {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "ok",
        }

    app = create_app(
        session_store_path=tmp_path / "sessions.json",
        claude_stream_runner=fake_stream_runner,
    )
    client = await make_client(app)

    try:
        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "stream": True,
                "system": "sys",
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "hello"}]}
                ],
            },
            headers={"x-claude-code-session-id": "open-session-1"},
        )
        body = await resp.text()

        assert resp.status == 200
        assert resp.headers["Content-Type"].startswith("text/event-stream")
        assert "event: message_start" in body
        assert "event: content_block_delta" in body
        assert '"text":"ok"' in body
        assert "data: [DONE]" in body
        assert calls[0]["resume"] is False
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_messages_endpoint_resumes_existing_session(tmp_path):
    calls = []

    async def fake_runner(prompt, claude_session_id, resume, model):
        calls.append((claude_session_id, resume, prompt))
        return ClaudeRunResult(text="ok", claude_session_id=claude_session_id)

    app = create_app(
        session_store_path=tmp_path / "sessions.json", claude_runner=fake_runner
    )
    client = await make_client(app)
    payload = {
        "model": "claude-sonnet-4-6",
        "stream": False,
        "messages": [{"role": "user", "content": [{"type": "text", "text": "hello"}]}],
    }

    try:
        first = await client.post(
            "/v1/messages",
            json=payload,
            headers={"x-claude-code-session-id": "open-session-1"},
        )
        assert first.status == 200

        second = await client.post(
            "/v1/messages",
            json={
                **payload,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "hello"}]},
                    {"role": "assistant", "content": [{"type": "text", "text": "ok"}]},
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "follow up"}],
                    },
                ],
            },
            headers={"x-claude-code-session-id": "open-session-1"},
        )
        assert second.status == 200
        assert calls[0][0] is None and calls[0][1] is False
        assert calls[1][0] is None and calls[1][1] is False
        assert "Conversation so far:" in calls[1][2]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_tool_result_turn_uses_stateless_continuation_prompt(tmp_path):
    calls = []

    async def fake_runner(prompt, claude_session_id, resume, model):
        calls.append((claude_session_id, resume, prompt))
        return ClaudeRunResult(text="ok", claude_session_id=claude_session_id or "")

    app = create_app(
        session_store_path=tmp_path / "sessions.json", claude_runner=fake_runner
    )
    client = await make_client(app)

    try:
        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Read AGENTS.md and tell me the first line only.",
                            }
                        ],
                    },
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Reading now."}],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "content": "# AGENTS.md -- POINTER FILE",
                            }
                        ],
                    },
                ],
            },
            headers={"x-claude-code-session-id": "open-session-tool-result"},
        )
        assert resp.status == 200
        assert calls[0][0] is None and calls[0][1] is False
        assert "The original user request was:" in calls[0][2]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_messages_endpoint_returns_504_on_claude_timeout(tmp_path):
    async def fake_runner(prompt, claude_session_id, resume, model):
        from claude_opencode_bridge.server import (
            CLAUDE_RUN_TIMEOUT_SECONDS,
            ClaudeRunnerTimeout,
        )

        raise ClaudeRunnerTimeout(
            f"Claude CLI timed out after {CLAUDE_RUN_TIMEOUT_SECONDS}s for model {model}"
        )

    app = create_app(
        session_store_path=tmp_path / "sessions.json", claude_runner=fake_runner
    )
    client = await make_client(app)

    try:
        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "stream": False,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "hello"}]}
                ],
            },
            headers={"x-claude-code-session-id": "open-session-timeout"},
        )
        data = await resp.json()

        assert resp.status == 504
        assert data["error"]["type"] == "timeout_error"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_stream_messages_endpoint_emits_error_event_on_timeout(tmp_path):
    async def fake_stream_runner(prompt, claude_session_id, resume, model):
        from claude_opencode_bridge.server import (
            CLAUDE_RUN_TIMEOUT_SECONDS,
            ClaudeRunnerTimeout,
        )

        if False:
            yield {}
        raise ClaudeRunnerTimeout(
            f"Claude CLI timed out after {CLAUDE_RUN_TIMEOUT_SECONDS}s for model {model}"
        )

    app = create_app(
        session_store_path=tmp_path / "sessions.json",
        claude_stream_runner=fake_stream_runner,
    )
    client = await make_client(app)

    try:
        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "stream": True,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "hello"}]}
                ],
            },
            headers={"x-claude-code-session-id": "open-session-stream-timeout"},
        )
        body = await resp.text()

        assert resp.status == 200
        assert "event: error" in body
        assert '"type":"timeout_error"' in body
    finally:
        await client.close()


def test_translate_tool_input_maps_read_file_path() -> None:
    translated = translate_tool_input(
        "Read", {"file_path": "/tmp/test.md", "limit": 1, "offset": 2}
    )

    assert translated == {"filePath": "/tmp/test.md", "limit": 1, "offset": 2}


def test_translate_tool_input_adds_bash_defaults() -> None:
    translated = translate_tool_input("Bash", {"command": "pwd"})

    assert translated["command"] == "pwd"
    assert translated["description"].startswith("Runs command:")
    assert translated["timeout"] == 120000


@pytest.mark.asyncio
async def test_stream_messages_translate_tool_use_input_keys(tmp_path):
    async def fake_stream_runner(prompt, claude_session_id, resume, model):
        yield {
            "type": "stream_event",
            "event": {
                "type": "message_start",
                "message": {
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "model": model,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            },
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Reading now.\n\n"},
            },
        }
        yield {
            "type": "stream_event",
            "event": {"type": "content_block_stop", "index": 0},
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "index": 0,
                "delta": {
                    "type": "text_delta",
                    "text": '<function_calls>\n<invoke name="Read">\n<parameter name="file_path">/tmp/test.md</parameter>\n<parameter name="limit">1</parameter>\n</invoke>\n</function_calls>\n\nThe first line is fake',
                },
            },
        }
        yield {
            "type": "stream_event",
            "event": {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }
        yield {"type": "stream_event", "event": {"type": "message_stop"}}
        yield {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "ok",
        }

    app = create_app(
        session_store_path=tmp_path / "sessions.json",
        claude_stream_runner=fake_stream_runner,
    )
    client = await make_client(app)

    try:
        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "stream": True,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "hello"}]}
                ],
            },
            headers={"x-claude-code-session-id": "open-session-tool-translate"},
        )
        body = await resp.text()

        assert resp.status == 200
        assert '"text":"Reading now."' in body
        assert '\\"filePath\\":\\"/tmp/test.md\\"' in body
        assert "file_path" not in body
        assert "function_calls" not in body
        assert "The first line is fake" not in body
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_default_claude_stream_runner_handles_large_json_lines(monkeypatch):
    from claude_opencode_bridge import server as bridge

    payload = {
        "type": "stream_event",
        "event": {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": "A" * 70000},
        },
    }
    script = f'import json; print(json.dumps({payload!r}, separators=(",",":")))'

    monkeypatch.setattr(
        bridge,
        "build_claude_stream_command",
        lambda prompt, claude_session_id, resume, model: [sys.executable, "-c", script],
    )
    monkeypatch.setattr(bridge, "build_claude_env", lambda: {})

    items = []
    async for item in bridge.default_claude_stream_runner(
        "prompt", "session", False, "claude-sonnet-4-6"
    ):
        items.append(item)

    assert items[0]["type"] == "stream_event"
    assert items[0]["event"]["delta"]["text"] == "A" * 70000
