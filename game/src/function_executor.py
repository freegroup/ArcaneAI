"""
The step between the two stages: runs the function stage 1 chose.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

from jinja2 import Template

from builtin_functions import BuiltinContext

if TYPE_CHECKING:
    from builtin_functions import BuiltinFunction, BuiltinRegistry
    from game_engine import GameEngine
    from state_engine import Action


@dataclass
class FunctionOutcome:
    # The function whose effect happened: a game action or a built-in one.
    function: str
    # What stage 2 is told: what happened, or how to answer.
    note: str
    # The game action that fired, if any.
    fired_action: Optional[str] = None


class FunctionExecutor:
    """
    A game action fires on the state engine and changes the world; a
    built-in function changes nothing and only tells stage 2 how to answer.
    """

    def __init__(self, builtins: BuiltinRegistry, action_note: Dict[str, Any]) -> None:
        self.builtins = builtins
        # Line templates from prompt_rule_stage2_with_function.yaml (actionNote).
        self.action_note = action_note

    def run(self, engine: GameEngine, name: str) -> FunctionOutcome:
        builtin = self.builtins.by_name(name)
        if builtin is not None:
            return self._builtin(builtin, engine)

        action = engine.state_engine.get_action(name)
        state_before = engine.state_engine.current_state
        success, message = engine.state_engine.execute_action(name)
        if not success:
            # Unavailable actions are never offered, so the game itself failed (a broken script).
            print(f'[EXECUTOR] {message}')
            return self._builtin(self.builtins.on_error, engine, attempted=action)
        moved = engine.state_engine.current_state != state_before
        return FunctionOutcome(function=name, note=self._note(action, engine, moved), fired_action=name)

    def _builtin(self, function: BuiltinFunction, engine: GameEngine, attempted: Optional[Action] = None) -> FunctionOutcome:
        return FunctionOutcome(function=function.name, note=function.run(BuiltinContext(engine, attempted)))

    def _note(self, action: Action, engine: GameEngine, moved: bool) -> str:
        """
        What stage 2 is told about the action that fired: its name, what the
        player does with it, what follows from it (after_fire, rendered
        against the inventory afterwards) and whether the room changed.
        """
        templates = self.action_note
        lines = [
            templates['action'].replace('{name}', action.name),
            templates['description'].replace('{description}', action.description.strip()),
        ]
        result = self._render(action.after_fire, engine).strip()
        if result:
            lines.append(templates['result'].replace('{result}', result))
        if moved:
            lines.append(templates['newRoom'])
        return '\n'.join(lines)

    @staticmethod
    def _render(text: str, engine: GameEngine) -> str:
        try:
            return Template(text).render(engine.inventory.to_dict())
        except Exception as e:
            print(f'[WARNING] Failed to render after_fire: {e}')
            return text
