from typing import Optional
from llm import LLMFactory, LLMMessage


class GameController:
    """
    Controls the game flow by integrating GameEngine with LLM.
    """
    
    def __init__(self, session):
        """
        Initialize the game controller.
        
        Args:
            session: GameSession (has game_engine.state_engine)
        """
        self.session = session
        # LLM is implementation detail of this controller
        self.llm_factory = LLMFactory()
        self.llm_provider = self.llm_factory.create_provider()
        self.chat_history = []
        
        # Get max history length from config
        self.max_history_length = self.llm_factory.config.get('max_history_length', 20)
    
    def _trim_history(self):
        """
        Trim chat history to max_history_length.
        Always keeps system prompt (index 0) + last N messages.
        """
        if len(self.chat_history) <= self.max_history_length:
            return
        
        # Keep system prompt + last (max_history_length - 1) messages
        system_prompt = self.chat_history[0]
        recent_messages = self.chat_history[-(self.max_history_length - 1):]
        self.chat_history = [system_prompt] + recent_messages
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        state_engine = self.session.game_engine.state_engine
        game_data = self.session.game_engine.game_data
        actions = state_engine.get_available_actions()
        
        # Combine identity and behaviour from game_data
        prompt = ""
        
        identity = game_data.get('identity', '')
        if identity:
            prompt += identity + "\n\n"
        
        behaviour = game_data.get('behaviour', '')
        if behaviour:
            prompt += behaviour + "\n\n"
        
        # Add current room description
        current_state = state_engine.get_current_state()
        prompt += f"AKTUELLER RAUM:\n{current_state.get_description()}\n\n"
        
        prompt += """WICHTIG: Du musst IMMER mit einer der folgenden Aktionen antworten:

Verfügbare Aktionen:
"""
        
        for action in actions:
            prompt += f"- {action.name}: {action.description}"
            if action.after_fire:
                prompt += f" [Wenn gewählt: {action.after_fire}]"
            prompt += "\n"
        
        prompt += """- keine_aktion: Wenn keine der Aktionen passt

ANTWORT-FORMAT:
1. Antworte dem Spieler in einem Satz
2. Wähle EINE Aktion aus der Liste
3. Format: [AKTION: action_name]

Beispiel:
"Du gehst nach Norden. [AKTION: gehe_to_B]"

Wenn keine Aktion passt:
"Ich verstehe nicht, was du tun möchtest. [AKTION: keine_aktion]"
"""
        
        return prompt
    
    def _extract_action(self, llm_response: str) -> Optional[str]:
        """
        Extract action name from LLM response.
        
        Args:
            llm_response: Response from LLM
            
        Returns:
            Action name or None
        """
        # Look for [AKTION: action_name] pattern
        import re
        match = re.search(r'\[AKTION:\s*(\w+)\]', llm_response)
        if match:
            return match.group(1)
        return None
    
    def _clean_response(self, llm_response: str) -> str:
        """Remove action marker and thinking from response."""
        import re
        
        # Remove action marker
        response = re.sub(r'\[AKTION:\s*\w+\]', '', llm_response).strip()
        
        # Pattern 1: Extract quoted text first (most reliable)
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            # Return the last quoted text (usually the final answer)
            return quoted[-1].strip()
        
        # Pattern 2: Remove thinking blocks (everything before first sentence)
        # Remove lines that start with thinking patterns
        lines = response.split('\n')
        clean_lines = []
        skip_mode = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this is a thinking line
            lower_line = line.lower()
            if any(lower_line.startswith(pattern) for pattern in [
                'if ', 'wait', 'looking', 'let me', 'i should', 'the player',
                'that\'s', 'let\'s', 'i need', 'i must', 'i will', 'i can'
            ]):
                skip_mode = True
                continue
            
            # If line ends with period/exclamation/question, we're past thinking
            if line.endswith(('.', '!', '?', '…')):
                skip_mode = False
            
            # Add line if not in skip mode
            if not skip_mode:
                clean_lines.append(line)
        
        if clean_lines:
            return ' '.join(clean_lines)
        
        # Fallback: return first sentence if nothing else works
        sentences = re.split(r'[.!?]\s+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                return sentence
        
        return response.strip()
    
    def start_game(self) -> str:
        """
        Start the game and return LLM's welcome message.
        The LLM receives the game description and welcomes the player in character.
        
        Returns:
            LLM's welcome message
        """
        self.chat_history = []
        
        # Add system prompt
        system_prompt = self._build_system_prompt()
        self.chat_history.append(
            LLMMessage(role="system", content=system_prompt)
        )
        
        # Send initial state description to LLM and ask for welcome
        state_description = self.session.game_engine.state_engine.get_current_state().get_description()
        welcome_prompt = f"""Das Spiel beginnt. Hier ist die Situation:

{state_description}

Begrüße den Spieler in deiner Rolle und bereite ihn auf das Abenteuer vor. Beschreibe die Situation und gib ihm einen ersten Hinweis, was er tun könnte."""
        
        self.chat_history.append(
            LLMMessage(role="user", content=welcome_prompt)
        )
        
        # Get LLM's welcome response
        try:
            response = self.llm_provider.chat(self.chat_history)
            welcome_text = response.content
        except Exception as e:
            # Fallback to state description if LLM fails
            return state_description
        
        # Add to history
        self.chat_history.append(
            LLMMessage(role="assistant", content=welcome_text)
        )
        
        # Clean and return welcome message
        return self._clean_response(welcome_text)
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and return LLM response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        # Add user input to history
        self.chat_history.append(
            LLMMessage(role="user", content=user_input)
        )
        
        # Update system prompt with current actions
        self.chat_history[0] = LLMMessage(
            role="system",
            content=self._build_system_prompt()
        )
        
        # Get LLM response
        try:
            response = self.llm_provider.chat(self.chat_history)
            llm_text = response.content
        except Exception as e:
            return f"Fehler beim LLM-Aufruf: {e}"
        
        # Add to history
        self.chat_history.append(
            LLMMessage(role="assistant", content=llm_text)
        )
        
        # Trim history if needed (keep system prompt + last N messages)
        self._trim_history()
        
        # Extract action
        action_name = self._extract_action(llm_text)
        clean_response = self._clean_response(llm_text)
        
        # Handle no action
        if action_name == "keine_aktion" or action_name is None:
            return clean_response
        
        # Execute action
        success, message = self.session.game_engine.state_engine.set_state(action_name)
        
        if success:
            # Return only LLM response, no state description
            return clean_response
        else:
            # Action failed (hook veto or invalid)
            return f"{clean_response}\n\n(Action konnte nicht ausgeführt werden: {message})"
    
