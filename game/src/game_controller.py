from __future__ import annotations
import threading
from typing import TYPE_CHECKING, Optional

from llm import LLMFactory, BaseLLMProvider
from game_history import GameHistory
from voice import VoiceFactory, BaseTTSProvider
from prompt_config import DecisionConfig, GoalConfig, MoodConfig, NarrationConfig
from builtin_functions import BuiltinRegistry
from prompt_builder import PromptBuilder
from stage_1_decision import DecisionStage
from function_executor import FunctionExecutor
from stage_2_narration import NarrationStage
from companion_director import CompanionDirector

if TYPE_CHECKING:
    from session import GameSession


class GameController:
    """
    Runs one turn of the game loop:

    1. Stage 1 (DecisionStage): the model picks the function the player's
       input asks for — a game action or a built-in one.
    2. Run it (FunctionExecutor): a game action changes the world; a
       built-in function only says how to answer.
    3. Stage 2 (NarrationStage): the model tells the player, in the game's
       personality.

    Each stage runs on its own LLM (llm.stage1 / llm.stage2 / llm.mood in
    config.yaml) and reads its prompts from game/prompts/ — or from
    game/prompts/<provider>/ if that provider brings its own.
    """

    def __init__(self, session: GameSession) -> None:
        self.session = session

        factory = LLMFactory()
        self.decision_llm: BaseLLMProvider = factory.create_provider(stage='stage1')
        self.narration_llm: BaseLLMProvider = factory.create_provider(stage='stage2')
        self.mood_llm: BaseLLMProvider = factory.create_provider(stage='mood')

        max_length: int = factory.config.get('llm', {}).get('max_history_length', 20)
        self.history: GameHistory = GameHistory(max_length=max_length)

        builtins = BuiltinRegistry(self.decision_llm.name)
        with_action = NarrationConfig.load('prompt_rule_stage2_with_function', self.narration_llm.name)
        no_action = NarrationConfig.load('prompt_rule_stage2_without_function', self.narration_llm.name)
        self.decision = DecisionStage(
            self.decision_llm,
            PromptBuilder(builtins, DecisionConfig.load(self.decision_llm.name)),
            builtins,
        )
        self.executor = FunctionExecutor(builtins, with_action.extra['actionNote'])
        self.narration = NarrationStage(self.narration_llm, with_action, no_action)

        self.voice: BaseTTSProvider = VoiceFactory().create_provider(session.audio_sink)
        self._companion: Optional[CompanionDirector] = None

    @property
    def companion(self) -> CompanionDirector:
        # Lazy: the inventory exists only once GameEngine is fully built.
        if self._companion is None:
            engine = self.session.game_engine
            self._companion = CompanionDirector(
                self.mood_llm, engine.inventory, engine.game_data,
                MoodConfig.load(self.mood_llm.name), GoalConfig.load(self.mood_llm.name),
            )
        return self._companion

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_game(self) -> str:
        """The opening narration. Nothing is decided; starts the room ambience."""
        self.history.clear()
        engine = self.session.game_engine

        try:
            welcome_text = self.narration.welcome(engine) or self.narration.fallback_answer
        except Exception as e:
            print(f'[CONTROLLER] Begrüßung fehlgeschlagen: {e}')
            return engine.state_engine.get_current_state().get_description()

        self.history.add_entry(
            user_input=self.narration.welcome_input(engine),
            llm_response=welcome_text,
            metadata={'type': 'welcome'},
        )

        self.send_ambient()
        self.voice.speak(self.session, welcome_text)
        return welcome_text

    def process_input(self, user_input: str) -> dict:
        engine = self.session.game_engine

        # The player interrupted: the previous answer must not keep talking.
        self.stop_speaking()

        # Stage 1: which function.
        chosen = self.decision.decide(engine, self.history, user_input)

        # Run it.
        outcome = self.executor.run(engine, chosen)

        # Stage 2: what the player is told.
        try:
            narrative = self.narration.tell(
                engine, self.history, user_input, outcome.note,
                action_executed=outcome.fired_action is not None,
            )
        except Exception as e:
            print(f'[CONTROLLER] Stufe 2 fehlgeschlagen: {e}')
            narrative = ''
        narrative = narrative or self.narration.fallback_answer

        self.history.add_entry(
            user_input=user_input,
            llm_response=narrative,
            chosen_function=outcome.function,
            function_success=outcome.function != self.executor.builtins.on_error.name,
        )

        self.companion.update_async(self.history)

        threading.Thread(
            target=self.voice.speak, args=(self.session, narrative), daemon=True
        ).start()

        return {
            'response': narrative,
            'executed_action': outcome.fired_action,
            'game_over': engine.state_engine.get_current_state().is_end,
        }

    def stop_speaking(self) -> None:
        """
        Stop the current speech on the server (no more audio is sent) and tell
        the client to drop what it has already received. Blocks until the
        speech thread has ended.
        """
        self.voice.stop(self.session)
        if self.session.message_queue:
            self.session.message_queue.send('speak_stop', {})

    # kept for external callers (e.g. runners that check goal drift)
    def get_game_target_reminder(self) -> str:
        return self.companion.get_goal_reminder(self.history)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def send_ambient(self) -> None:
        """Start the current room's ambient sound (game start, client reconnect)."""
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
