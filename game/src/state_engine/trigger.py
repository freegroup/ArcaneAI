"""
Trigger class - action that stays in the same state (interaction).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from .action import Action


@dataclass
class Trigger(Action):
    """
    A trigger is an action that stays in the same state.
    Used for interactions with objects/NPCs in the current location.
    
    Examples:
    - untersuche_den_raum
    - nehme_das_packet
    - rede_mit_waechter
    - oeffne_tuer_mit_gewalt
    """
    state: str = ""  # The state this trigger belongs to (required but with default for dataclass ordering)
    
    def __post_init__(self) -> None:
        """Validate that trigger has a state."""
        super().__post_init__()
        
        if not self.state:
            raise ValueError(f"Trigger '{self.name}' must have a state")
    
    def check_conditions(self, current_state: str, lua_sandbox) -> bool:
        """
        Check if this trigger is available.
        Overrides Action to add state check before checking Lua conditions.
        
        Args:
            current_state: The current state to check against
            lua_sandbox: LuaSandbox to evaluate conditions
            
        Returns:
            True if trigger is available (correct state AND conditions met)
        """
        # Check if trigger is in current state
        if self.state != current_state:
            return False
        
        # Check Lua conditions via parent class
        return super().check_conditions(current_state, lua_sandbox)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Trigger(name='{self.name}', state='{self.state}')"
    
    def fire(self, state_engine) -> tuple[bool, str]:
        """
        Fire this trigger - execute scripts but stay in same state.
        
        Args:
            state_engine: The StateEngine (state won't change)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get lua sandbox
        lua_sandbox = state_engine.session.game_engine.inventory.lua
        
        # Execute scripts/actions
        if not self.execute_actions(lua_sandbox):
            return False, f"Failed to execute scripts for trigger '{self.name}'"
        
        # Send sound events (but state stays the same)
        state_engine._send_sound_events(self, state_engine.current_state)
        
        # Build message
        message = f"Trigger '{self.name}' ausgeführt (State bleibt {state_engine.current_state})."
        
        return True, message
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        desc_preview = self.description[:30] + "..." if len(self.description) > 30 else self.description
        scripts_info = f", scripts={len(self.scripts)}" if self.scripts else ""
        conditions_info = f", conditions={len(self.conditions)}" if self.conditions else ""
        return f"Trigger(name='{self.name}', state='{self.state}', desc='{desc_preview}'{conditions_info}{scripts_info})"