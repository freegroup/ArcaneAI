"""
Base class for message queues.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from .messages import Message


class MessageQueue(ABC):
    """
    Abstract base class for message queues.
    Allows components to send messages without knowing the transport.
    """
    
    @abstractmethod
    def send(self, message: Union[Message, str], data: Optional[Dict[str, Any]] = None) -> None:
        """
        Send a message to the client.
        
        Args:
            message: Message object or legacy string type
            data: Message data (only used with legacy string type)
        """
        pass
