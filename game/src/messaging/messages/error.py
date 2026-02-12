"""
Error Message.
"""
from dataclasses import dataclass
from typing import Dict, Any
from .base import Message


@dataclass
class ErrorMessage(Message):
    """Error message."""
    error: str
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"error": self.error}
        if self.details:
            data["details"] = self.details
        return {
            "type": self.type,
            "data": data
        }
    
    @property
    def type(self) -> str:
        return "error"