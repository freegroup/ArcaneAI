"""
Base class of the built-in functions every game offers next to its own
actions (those of its model.json).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from game_engine import GameEngine
    from state_engine import Action


@dataclass
class BuiltinContext:
    """The game a built-in function runs in."""
    engine: GameEngine
    # The game action the player attempted, when this function stands in for it (it failed).
    attempted: Optional[Action] = None


class BuiltinFunction(ABC):
    """
    Stage 1 can choose it like a game action. It never changes the game —
    that is what game actions are for. When chosen, run() tells stage 2 how
    to answer the player. Texts come from prompt_builtin_functions.yaml.

    A new built-in function is a subclass in action_<name>.py, a section in
    prompt_builtin_functions.yaml and an entry in BuiltinRegistry.
    """

    name: str = ''

    def __init__(self, texts: Dict[str, Any]) -> None:
        self.texts = texts

    @property
    def description(self) -> str:
        """What it is for — stage 1 matches the player's input against it."""
        return self.texts['description']

    @abstractmethod
    def run(self, context: BuiltinContext) -> str:
        """What stage 2 is told when this function was chosen."""
