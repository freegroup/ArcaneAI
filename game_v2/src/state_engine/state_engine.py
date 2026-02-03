"""
State Engine for managing game states and actions.
"""
import json
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass


@dataclass
class State:
    """Represents a game state."""
    name: str
    description: str


@dataclass
class Action:
    """Represents an action that can be performed."""
    state_before: str
    state_after: str
    name: str
    description: str
    on_transition: str = ""  # Context text for LLM when this action is chosen


class StateEngine:
    """
    Manages game states and actions.
    Loads from game_definition.json and handles state transitions.
    """
    
    def __init__(self, definition_path: str):
        """
        Initialize the state engine.
        
        Args:
            definition_path: Path to game_definition.json
        """
        self.definition_path = Path(definition_path)
        self.states: Dict[str, State] = {}
        self.actions: List[Action] = []
        self.current_state: Optional[str] = None
        self.action_hook: Optional[Callable[[Action], bool]] = None
        self.identity: str = ""
        self.behaviour: str = ""
        
        self._load_definition()
    
    def _load_definition(self):
        """Load game definition from JSON file."""
        if not self.definition_path.exists():
            raise FileNotFoundError(f"Game definition not found: {self.definition_path}")
        
        with open(self.definition_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load states
        for state_name, state_data in data.get('states', {}).items():
            self.states[state_name] = State(
                name=state_name,
                description=state_data['description']
            )
        
        # Load actions
        for action_data in data.get('actions', []):
            self.actions.append(Action(
                state_before=action_data['state_before'],
                state_after=action_data['state_after'],
                name=action_data['name'],
                description=action_data['description'],
                on_transition=action_data.get('on_transition', '')
            ))
        
        # Load identity and behaviour
        self.identity = data.get('identity', '')
        self.behaviour = data.get('behaviour', '')
        
        # Set initial state from definition, or fallback to first state
        initial_state = data.get('initial_state')
        if initial_state and initial_state in self.states:
            self.current_state = initial_state
        elif self.states:
            self.current_state = list(self.states.keys())[0]
    
    def set_action_hook(self, hook: Callable[[Action], bool]):
        """
        Set a hook that is called before state transitions.
        
        Args:
            hook: Function that receives an Action and returns True to allow, False to veto
        """
        self.action_hook = hook
    
    def get_current_state(self) -> Optional[State]:
        """Get the current state object."""
        if self.current_state:
            return self.states.get(self.current_state)
        return None
    
    def get_current_state_name(self) -> str:
        """Get the name of the current state."""
        return self.current_state or "Unknown"
    
    def get_current_state_description(self) -> str:
        """Get the description of the current state."""
        state = self.get_current_state()
        return state.description if state else "Kein State aktiv."
    
    def get_available_actions(self) -> List[Action]:
        """Get all actions available in the current state."""
        if not self.current_state:
            return []
        
        return [
            action for action in self.actions
            if action.state_before == self.current_state
        ]
    
    def get_action_by_name(self, action_name: str) -> Optional[Action]:
        """
        Get an action by name that is available in the current state.
        
        Args:
            action_name: Name of the action
            
        Returns:
            Action object or None if not found/not available
        """
        available = self.get_available_actions()
        for action in available:
            if action.name == action_name:
                return action
        return None
    
    def execute_action(self, action_name: str) -> tuple[bool, str]:
        """
        Execute an action by name.
        
        Args:
            action_name: Name of the action to execute
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Find the action
        action = self.get_action_by_name(action_name)
        if not action:
            return False, f"Action '{action_name}' ist im aktuellen State nicht verfügbar."
        
        # Call hook if set - hook can veto the action
        if self.action_hook:
            if not self.action_hook(action):
                return False, f"Action '{action_name}' wurde durch Hook blockiert."
        
        # Perform state transition
        old_state = self.current_state
        self.current_state = action.state_after
        
        # Build message
        if old_state == action.state_after:
            message = f"Action '{action_name}' ausgeführt (State bleibt {self.current_state})."
        else:
            message = f"State gewechselt von {old_state} nach {self.current_state}."
        
        return True, message
    
    def get_available_action_names(self) -> List[str]:
        """Get list of available action names in current state."""
        return [action.name for action in self.get_available_actions()]
    
    def get_available_actions_description(self) -> str:
        """Get a formatted string of available actions with descriptions."""
        actions = self.get_available_actions()
        if not actions:
            return "Keine Aktionen verfügbar."
        
        lines = []
        for action in actions:
            lines.append(f"- {action.name}: {action.description}")
        
        return "\n".join(lines)