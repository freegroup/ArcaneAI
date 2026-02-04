"""
State Change Message.
"""
from dataclasses import dataclass
from typing import Dict, Any
from .base import Message


@dataclass
class StateMessage(Message):
    """Message sent when game state changes."""
    old_state: str
    new_state: str
    action: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": {
                "old_state": self.old_state,
                "new_state": self.new_state,
                "action": self.action
            }
        }
    
    @property
    def type(self) -> str:
        return "state_change"