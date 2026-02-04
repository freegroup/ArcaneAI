"""
Console message queue implementation.
"""
import json
from typing import Dict, Any
from .base import MessageQueue


class ConsoleMessageQueue(MessageQueue):
    """
    Message queue for console/terminal output.
    Simply prints messages to stdout.
    """
    
    def send(self, message, data: Dict[str, Any] = None):
        """Print message to console."""
        # Handle Message objects
        if hasattr(message, 'to_dict'):
            message_dict = message.to_dict()
            message_type = message_dict['type']
            data = message_dict.get('data', {})
        else:
            # Legacy string type
            message_type = message
            data = data or {}
        
        if message_type == "chat_response":
            # Just print the text for chat responses
            print(data.get('text', ''))
        elif message_type == "inventory_update":
            # Print inventory updates
            print(f"\n[INVENTORY UPDATE] {json.dumps(data, indent=2)}\n")
        elif message_type == "state_change":
            # Print state changes
            print(f"\n[STATE] → {data.get('state')}\n")
        else:
            # Generic message
            print(f"\n[{message_type.upper()}] {json.dumps(data, indent=2)}\n")