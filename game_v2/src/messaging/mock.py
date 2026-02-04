"""
Mock message queue implementation for testing.
"""
from typing import Dict, Any
from .base import MessageQueue


class MockMessageQueue(MessageQueue):
    """
    Mock message queue for testing.
    Records all messages but doesn't send them anywhere.
    """
    
    def __init__(self):
        """Initialize empty message log."""
        self.messages = []
    
    def send(self, message, data: Dict[str, Any] = None):
        """Store message in buffer."""
        # Handle Message objects
        if hasattr(message, 'to_dict'):
            message_dict = message.to_dict()
        else:
            # Legacy string type
            message_dict = {
                "type": message,
                "data": data or {}
            }
        self.messages.append(message_dict)
    
    def get_sent_messages(self) -> list:
        """Get all sent messages."""
        return self.messages.copy()
    
    def clear(self):
        """Clear message log."""
        self.messages.clear()