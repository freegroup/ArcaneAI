"""
Base Message class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class Message(ABC):
    """Base class for all messages."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary for JSON/WebSocket."""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """Message type identifier."""
        pass