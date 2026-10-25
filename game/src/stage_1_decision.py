"""
Stage 1: maps the player's input to one of the functions possible right
now — nothing else, no text.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from llm import BaseLLMProvider, LLMFunction, LLMMessage

if TYPE_CHECKING:
    from builtin_functions import BuiltinRegistry
    from game_engine import GameEngine
    from game_history import GameHistory
    from prompt_builder import PromptBuilder


class DecisionStage:
    """
    The model gets the dialogue so far including the functions called
    earlier (without them it imitates plain text answers and narrates
    actions instead of calling them). An answer that calls no function, or
    one that was not offered, is discarded and the model asked again; if
    that fails too, the fallback (keine_aktion) counts.
    """

    def __init__(self, llm: BaseLLMProvider, prompts: PromptBuilder, builtins: BuiltinRegistry) -> None:
        self.llm = llm
        self.prompts = prompts
        self.builtins = builtins

    def decide(self, engine: GameEngine, history: GameHistory, user_input: str) -> str:
        """The function the player's input asks for — a game action or a built-in one."""
        config = self.prompts.config
        functions = self.prompts.functions(engine)
        conversation = [LLMMessage('system', self.prompts.system_prompt(engine))]
        for entry in history.recent(config.history_length, config.history_chars):
            # The welcome and a failed turn count as the fallback: on_system_error is never offered.
            called = entry.chosen_function
            if called is None or called == self.builtins.on_error.name:
                called = self.builtins.fallback.name
            conversation.append(LLMMessage('user', entry.user_input))
            conversation.append(LLMMessage('assistant', entry.llm_response, function_call=called))

        question = user_input
        for attempt in range(1, config.max_attempts + 1):
            try:
                response = self.llm.chat(
                    [*conversation, LLMMessage('user', question)],
                    functions,
                    max_tokens=config.max_output_tokens,
                    label=f'Stufe 1 · Funktionswahl · Versuch {attempt}',
                )
            except Exception as e:
                print(f'[STAGE 1] {e}')
                break
            problem = self._problem(response.function_call, functions)
            if problem is None:
                return response.function_call
            print(f'[STAGE 1] verworfen: {problem}')
            question = self.prompts.retry_input(user_input, problem, functions)
        return self.builtins.fallback.name

    def _problem(self, called: Optional[str], offered: List[LLMFunction]) -> Optional[str]:
        """Why an answer is discarded, or None if it is fine."""
        config = self.prompts.config
        if called is None:
            return config.reason_no_call
        if not any(f.name == called for f in offered):
            return config.reason_unknown_function.replace('{called}', called)
        return None
