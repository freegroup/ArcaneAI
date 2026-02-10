"""
Action class for state transitions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Action:
    """Represents an action that can be performed."""
    state_before: str
    state_after: str
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
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Action(name='{self.name}', {self.state_before} → {self.state_after})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        desc_preview = self.description[:30] + "..." if len(self.description) > 30 else self.description
        scripts_info = f", scripts={len(self.scripts)}" if self.scripts else ""
        return f"Action(name='{self.name}', {self.state_before} → {self.state_after}, desc='{desc_preview}'{scripts_info})"
