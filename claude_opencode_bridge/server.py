from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiohttp import web

from .protocol import (
    anthropic_message_payload,
    build_prompt_from_request,
    extract_session_id,
    normalize_model,
    sse_frame,
)
from .sessions import SessionStore

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7411
DEFAULT_STATE_DIR = Path.home() / ".claude-opencode-bridge"
DEFAULT_SESSION_STORE = DEFAULT_STATE_DIR / "sessions.json"
HOST_KEY = web.AppKey("host", str)
PORT_KEY = web.AppKey("port", int)
SESSION_STORE_KEY = web.AppKey("session_store", SessionStore)
CLAUDE_RUNNER_KEY = web.AppKey("claude_runner", Callable)
DIRECT_CLAUDE_ENV_UNSET = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_API_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
)


@dataclass
class ClaudeRunResult:
    text: str
    claude_session_id: str


class ClaudeRunnerError(RuntimeError):
    pass


ClaudeRunner = Callable[[str, str, bool, str], Awaitable[ClaudeRunResult]]


def build_claude_env() -> dict[str, str]:
    env = dict(subprocess.os.environ)
    for key in DIRECT_CLAUDE_ENV_UNSET:
        env.pop(key, None)
    return env


def _run_claude_process(
    prompt: str,
    claude_session_id: str,
    resume: bool,
    model: str,
) -> ClaudeRunResult:
    command = ["claude"]
    if resume:
        command.extend(["--resume", claude_session_id])
    else:
        command.extend(["--session-id", claude_session_id])
    command.extend(["--print", "--model", model, "-p", prompt])

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,
        env=build_claude_env(),
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "Claude CLI failed").strip()
        raise ClaudeRunnerError(detail)
    return ClaudeRunResult(
        text=proc.stdout.strip(), claude_session_id=claude_session_id
    )


async def default_claude_runner(
    prompt: str,
    claude_session_id: str,
    resume: bool,
    model: str,
) -> ClaudeRunResult:
    return await asyncio.to_thread(
        _run_claude_process,
        prompt,
        claude_session_id,
        resume,
        model,
    )


async def write_sse_message(
    response: web.StreamResponse, text: str, model: str
) -> None:
    message = anthropic_message_payload(text, model)
    await response.write(
        sse_frame(
            "message_start",
            {"type": "message_start", "message": {**message, "content": []}},
        )
    )
    await response.write(
        sse_frame(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        )
    )
    await response.write(
        sse_frame(
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": text},
            },
        )
    )
    await response.write(
        sse_frame("content_block_stop", {"type": "content_block_stop", "index": 0})
    )
    await response.write(
        sse_frame(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        )
    )
    await response.write(sse_frame("message_stop", {"type": "message_stop"}))
    await response.write(b"data: [DONE]\n\n")


async def health(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "status": "ok",
            "listen_host": request.app[HOST_KEY],
            "listen_port": request.app[PORT_KEY],
            "claude_bin": shutil.which("claude"),
            "session_store": str(request.app[SESSION_STORE_KEY].path),
        }
    )


async def handle_messages(request: web.Request) -> web.StreamResponse | web.Response:
    payload = await request.json()
    store = request.app[SESSION_STORE_KEY]
    claude_runner = request.app[CLAUDE_RUNNER_KEY]

    opencode_session_id = extract_session_id(request.headers)
    claude_session_id = store.get_or_create(opencode_session_id)
    resume = store.is_initialized(opencode_session_id)
    prompt = build_prompt_from_request(payload, initial_turn=not resume)
    model = normalize_model(payload.get("model"))

    try:
        result = await claude_runner(prompt, claude_session_id, resume, model)
    except ClaudeRunnerError as exc:
        return web.json_response(
            {
                "type": "error",
                "error": {"type": "api_error", "message": str(exc)},
            },
            status=502,
        )

    store.mark_initialized(opencode_session_id)

    if payload.get("stream", True):
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream; charset=utf-8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)
        await write_sse_message(response, result.text, model)
        await response.write_eof()
        return response

    return web.json_response(anthropic_message_payload(result.text, model))


def create_app(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    session_store_path: Path | None = None,
    claude_runner: ClaudeRunner = default_claude_runner,
) -> web.Application:
    app = web.Application()
    app[HOST_KEY] = host
    app[PORT_KEY] = port
    app[SESSION_STORE_KEY] = SessionStore(session_store_path or DEFAULT_SESSION_STORE)
    app[CLAUDE_RUNNER_KEY] = claude_runner
    app.router.add_get("/health", health)
    app.router.add_post("/v1/messages", handle_messages)
    app.router.add_post("/messages", handle_messages)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Claude OpenCode Bridge server."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--session-store",
        default=str(DEFAULT_SESSION_STORE),
        help="Path to the persistent session mapping file.",
    )
    args = parser.parse_args()

    app = create_app(
        host=args.host,
        port=args.port,
        session_store_path=Path(args.session_store),
    )
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
