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
        llm_factory = LLMFactory()
        self.llm_provider = llm_factory.create_provider()
        self.conversation_history = []
    
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
        
        # Remove thinking blocks (common patterns from reasoning models)
        # Pattern 1: Text between quotes after "Wait" or "Looking"
        response = re.sub(r'Wait,.*?(?="|$)', '', response, flags=re.DOTALL)
        response = re.sub(r'Looking.*?(?="|$)', '', response, flags=re.DOTALL)
        
        # Pattern 2: Extract only quoted text if present
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            # Return the last quoted text (usually the final answer)
            return quoted[-1].strip()
        
        # Pattern 3: Remove lines that look like thinking
        lines = response.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty lines or thinking patterns
            if not line:
                continue
            if line.lower().startswith(('wait', 'looking', 'let me', 'i should')):
                continue
            clean_lines.append(line)
        
        if clean_lines:
            return ' '.join(clean_lines)
        
        return response.strip()
    
    def start_game(self) -> str:
        """
        Start the game and return initial state description.
        
        Returns:
            Initial state description
        """
        self.conversation_history = []
        
        # Add system prompt
        system_prompt = self._build_system_prompt()
        self.conversation_history.append(
            LLMMessage(role="system", content=system_prompt)
        )
        
        # Return current state description
        return self.session.game_engine.state_engine.get_current_state().get_description()
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and return LLM response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        # Add user input to history
        self.conversation_history.append(
            LLMMessage(role="user", content=user_input)
        )
        
        # Update system prompt with current actions
        self.conversation_history[0] = LLMMessage(
            role="system",
            content=self._build_system_prompt()
        )
        
        # Get LLM response
        try:
            response = self.llm_provider.chat(self.conversation_history)
            llm_text = response.content
        except Exception as e:
            return f"Fehler beim LLM-Aufruf: {e}"
        
        # Add to history
        self.conversation_history.append(
            LLMMessage(role="assistant", content=llm_text)
        )
        
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
    
