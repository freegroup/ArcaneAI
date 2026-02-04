"""
Text Message.
"""
from dataclasses import dataclass
from typing import Dict, Any
from .base import Message


@dataclass
class TextMessage(Message):
    """Generic text message."""
    text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": {"text": self.text}
        }
    
    @property
    def type(self) -> str:
        return "text"