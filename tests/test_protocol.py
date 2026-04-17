from claude_opencode_bridge.protocol import (
    anthropic_message_payload,
    build_tool_result_continuation,
    build_prompt_from_request,
    extract_function_calls,
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


def test_build_tool_result_continuation_for_success() -> None:
    prompt = build_tool_result_continuation(
        [
            {
                "type": "tool_result",
                "content": "Wrote file successfully.",
                "is_error": False,
            }
        ]
    )

    assert prompt is not None
    assert "Tool result status: success" in prompt
    assert "Do not claim the tool was blocked" in prompt


def test_build_prompt_from_request_prefers_tool_result_continuation() -> None:
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "content": "Wrote file successfully.",
                        "is_error": False,
                    }
                ],
            }
        ]
    }

    prompt = build_prompt_from_request(payload, initial_turn=False)

    assert "Tool result status: success" in prompt


def test_build_prompt_from_request_keeps_original_request_in_tool_result_turn() -> None:
    payload = {
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
                        "is_error": False,
                    }
                ],
            },
        ]
    }

    prompt = build_prompt_from_request(payload, initial_turn=False)

    assert "The original user request was:" in prompt
    assert "Read AGENTS.md and tell me the first line only." in prompt


def test_build_prompt_from_request_for_simple_initial_turn() -> None:
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Reply exactly: ok"}]}
        ]
    }

    prompt = build_prompt_from_request(payload, initial_turn=True)

    assert prompt == "Reply exactly: ok"


def test_extract_function_calls_returns_plain_text_when_no_xml() -> None:
    text, tool_calls = extract_function_calls("hello")

    assert text == "hello"
    assert tool_calls == []


def test_extract_function_calls_parses_tool_intent_and_strips_trailing_text() -> None:
    text, tool_calls = extract_function_calls(
        "Reading now.\n\n"
        "<function_calls>\n"
        '<invoke name="Read">\n'
        '<parameter name="file_path">/tmp/test.md</parameter>\n'
        '<parameter name="limit">1</parameter>\n'
        "</invoke>\n"
        "</function_calls>\n\n"
        "The first line is fake"
    )

    assert text == "Reading now."
    assert tool_calls == [
        {"name": "Read", "input": {"file_path": "/tmp/test.md", "limit": 1}}
    ]


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
