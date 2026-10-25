"""
Stage 2: tells the player what happened — in the game's personality and
the companion's mood.
"""
from __future__ import annotations
import re
from typing import TYPE_CHECKING

from jinja2 import Template

from llm import BaseLLMProvider, LLMMessage

if TYPE_CHECKING:
    from game_engine import GameEngine
    from game_history import GameHistory
    from prompt_config import NarrationConfig


class NarrationStage:
    """
    The engine, not the model, picks how to answer: with_action when a game
    action ran (keep it short), no_action otherwise — keine_aktion, help,
    error and the welcome — with more context and a stronger reference to
    the room. Stage 2 decides nothing, so it can run on a different model
    than stage 1 (strong in language, no function calling needed).
    """

    def __init__(self, llm: BaseLLMProvider, with_action: NarrationConfig, no_action: NarrationConfig) -> None:
        self.llm = llm
        self.with_action = with_action
        self.no_action = no_action

    def welcome_input(self, engine: GameEngine) -> str:
        """What opens the game."""
        return engine.game_data.get('welcome_prompt') or self.no_action.extra['welcomeInput']

    @property
    def fallback_answer(self) -> str:
        """Said when the model gave no usable text."""
        return self.no_action.extra['fallbackAnswer']

    def welcome(self, engine: GameEngine) -> str:
        """The opening narration — like 'no action': the room is introduced."""
        response = self.llm.chat(
            [
                LLMMessage('system', self.system_prompt(engine, self.no_action)),
                LLMMessage('user', self.welcome_input(engine)),
            ],
            max_tokens=self.no_action.max_output_tokens,
            label='Stufe 2 · Erzählen (Begrüßung)',
        )
        return self._tidy(response.content)

    def tell(self, engine: GameEngine, history: GameHistory, user_input: str, note: str, action_executed: bool) -> str:
        """
        What the player is told after user_input; note says what the game
        did or how to answer. engine is in the state after the turn.
        """
        config = self.with_action if action_executed else self.no_action
        messages = [LLMMessage('system', self.system_prompt(engine, config))]
        for entry in history.recent(config.history_length, config.history_chars):
            messages.append(LLMMessage('user', entry.user_input))
            messages.append(LLMMessage('assistant', entry.llm_response))
        messages.append(LLMMessage('user', f'{user_input}\n\n(SPIEL:\n{note})'))
        response = self.llm.chat(messages, max_tokens=config.max_output_tokens, label='Stufe 2 · Erzählen')
        return self._tidy(response.content)

    def system_prompt(self, engine: GameEngine, config: NarrationConfig) -> str:
        """
        Who speaks, the goal, the current room, what the player could do here
        (if the config asks for it) and — last, next to the conversation — how to answer.
        """
        prompt = (self._personality(engine) or config.role) + '\n\n'
        game_target: str = engine.game_data.get('game_target', '')
        if game_target:
            prompt += f'SPIELZIEL:\n{game_target}\n\n'
        prompt += f'AKTUELLER RAUM:\n{engine.state_engine.get_current_state().get_description()}\n\n'
        possible = config.extra.get('possibleActions')
        actions = engine.state_engine.get_available_actions()
        if possible and actions:
            # Only the descriptions: the function names mean nothing to the player.
            lines = '\n'.join(f'- {a.description.strip()}' for a in actions)
            prompt += possible.replace('{actions}', lines) + '\n\n'
        prompt += config.rules
        return prompt

    @staticmethod
    def _personality(engine: GameEngine) -> str:
        """
        The personality is a Jinja2 template, like room descriptions — the
        game designer writes {% if companion_mood == 'X' %} blocks into it.
        """
        identity: str = engine.game_data.get('personality', '')
        try:
            return Template(identity).render(engine.inventory.to_dict()).strip()
        except Exception as e:
            print(f'[WARNING] Failed to render personality template: {e}')
            return identity.strip()

    @staticmethod
    def _tidy(text: str) -> str:
        """Collapse blank lines: the model likes to put one between sentences."""
        return re.sub(r'\n\s*\n+', '\n', text.strip())
