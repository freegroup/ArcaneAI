"""
Session store — persists game sessions per Telegram chat_id to JSON.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional


class SessionStore:
    """
    Persists session state (current_state, inventory, history) per chat_id.
    Each chat_id gets its own JSON file in the sessions directory.
    """

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        if sessions_dir is None:
            sessions_dir = Path(__file__).parent.parent.parent / "sessions" / "telegram"
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, chat_id: int) -> Path:
        return self.sessions_dir / f"{chat_id}.json"

    def save(self, chat_id: int, session_data: Dict[str, Any]) -> None:
        """Persist session state for a chat_id."""
        with open(self._path(chat_id), "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    def load(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Load persisted session state for a chat_id. Returns None if not found."""
        path = self._path(chat_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def delete(self, chat_id: int) -> None:
        """Delete persisted session state for a chat_id (e.g. on /reset)."""
        path = self._path(chat_id)
        if path.exists():
            path.unlink()

    def save_pending(self, chat_id: int, text: str) -> None:
        """Save a pending (unanswered) user input for a chat_id."""
        path = self.sessions_dir / f"{chat_id}_pending.txt"
        path.write_text(text, encoding="utf-8")

    def load_pending(self, chat_id: int) -> Optional[str]:
        """Return the pending user input if one exists, else None."""
        path = self.sessions_dir / f"{chat_id}_pending.txt"
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text if text else None

    def clear_pending(self, chat_id: int) -> None:
        """Clear the pending user input after a successful response."""
        path = self.sessions_dir / f"{chat_id}_pending.txt"
        if path.exists():
            path.unlink()

    def exists(self, chat_id: int) -> bool:
        return self._path(chat_id).exists()
