"""
Game History Management
One entry per turn: what the player said, the function that ran and what
the player was told.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    """
    One turn. The welcome is an entry whose input is the opening instruction
    (metadata type 'welcome', no function).
    """
    turn_number: int
    timestamp: float
    user_input: str
    llm_response: str
    # The function that ran: a game action or a built-in one (None for the welcome).
    chosen_function: Optional[str] = None
    function_success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_welcome(self) -> bool:
        return self.metadata.get('type') == 'welcome'

    def __str__(self) -> str:
        return (
            f"Turn {self.turn_number}: '{self.user_input}' → "
            f"'{self.llm_response[:50]}...' "
            f"[{self.chosen_function or 'no function'}]"
        )


class GameHistory:
    """Keeps the latest turns (at most max_length)."""

    def __init__(self, max_length: int = 20) -> None:
        self.entries: List[HistoryEntry] = []
        self.max_length: int = max_length
        self.turn_counter: int = 0

    def add_entry(
        self,
        user_input: str,
        llm_response: str,
        chosen_function: Optional[str] = None,
        function_success: bool = True,
        metadata: Optional[dict] = None
    ) -> HistoryEntry:
        self.turn_counter += 1
        entry = HistoryEntry(
            turn_number=self.turn_counter,
            timestamp=datetime.now().timestamp(),
            user_input=user_input,
            llm_response=llm_response,
            chosen_function=chosen_function,
            function_success=function_success,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_length:
            self.entries = self.entries[-self.max_length:]
        return entry

    def recent(self, count: int, chars: int) -> List[HistoryEntry]:
        """
        The latest entries — at most count entries and chars characters of
        input and narration, since a model's context is limited.
        """
        recent: List[HistoryEntry] = []
        used = 0
        for entry in reversed(self.entries[-count:] if count > 0 else []):
            used += len(entry.user_input) + len(entry.llm_response)
            if used > chars:
                break
            recent.insert(0, entry)
        return recent

    def get_last_entry(self) -> Optional[HistoryEntry]:
        return self.entries[-1] if self.entries else None

    def clear(self) -> None:
        self.entries = []
        self.turn_counter = 0

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"GameHistory({len(self.entries)} entries, turn {self.turn_counter})"
