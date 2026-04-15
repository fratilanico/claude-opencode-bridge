from __future__ import annotations

import json
import uuid
from typing import Any, Mapping


def flatten_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text = str(block.get("text") or "").strip()
            if text:
                text_parts.append(text)
        elif block_type == "tool_result":
            text = flatten_content(block.get("content"))
            if text:
                text_parts.append(f"Tool result:\n{text}")
    return "\n\n".join(text_parts).strip()


def flatten_system(system: Any) -> str:
    if isinstance(system, str):
        return system.strip()
    if isinstance(system, list):
        return flatten_content(system)
    return ""


def build_prompt_from_request(payload: dict[str, Any], initial_turn: bool) -> str:
    messages = payload.get("messages") or []
    if not isinstance(messages, list):
        messages = []

    if not initial_turn:
        for message in reversed(messages):
            if message.get("role") == "user":
                text = flatten_content(message.get("content"))
                if text:
                    return text
        return "Continue."

    parts: list[str] = []
    system_text = flatten_system(payload.get("system"))
    if system_text and len(system_text) <= 2000:
        parts.append("System instructions:\n" + system_text)

    transcript: list[str] = []
    for message in messages:
        role = str(message.get("role") or "user").capitalize()
        text = flatten_content(message.get("content"))
        if text:
            transcript.append(f"{role}: {text}")

    if transcript:
        parts.append("Conversation so far:\n" + "\n\n".join(transcript))

    prompt = "\n\n".join(parts).strip()
    return prompt or "Continue."


def extract_session_id(headers: Mapping[str, str]) -> str:
    for key in (
        "x-claude-code-session-id",
        "x-opencode-session-id",
        "x-client-request-id",
    ):
        value = headers.get(key)
        if value:
            return value
    return str(uuid.uuid4())


def normalize_model(model: str | None) -> str:
    if not model:
        return "claude-sonnet-4-6"
    return model.split("/", 1)[1] if "/" in model else model


def anthropic_message_payload(text: str, model: str) -> dict[str, Any]:
    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def sse_frame(event: str, data: dict[str, Any]) -> bytes:
    body = json.dumps(data, separators=(",", ":"))
    return f"event: {event}\ndata: {body}\n\n".encode()
