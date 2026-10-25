"""
The built-in functions of every game.
"""
from __future__ import annotations
from typing import List, Optional

from prompt_config import load_prompt_file
from .builtin_function import BuiltinFunction
from .action_keine_aktion import ActionKeineAktion
from .action_helfe_dem_spieler import ActionHelfeDemSpieler
from .action_on_system_error import ActionOnSystemError


class BuiltinRegistry:
    def __init__(self, provider: str = '') -> None:
        texts = load_prompt_file('prompt_builtin_functions', provider)
        # What counts when stage 1 gives no usable answer.
        self.fallback: BuiltinFunction = ActionKeineAktion(texts['keine_aktion'])
        # What the engine chooses when something in the game fails. Never offered to stage 1.
        self.on_error: BuiltinFunction = ActionOnSystemError(texts['on_system_error'])
        # Offered to stage 1 next to the game's actions, in this order.
        self.functions: List[BuiltinFunction] = [
            self.fallback,
            ActionHelfeDemSpieler(texts['helfe_dem_spieler']),
        ]

    def by_name(self, name: str) -> Optional[BuiltinFunction]:
        """The offered built-in function called name, or None."""
        return next((f for f in self.functions if f.name == name), None)
