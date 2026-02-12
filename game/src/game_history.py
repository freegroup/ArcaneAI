"""
Game History Management
Structured history that tracks prompts, functions, and responses.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from datetime import datetime
from llm import LLMMessage, LLMFunction


@dataclass
class HistoryEntry:
    """
    Represents a single turn in the game history.

    Stores complete context including what functions were available,
    enabling replay, debugging, and analysis.
    """
    turn_number: int
    timestamp: float
    user_input: str
    base_prompt: str  # System prompt WITHOUT function instructions
    available_functions: List[LLMFunction]
    llm_response: str
    chosen_function: Optional[str] = None
    function_success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)  # For future extensions

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"Turn {self.turn_number}: '{self.user_input}' → "
            f"'{self.llm_response[:50]}...' "
            f"[{self.chosen_function or 'no function'}]"
        )


class GameHistory:
    """
    Manages structured game history.

    Provides conversion to LLM message format while maintaining
    complete historical context for debugging and analysis.
    """

    def __init__(self, max_length: int = 20) -> None:
        """
        Initialize game history.

        Args:
            max_length: Maximum number of entries to keep
        """
        self.entries: List[HistoryEntry] = []
        self.max_length: int = max_length
        self.turn_counter: int = 0

    def add_entry(
        self,
        user_input: str,
        base_prompt: str,
        available_functions: List[LLMFunction],
        llm_response: str,
        chosen_function: Optional[str] = None,
        function_success: bool = True,
        metadata: Optional[dict] = None
    ) -> HistoryEntry:
        """
        Add a new entry to the history.

        Args:
            user_input: User's input
            base_prompt: Base system prompt (without functions)
            available_functions: Functions available at this turn
            llm_response: LLM's response
            chosen_function: Function chosen by LLM (if any)
            function_success: Whether function execution succeeded
            metadata: Additional metadata

        Returns:
            The created HistoryEntry
        """
        self.turn_counter += 1

        entry: HistoryEntry = HistoryEntry(
            turn_number=self.turn_counter,
            timestamp=datetime.now().timestamp(),
            user_input=user_input,
            base_prompt=base_prompt,
            available_functions=available_functions.copy(),  # Deep copy
            llm_response=llm_response,
            chosen_function=chosen_function,
            function_success=function_success,
            metadata=metadata or {}
        )

        self.entries.append(entry)
        self._trim_if_needed()

        return entry

    def to_llm_messages(self, current_base_prompt: str) -> List[LLMMessage]:
        """
        Convert history to LLM message format.

        IMPORTANT: Functions are NOT included in messages!
        Only the base prompt and conversation turns.

        Args:
            current_base_prompt: Current base prompt (without functions)

        Returns:
            List of LLMMessage objects for API call
        """
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=current_base_prompt)
        ]

        for entry in self.entries:
            messages.append(LLMMessage(role="user", content=entry.user_input))
            messages.append(LLMMessage(role="assistant", content=entry.llm_response))

        return messages

    def get_last_entry(self) -> Optional[HistoryEntry]:
        """Get the most recent history entry."""
        return self.entries[-1] if self.entries else None

    def get_entries_since(self, turn_number: int) -> List[HistoryEntry]:
        """Get all entries since a specific turn number."""
        return [e for e in self.entries if e.turn_number >= turn_number]

    def _trim_if_needed(self) -> None:
        """Trim history to max_length if needed."""
        if len(self.entries) > self.max_length:
            self.entries = self.entries[-self.max_length:]

    def clear(self) -> None:
        """Clear all history."""
        self.entries = []
        self.turn_counter = 0

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)

    def __repr__(self) -> str:
        """String representation."""
        return f"GameHistory({len(self.entries)} entries, turn {self.turn_counter})"
