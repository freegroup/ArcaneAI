"""
State Engine for managing game states and actions.
"""
from typing import Dict, List, Optional, Callable
from .state import State
from .action import Action


class StateEngine:
    """
    Manages game states and actions.
    Does NOT load files - receives data from GameEngine.
    """
    
    def __init__(
        self,
        session,
        states: Dict[str, dict],
        actions: List[dict],
        initial_state: str
    ):
        """
        Initialize the state engine with game data.
        
        Args:
            session: GameSession for message passing (REQUIRED)
            states: Dictionary of state definitions
            actions: List of action definitions
            initial_state: Name of the initial state
        """
        self.session = session
        self.states: Dict[str, State] = {}
        self.actions: List[Action] = []
        self.action_hooks: List[Callable[[Action], bool]] = []
        
        # Load states with session reference for template rendering
        for state_name, state_data in states.items():
            self.states[state_name] = State(
                name=state_name,
                description=state_data['description'],
                session=session
            )
        
        # Load actions
        for action_data in actions:
            # Build prompts dict from action data
            prompts = action_data.get('prompts', {})
            
            # Backward compatibility: if no prompts dict, try old formats
            if not prompts:
                # Try 'prompt' (singular)
                prompts = action_data.get('prompt', {})
            if not prompts:
                # Try old fields
                prompts = {
                    "description": action_data.get('description', ''),
                    "after_fire": action_data.get('on_transition', '')
                }
            
            self.actions.append(Action(
                state_before=action_data['state_before'],
                state_after=action_data['state_after'],
                name=action_data['name'],
                prompts=prompts,
                conditions=action_data.get('conditions', []),
                scripts=action_data.get('scripts', [])
            ))
        
        # Set initial state
        if initial_state and initial_state in self.states:
            self.current_state = initial_state
        elif self.states:
            self.current_state = list(self.states.keys())[0]
        else:
            raise ValueError("No states defined")
        
        # Validate that we have an initial state
        if not self.current_state:
            raise ValueError("No initial_state defined")
    
    def add_action_hook(self, hook: Callable[[Action], bool]):
        """
        Add a hook that is called before state transitions.
        Multiple hooks can be registered.
        
        Args:
            hook: Function that receives an Action and returns True to allow, False to veto
        """
        self.action_hooks.append(hook)
    
    def get_current_state(self) -> State:
        """Get the current state object."""
        return self.states[self.current_state]
    
    def get_available_actions(self) -> List[Action]:
        """
        Get all actions available in the current state.
        Only returns actions whose conditions are met.
        """
        lua_sandbox = self.session.game_engine.inventory.lua
        available = []
        
        for action in self.actions:
            # Check if action is in current state
            if action.state_before != self.current_state:
                continue
            
            # Check if all conditions are met
            if not self._check_conditions(action.conditions, lua_sandbox):
                continue
            
            available.append(action)
        
        return available
    
    def _check_conditions(self, conditions: List[str], lua_sandbox) -> bool:
        """
        Check if all conditions are met.
        
        Args:
            conditions: List of Lua condition expressions
            lua_sandbox: LuaSandbox to evaluate conditions
            
        Returns:
            True if all conditions are met, False otherwise
        """
        if not conditions:
            return True  # No conditions = always available
        
        for condition in conditions:
            try:
                result = lua_sandbox.eval(f"return ({condition})")
                if not result:
                    return False
            except Exception as e:
                print(f"[WARNING] Failed to evaluate condition '{condition}': {e}")
                return False
        
        return True
    
    def get_action(self, name: str) -> Optional[Action]:
        """
        Get an action by name that is available in the current state.
        
        Args:
            name: Name of the action
            
        Returns:
            Action object or None if not found/not available
        """
        available = self.get_available_actions()
        for action in available:
            if action.name == name:
                return action
        return None
    
    def set_state(self, name: str) -> tuple[bool, str]:
        """
        Set state by executing the named action.
        
        Args:
            name: Name of the action to execute
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Find the action
        action = self.get_action(name)
        if not action:
            return False, f"Action '{name}' ist im aktuellen State nicht verfügbar."
        
        # Call all hooks - any hook can veto the action
        for hook in self.action_hooks:
            if not hook(action):
                return False, f"Action '{name}' wurde durch Hook blockiert."
        
        # Perform state transition
        old_state = self.current_state
        self.current_state = action.state_after
        
        # Build message
        if old_state == action.state_after:
            message = f"Action '{name}' ausgeführt (State bleibt {self.current_state})."
        else:
            message = f"State gewechselt von {old_state} nach {self.current_state}."
        
        return True, message
