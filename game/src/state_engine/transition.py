"""
Transition class - action that changes state (movement/navigation).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from .action import Action


@dataclass
class Transition(Action):
    """
    A transition is an action that changes from one state to another.
    Used for movement and navigation between locations.
    
    Examples:
    - gehe_zum_baum
    - klettere_fenster
    - gehe_nach_norden
    - gehe_in_die_gelbe_hoehle
    """
    state_before: str = ""  # The state to transition from (required but with default for dataclass ordering)
    state_after: str = ""   # The state to transition to (required but with default for dataclass ordering)
    
    def __post_init__(self) -> None:
        """Validate that transition changes state."""
        super().__post_init__()
        
        # Validate: Fields must be set
        if not self.state_before or not self.state_after:
            raise ValueError(f"Transition '{self.name}' must have both state_before and state_after")
        # Validate: Transition must have different state_before and state_after
        if self.state_before == self.state_after:
            raise ValueError(
                f"Transition '{self.name}' must have different state_before and state_after. "
                f"Got: {self.state_before} → {self.state_after} (same state!)"
            )
    
    def check_conditions(self, current_state: str, lua_sandbox) -> bool:
        """
        Check if this transition is available.
        Overrides Action to add state check before checking Lua conditions.
        
        Args:
            current_state: The current state to check against
            lua_sandbox: LuaSandbox to evaluate conditions
            
        Returns:
            True if transition is available (correct state AND conditions met)
        """
        # Check if transition is in current state
        if self.state_before != current_state:
            return False
        
        # Check Lua conditions via parent class
        return super().check_conditions(current_state, lua_sandbox)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Transition(name='{self.name}', {self.state_before} → {self.state_after})"
    
    def fire(self, state_engine) -> tuple[bool, str]:
        """
        Fire this transition - execute scripts and change state.
        
        Args:
            state_engine: The StateEngine to update
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get lua sandbox
        lua_sandbox = state_engine.session.game_engine.inventory.lua
        
        # Execute scripts/actions
        if not self.execute_actions(lua_sandbox):
            return False, f"Failed to execute scripts for transition '{self.name}'"
        
        # Update state (this is what makes it a Transition!)
        old_state = state_engine.current_state
        state_engine.current_state = self.state_after
        
        # Send sound events
        state_engine._send_sound_events(self, old_state)
        
        # Build message
        message = f"State gewechselt von {old_state} nach {state_engine.current_state}."
        
        return True, message
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        desc_preview = self.description[:30] + "..." if len(self.description) > 30 else self.description
        scripts_info = f", scripts={len(self.scripts)}" if self.scripts else ""
        conditions_info = f", conditions={len(self.conditions)}" if self.conditions else ""
        return f"Transition(name='{self.name}', {self.state_before} → {self.state_after}, desc='{desc_preview}'{conditions_info}{scripts_info})"