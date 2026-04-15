from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


class SessionStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text())
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2) + "\n")

    def get_or_create(self, opencode_session_id: str) -> str:
        entry = self._data.get(opencode_session_id)
        if entry and entry.get("claude_session_id"):
            return str(entry["claude_session_id"])

        claude_session_id = str(uuid.uuid4())
        self._data[opencode_session_id] = {
            "claude_session_id": claude_session_id,
            "initialized": False,
            "updated_at": int(time.time()),
        }
        self._save()
        return claude_session_id

    def is_initialized(self, opencode_session_id: str) -> bool:
        entry = self._data.get(opencode_session_id)
        return bool(entry and entry.get("initialized"))

    def mark_initialized(self, opencode_session_id: str) -> None:
        claude_session_id = self.get_or_create(opencode_session_id)
        self._data[opencode_session_id] = {
            "claude_session_id": claude_session_id,
            "initialized": True,
            "updated_at": int(time.time()),
        }
        self._save()
