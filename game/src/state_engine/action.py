"""
Base Action class for state engine.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from scripting.lua import LuaSandbox


@dataclass
class Action(ABC):
    """
    Base class for actions that can be performed.
    Subclasses: Trigger (same state) and Transition (state change).
    """
    name: str
    prompts: Dict[str, str]  # Prompt information (description, after_fire)
    conditions: List[str] = field(default_factory=list)  # Conditions that must be met (Lua expressions)
    scripts: List[str] = field(default_factory=list)  # Scripts to execute when action is performed
    sound_effect: Optional[str] = None  # Sound effect file to play
    sound_effect_volume: int = 100
    sound_effect_duration: Optional[float] = None  # 0 or None = play full
    once: bool = False  # One-time action: once fired, it is never offered again
    
    def __post_init__(self) -> None:
        """Initialize conditions and scripts as empty lists if None."""
        # Ensure prompts has required keys
        if not isinstance(self.prompts, dict):
            self.prompts = {"description": str(self.prompts), "after_fire": ""}
        if "description" not in self.prompts:
            self.prompts["description"] = ""
        if "after_fire" not in self.prompts:
            self.prompts["after_fire"] = ""
    
    @property
    def description(self) -> str:
        """Get description from prompts."""
        return self.prompts.get("description", "")
    
    @property
    def after_fire(self) -> str:
        """Get after_fire text from prompts."""
        return self.prompts.get("after_fire", "")

    @property
    def room(self) -> str:
        """The room this action is offered in."""
        raise NotImplementedError

    @property
    def once_key(self) -> str:
        """
        Internal inventory variable marking a one-time action as done:
        once__<room>__<action> (a valid Lua name). It changes when the room or
        action is renamed, so games should not refer to it — they set their
        own variable in the action's scripts instead.
        """
        return re.sub(r'[^A-Za-z0-9_]', '_', f'once__{self.room}__{self.name}')
    
    def check_conditions(self, current_state: str, lua_sandbox: LuaSandbox) -> bool:
        """
        Check if this action is available.
        Base implementation checks Lua conditions only.
        Subclasses may override to add state checks (e.g., Transition).
        
        Args:
            current_state: The current state to check against
            lua_sandbox: LuaSandbox to evaluate conditions
            
        Returns:
            True if action is available, False otherwise
        """
        # A one-time action that already fired is gone for good
        if self.once and lua_sandbox.get_var(self.once_key):
            return False

        # Check Lua conditions
        if not self.conditions:
            return True  # No conditions = always available
        
        for condition in self.conditions:
            try:
                result = lua_sandbox.eval(f"return ({condition})")
                if not result:
                    return False
            except Exception as e:
                print(f"[WARNING] Failed to evaluate condition '{condition}' for action '{self.name}': {e}")
                return False
        
        return True
    
    def execute_actions(self, inventory) -> bool:
        """
        Execute all scripts of this action (once) via the inventory.
        This is common to both Triggers and Transitions.

        Returns:
            True if all scripts executed successfully, False otherwise
        """
        if not self.scripts:
            return True  # No scripts = success
        return inventory.run_scripts(self.name, self.scripts)
