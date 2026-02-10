"""
Messaging package for sending messages to clients.
Provides abstraction layer for Console, WebSocket, etc.
"""
from .base import MessageQueue
from .console import ConsoleMessageQueue
from .websocket import WebSocketMessageQueue
from .messages import (
    Message,
    InventoryMessage,
    StateMessage,
    TextMessage,
    ErrorMessage
)

__all__ = [
    'MessageQueue',
    'ConsoleMessageQueue',
    'WebSocketMessageQueue',
    'Message',
    'InventoryMessage',
    'StateMessage',
    'TextMessage',
    'ErrorMessage'
]
