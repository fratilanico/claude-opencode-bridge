from claude_opencode_bridge.protocol import (
    anthropic_message_payload,
    build_prompt_from_request,
    extract_session_id,
    normalize_model,
    sse_frame,
)


def test_build_prompt_from_request_for_initial_turn() -> None:
    payload = {
        "model": "claude-sonnet-4-6",
        "system": "system guidance",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "hello"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "hi"}]},
            {"role": "user", "content": [{"type": "text", "text": "do the thing"}]},
        ],
    }

    prompt = build_prompt_from_request(payload, initial_turn=True)

    assert "System instructions:" in prompt
    assert "User: hello" in prompt
    assert "Assistant: hi" in prompt
    assert "User: do the thing" in prompt


def test_build_prompt_from_request_for_follow_up_turn() -> None:
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "old"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "reply"}]},
            {"role": "user", "content": [{"type": "text", "text": "latest ask"}]},
        ]
    }

    prompt = build_prompt_from_request(payload, initial_turn=False)

    assert prompt == "latest ask"


def test_extract_session_id_prefers_known_headers() -> None:
    session_id = extract_session_id({"x-claude-code-session-id": "session-123"})
    assert session_id == "session-123"


def test_normalize_model_strips_provider_prefix() -> None:
    assert normalize_model("anthropic/claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_anthropic_payload_contains_text_content() -> None:
    payload = anthropic_message_payload("ok", "claude-sonnet-4-6")
    assert payload["content"][0]["text"] == "ok"


def test_sse_frame_contains_event_and_json() -> None:
    frame = sse_frame("message_start", {"type": "message_start"}).decode()
    assert "event: message_start" in frame
    assert '"type":"message_start"' in frame
