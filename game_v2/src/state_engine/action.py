"""
Base Action class for state engine.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
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
    
    def execute_actions(self, lua_sandbox: LuaSandbox) -> bool:
        """
        Execute all scripts/actions for this action.
        This is common to both Triggers and Transitions.
        
        Args:
            lua_sandbox: LuaSandbox to execute scripts
            
        Returns:
            True if all scripts executed successfully, False otherwise
        """
        if not self.scripts:
            return True  # No scripts = success
        
        for script in self.scripts:
            if not script or script.strip() == "":
                continue  # Skip empty scripts
            
            try:
                # Use eval() which internally calls lua.execute()
                lua_sandbox.eval(script)
            except Exception as e:
                print(f"[WARNING] Failed to execute script '{script}' for action '{self.name}': {e}")
                return False
        
        return True
    
    @abstractmethod
    def fire(self, state_engine) -> tuple[bool, str]:
        """
        Fire this action - execute scripts and handle state.
        Must be implemented by Trigger and Transition subclasses.
        
        Args:
            state_engine: The StateEngine to update
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        desc_preview = self.description[:30] + "..." if len(self.description) > 30 else self.description
        scripts_info = f", scripts={len(self.scripts)}" if self.scripts else ""
        return f"{self.__class__.__name__}(name='{self.name}', desc='{desc_preview}'{scripts_info})"
