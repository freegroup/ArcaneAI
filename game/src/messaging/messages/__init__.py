"""
Message classes for type-safe messaging.
Each message type in its own file.
"""
from .base import Message
from .inventory import InventoryMessage
from .state import StateMessage
from .text import TextMessage
from .error import ErrorMessage
from .sound import AmbientSoundMessage, SoundEffectMessage

__all__ = [
    'Message',
    'InventoryMessage',
    'StateMessage',
    'TextMessage',
    'ErrorMessage',
    'AmbientSoundMessage',
    'SoundEffectMessage'
]
