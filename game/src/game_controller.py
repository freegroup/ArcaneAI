from __future__ import annotations
import threading
from typing import TYPE_CHECKING, List, Optional

from llm import LLMFactory, LLMMessage, LLMFunction, BaseLLMProvider
from game_history import GameHistory
from voice import VoiceFactory, BaseTTSProvider

if TYPE_CHECKING:
    from session import GameSession


class GameController:
    """
    Controls the game flow by integrating GameEngine with LLM.
    Uses structured history for debugging and analysis.
    """

    def __init__(self, session: GameSession) -> None:
        """
        Initialize the game controller.

        Args:
            session: GameSession (has game_engine.state_engine, audio_sink)
        """
        self.session: GameSession = session
        # LLM is implementation detail of this controller
        self.llm_factory: LLMFactory = LLMFactory()
        self.llm_provider: BaseLLMProvider = self.llm_factory.create_provider()

        # Structured history instead of simple message list
        max_length: int = self.llm_factory.config.get('llm', {}).get('max_history_length', 20)
        self.history: GameHistory = GameHistory(max_length=max_length)

        # Voice/TTS provider with audio sink from session
        self.voice_factory: VoiceFactory = VoiceFactory()
        self.voice_provider: BaseTTSProvider = self.voice_factory.create_provider(session.audio_sink)

    def _build_base_prompt(self) -> str:
        """
        Build base system prompt (identity, behavior, current state).
        Does NOT include function calling instructions.
        """
        from state_engine import StateEngine
        
        state_engine: StateEngine = self.session.game_engine.state_engine
        game_data: dict = self.session.game_engine.game_data

        # Combine identity and behaviour from game_data
        prompt: str = ""

        identity: str = game_data.get('identity', '')
        if identity:
            prompt += identity + "\n\n"

        behaviour: str = game_data.get('behaviour', '')
        if behaviour:
            prompt += behaviour + "\n\n"

        # Add current room description
        from state_engine import State
        current_state: State = state_engine.get_current_state()
        prompt += f"AKTUELLER RAUM:\n{current_state.get_description()}\n"

        return prompt

    def _build_functions(self) -> List[LLMFunction]:
        """
        Build list of available functions from current game state.
        Each action becomes a callable function.
        """
        from state_engine import StateEngine, Action
        
        state_engine: StateEngine = self.session.game_engine.state_engine
        actions: List[Action] = state_engine.get_available_actions()

        functions: List[LLMFunction] = []
        for action in actions:
            # Build description with after_fire hint if available
            description: str = action.description
            if action.after_fire:
                description += f". Falls du diese Aktion auswählst, dann bitte dies in deiner Antwort berücksichtigen: {action.after_fire}"

            functions.append(LLMFunction(
                name=action.name,
                description=description,
                parameters={
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "Deine narrative Antwort an den Spieler (kurz, in character)"
                        }
                    },
                    "required": ["response"]
                }
            ))

        # Always add fallback action
        functions.append(LLMFunction(
            name="keine_aktion",
            description="Keine der Aktionen passt zur Eingabe des Spielers",
            parameters={
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "Erkläre dem Spieler, warum du seine Eingabe nicht verstehst"
                    }
                },
                "required": ["response"]
            }
        ))

        return functions

    def start_game(self) -> str:
        """
        Start the game and return LLM's welcome message.

        Returns:
            LLM's welcome message
        """
        self.history.clear()

        # Build base prompt and functions
        base_prompt: str = self._build_base_prompt()
        functions: List[LLMFunction] = self._build_functions()

        # Get welcome prompt from game definition
        # NOTE: Room description is already in base_prompt (AKTUELLER RAUM section)
        game_data: dict = self.session.game_engine.game_data
        welcome_prompt: str = game_data.get('welcome_prompt', 'Das Spiel beginnt!')

        # Create messages for LLM call
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=base_prompt),
            LLMMessage(role="user", content=welcome_prompt)
        ]

        # Get LLM's welcome response
        from llm import LLMResponse
        try:
            response: LLMResponse = self.llm_provider.chat_with_functions(
                messages,
                functions,
                base_prompt
            )
            welcome_text: str = response.content
        except Exception:
            # Fallback to state description if LLM fails
            current_state = self.session.game_engine.state_engine.get_current_state()
            return current_state.get_description()

        # Add to structured history
        self.history.add_entry(
            user_input=welcome_prompt,
            base_prompt=base_prompt,
            available_functions=functions,
            llm_response=welcome_text,
            chosen_function="keine_aktion",
            metadata={"type": "welcome"}
        )

        # Send initial ambient sound for starting state
        self._send_initial_ambient()

        # Convert to speech
        self.voice_provider.speak(self.session, welcome_text)

        return welcome_text

    def process_input(self, user_input: str) -> dict:
        """
        Process user input and return LLM response with metadata.

        Args:
            user_input: User's input text

        Returns:
            Dict with 'response' (str), 'executed_action' (str or None)
        """
        from llm import LLMResponse
        
        # Build current functions and base prompt
        base_prompt: str = self._build_base_prompt()
        functions: List[LLMFunction] = self._build_functions()

        # Convert history to LLM messages
        messages: List[LLMMessage] = self.history.to_llm_messages(base_prompt)

        # Add current user input
        messages.append(LLMMessage(role="user", content=user_input))

        # Get LLM response with function calling
        try:
            response: LLMResponse = self.llm_provider.chat_with_functions(messages, functions, base_prompt)
        except Exception as e:
            return f"Fehler beim LLM-Aufruf: {e}"

        # Extract narrative response and function call
        from llm import LLMFunctionCall
        
        narrative_response: str = response.content
        function_call: Optional[LLMFunctionCall] = response.function_call

        # Handle function call result
        chosen_function_name: Optional[str] = None
        if function_call:
            chosen_function_name = function_call.name
        else:
            # Parsing failed - provide fallback message instead of raw output
            narrative_response = "Ich bin verwirrt... Kannst du das anders formulieren?"

        # Execute the action if one was chosen
        function_success: bool = True
        if function_call and function_call.name != "keine_aktion":
            action_name: str = function_call.name
            success: bool
            message: str
            success, message = self.session.game_engine.state_engine.execute_action(action_name)
            function_success = success

            if not success:
                # Action failed (hook veto or invalid)
                narrative_response = f"{narrative_response}\n\n(Action konnte nicht ausgeführt werden: {message})"

        # Add to structured history
        self.history.add_entry(
            user_input=user_input,
            base_prompt=base_prompt,
            available_functions=functions,
            llm_response=narrative_response,
            chosen_function=chosen_function_name,
            function_success=function_success
        )

        # Stop any current speech before starting new one
        self.voice_provider.stop(self.session)

        # Convert to speech in background thread (non-blocking)
        # This allows the text response to return immediately
        tts_thread = threading.Thread(
            target=self.voice_provider.speak,
            args=(self.session, narrative_response),
            daemon=True
        )
        tts_thread.start()

        # Return response with metadata
        return {
            'response': narrative_response,
            'executed_action': chosen_function_name if chosen_function_name != "keine_aktion" else None
        }

    def _send_initial_ambient(self) -> None:
        """Play ambient sound for the initial game state via jukebox."""
        from typing import Any
        from state_engine import State
        
        jukebox: Optional[Any] = self.session.jukebox
        if not jukebox:
            return

        state: State = self.session.game_engine.state_engine.get_current_state()
        if state.ambient_sound:
            jukebox.play_sound(
                self.session,
                state.ambient_sound,
                volume=state.ambient_sound_volume,
                loop=True
            )
