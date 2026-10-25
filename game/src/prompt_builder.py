"""
Builds the prompts of stage 1 from prompt_rule_stage1.yaml and the game.
Stage 1 only chooses the function, so it gets the rules about choosing —
not the personality (that is stage 2's).
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List

from llm import LLMFunction

if TYPE_CHECKING:
    from builtin_functions import BuiltinRegistry
    from game_engine import GameEngine
    from prompt_config import DecisionConfig


class PromptBuilder:

    def __init__(self, builtins: BuiltinRegistry, config: DecisionConfig) -> None:
        self.builtins = builtins
        self.config = config

    def system_prompt(self, engine: GameEngine) -> str:
        """
        The role, the goal, the current room and — last, next to the
        conversation — how to decide. The functions are handed over as tools.
        """
        prompt = self.config.role + '\n\n'
        game_target: str = engine.game_data.get('game_target', '')
        if game_target:
            prompt += f'SPIELZIEL:\n{game_target}\n\n'
        prompt += f'AKTUELLER RAUM:\n{engine.state_engine.get_current_state().get_description()}\n\n'
        prompt += self.config.decision_rules.replace('{fallback}', self.builtins.fallback.name)
        return prompt

    def functions(self, engine: GameEngine) -> List[LLMFunction]:
        """
        The game's actions possible right now, then the built-in ones (they
        win a name clash). An action's after_fire hint is about the answer:
        it goes to stage 2.
        """
        return [
            *(LLMFunction(a.name, a.description)
              for a in engine.state_engine.get_available_actions()
              if self.builtins.by_name(a.name) is None),
            *(LLMFunction(b.name, b.description) for b in self.builtins.functions),
        ]

    def retry_input(self, user_input: str, reason: str, functions: List[LLMFunction]) -> str:
        """The player's input once more, after an answer was discarded for reason."""
        hint = (self.config.retry_hint
                .replace('{reason}', reason)
                .replace('{functions}', ', '.join(f.name for f in functions))
                .replace('{fallback}', self.builtins.fallback.name))
        return f'{user_input}\n\n{hint}'
