from __future__ import annotations
import threading
from typing import TYPE_CHECKING, Optional

from llm import LLMFactory, LLMMessage, BaseLLMProvider
from game_history import GameHistory
from voice import VoiceFactory, BaseTTSProvider
from prompt_builder import PromptBuilder
from companion_director import CompanionDirector

if TYPE_CHECKING:
    from session import GameSession


class GameController:
    """
    Thin orchestrator: wires LLM, state engine, history, voice, and companion logic.
    """

    def __init__(self, session: GameSession) -> None:
        self.session = session

        llm_factory = LLMFactory()
        self.llm: BaseLLMProvider = llm_factory.create_provider()
        self.llm._session = session

        max_length: int = llm_factory.config.get('llm', {}).get('max_history_length', 20)
        self.history: GameHistory = GameHistory(max_length=max_length)

        self.voice: BaseTTSProvider = VoiceFactory().create_provider(session.audio_sink)
        self.prompt_builder = PromptBuilder()
        self._companion: Optional[CompanionDirector] = None

    @property
    def companion(self) -> CompanionDirector:
        if self._companion is None:
            engine = self.session.game_engine
            self._companion = CompanionDirector(self.llm, engine.inventory, engine.game_data)
        return self._companion

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_game(self) -> str:
        self.history.clear()

        prompt, functions = self._build_prompt_and_functions()
        game_data = self.session.game_engine.game_data
        welcome_prompt = game_data.get('welcome_prompt', 'Das Spiel beginnt!')

        messages = [
            LLMMessage(role='system', content=prompt),
            LLMMessage(role='user', content=welcome_prompt),
        ]

        try:
            response = self.llm.chat_with_functions(messages, functions, prompt)
            welcome_text = response.content
        except Exception:
            return self.session.game_engine.state_engine.get_current_state().get_description()

        self.history.add_entry(
            user_input=welcome_prompt,
            base_prompt=prompt,
            available_functions=functions,
            llm_response=welcome_text,
            chosen_function='keine_aktion',
            metadata={'type': 'welcome'},
        )

        self._send_initial_ambient()
        self.voice.speak(self.session, welcome_text)
        return welcome_text

    def process_input(self, user_input: str) -> dict:
        prompt, functions = self._build_prompt_and_functions()
        messages = self.history.to_llm_messages(prompt)
        messages.append(LLMMessage(role='user', content=user_input))

        try:
            response = self.llm.chat_with_functions(messages, functions, prompt)
        except Exception as e:
            return {'response': f'Fehler beim LLM-Aufruf: {e}', 'executed_action': None}

        narrative: str = response.content
        function_call = response.function_call
        chosen_name: Optional[str] = function_call.name if function_call else None

        if not narrative and not chosen_name:
            narrative = 'Hm? Ich versteh nicht was du meinst. Versuch\'s nochmal.'

        success = True
        if chosen_name and chosen_name != 'keine_aktion':
            success, message = self.session.game_engine.state_engine.execute_action(chosen_name)
            if not success:
                narrative = f'{narrative}\n\n(Action konnte nicht ausgeführt werden: {message})'

        self.history.add_entry(
            user_input=user_input,
            base_prompt=prompt,
            available_functions=functions,
            llm_response=narrative,
            chosen_function=chosen_name,
            function_success=success,
        )

        self.companion.update_async(self.history)

        self.voice.stop(self.session)
        threading.Thread(
            target=self.voice.speak, args=(self.session, narrative), daemon=True
        ).start()

        current_state = self.session.game_engine.state_engine.get_current_state()
        game_over = current_state.is_end

        return {
            'response': narrative,
            'executed_action': chosen_name if chosen_name != 'keine_aktion' else None,
            'game_over': game_over,
        }

    # kept for external callers (e.g. runners that check goal drift)
    def get_game_target_reminder(self) -> str:
        return self.companion.get_goal_reminder(self.history)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt_and_functions(self):
        engine = self.session.game_engine
        state = engine.state_engine.get_current_state()
        actions = engine.state_engine.get_available_actions()
        prompt = self.prompt_builder.build_system_prompt(state, engine.inventory, engine.game_data)
        functions = self.prompt_builder.build_functions(actions)
        return prompt, functions

    def _send_initial_ambient(self) -> None:
        jukebox = self.session.jukebox
        if not jukebox:
            return
        state = self.session.game_engine.state_engine.get_current_state()
        if state.ambient_sound:
            jukebox.play_sound(
                self.session,
                state.ambient_sound,
                volume=state.ambient_sound_volume,
                loop=True,
            )
