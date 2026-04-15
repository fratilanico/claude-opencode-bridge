from pathlib import Path

from claude_opencode_bridge.sessions import SessionStore


def test_same_opencode_session_maps_to_same_claude_session(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.json")

    first = store.get_or_create("open-session-1")
    second = store.get_or_create("open-session-1")

    assert first == second


def test_mark_initialized_persists_state(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.json")
    store.get_or_create("open-session-1")
    store.mark_initialized("open-session-1")

    reloaded = SessionStore(tmp_path / "sessions.json")

    assert reloaded.is_initialized("open-session-1") is True
