from typing import Optional
from llm import LLMFactory, LLMMessage
from state_engine import StateEngine, Action


class GameController:
    """
    Controls the game flow by integrating StateEngine with LLM.
    """
    
    def __init__(self, state_engine: StateEngine, llm_factory: LLMFactory):
        """
        Initialize the game controller.
        
        Args:
            state_engine: StateEngine instance
            llm_factory: LLMFactory instance
        """
        self.state_engine = state_engine
        self.llm_provider = llm_factory.create_provider()
        self.conversation_history = []
        
        # Set up action hook
        self.state_engine.set_action_hook(self._action_hook)
    
    def _action_hook(self, action: Action) -> bool:
        """
        Hook called before action execution.
        Can be overridden to add custom logic.
        
        Args:
            action: The action about to be executed
            
        Returns:
            True to allow, False to veto
        """
        # Log the action (only state transition, no description)
        print(f"[HOOK] {action.state_before} → {action.state_after}")
        
        # Default: always allow
        # Override this method to add custom veto logic
        return True
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        actions = self.state_engine.get_available_actions()
        
        # Combine identity and behaviour
        prompt = ""
        
        if self.state_engine.identity:
            prompt += self.state_engine.identity + "\n\n"
        
        if self.state_engine.behaviour:
            prompt += self.state_engine.behaviour + "\n\n"
        
        # Add current room description
        current_state_desc = self.state_engine.get_current_state_description()
        prompt += f"AKTUELLER RAUM:\n{current_state_desc}\n\n"
        
        prompt += """WICHTIG: Du musst IMMER mit einer der folgenden Aktionen antworten:

Verfügbare Aktionen:
"""
        
        for action in actions:
            prompt += f"- {action.name}: {action.description}"
            if action.on_transition:
                prompt += f" [Wenn gewählt: {action.on_transition}]"
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
        """Remove action marker from response."""
        import re
        return re.sub(r'\[AKTION:\s*\w+\]', '', llm_response).strip()
    
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
        return self.state_engine.get_current_state_description()
    
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
        success, message = self.state_engine.execute_action(action_name)
        
        if success:
            # Return only LLM response, no state description
            return clean_response
        else:
            # Action failed (hook veto or invalid)
            return f"{clean_response}\n\n(Action konnte nicht ausgeführt werden: {message})"
    
    def get_current_state(self) -> str:
        """Get current state name."""
        return self.state_engine.get_current_state_name()
