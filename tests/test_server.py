import pytest
from aiohttp.test_utils import TestClient, TestServer

from claude_opencode_bridge.server import ClaudeRunResult, create_app


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

    async def fake_runner(prompt, claude_session_id, resume, model):
        calls.append(
            {
                "prompt": prompt,
                "claude_session_id": claude_session_id,
                "resume": resume,
                "model": model,
            }
        )
        return ClaudeRunResult(text="ok", claude_session_id=claude_session_id)

    app = create_app(
        session_store_path=tmp_path / "sessions.json", claude_runner=fake_runner
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
        assert calls[0]["resume"] is False
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_messages_endpoint_resumes_existing_session(tmp_path):
    calls = []

    async def fake_runner(prompt, claude_session_id, resume, model):
        calls.append(resume)
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
        assert calls == [False, True]
    finally:
        await client.close()
