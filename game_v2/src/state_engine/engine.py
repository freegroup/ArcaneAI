"""
State Engine for managing game states and actions.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from .state import State
from .action import Action

if TYPE_CHECKING:
    from session import GameSession
    from scripting.lua import LuaSandbox


class StateEngine:
    """
    Manages game states and actions.
    Does NOT load files - receives data from GameEngine.
    """
    
    def __init__(
        self,
        session: GameSession,
        states: Dict[str, Dict[str, Any]],
        actions: List[Dict[str, Any]],
        initial_state: str
    ) -> None:
        """
        Initialize the state engine with game data.
        
        Args:
            session: GameSession for message passing (REQUIRED)
            states: Dictionary of state definitions
            actions: List of action definitions
            initial_state: Name of the initial state
        """
        self.session: GameSession = session
        self.states: Dict[str, State] = {}
        self.actions: List[Action] = []
        self.action_hooks: List[Callable[[Action], bool]] = []
        self.current_state: str = ""
        
        # Load states with session reference for template rendering
        for state_name, state_data in states.items():
            self.states[state_name] = State(
                name=state_name,
                description=state_data['description'],
                session=session,
                ambient_sound=state_data.get('ambient_sound'),
                ambient_sound_volume=state_data.get('ambient_sound_volume', 100)
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
                scripts=action_data.get('scripts', []),
                sound_effect=action_data.get('sound_effect'),
                sound_effect_volume=action_data.get('sound_effect_volume', 100),
                sound_effect_duration=action_data.get('sound_effect_duration')
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
    
    def add_action_hook(self, hook: Callable[[Action], bool]) -> None:
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
    
    def _check_conditions(self, conditions: List[str], lua_sandbox: LuaSandbox) -> bool:
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

        # Send sound events via message queue
        self._send_sound_events(action, old_state)

        # Build message
        if old_state == action.state_after:
            message = f"Action '{name}' ausgeführt (State bleibt {self.current_state})."
        else:
            message = f"State gewechselt von {old_state} nach {self.current_state}."

        return True, message

    def _send_sound_events(self, action: Action, old_state: str) -> None:
        """Play sound effect and ambient sound after a state transition via jukebox."""
        jukebox: Optional[Any] = self.session.jukebox
        if not jukebox:
            return

        # Play sound effect for the action (one-shot)
        if action.sound_effect:
            jukebox.play_sound(
                self.session,
                action.sound_effect,
                volume=action.sound_effect_volume,
                loop=False,
                duration=action.sound_effect_duration or 0
            )

        # Play ambient sound for the new state (looping)
        new_state = self.states.get(self.current_state)
        old_state_obj = self.states.get(old_state)

        if new_state:
            new_ambient = new_state.ambient_sound
            old_ambient = old_state_obj.ambient_sound if old_state_obj else None

            if new_ambient != old_ambient or old_state != self.current_state:
                # Stop old ambient first
                jukebox.stop_ambient(self.session)
                # Start new ambient if any
                if new_ambient:
                    jukebox.play_sound(
                        self.session,
                        new_ambient,
                        volume=new_state.ambient_sound_volume,
                        loop=True
                    )
