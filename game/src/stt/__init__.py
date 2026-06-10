"""
STT (Speech-to-Text) provider package.
"""
from .base_provider import BaseSTTProvider
from .console_provider import ConsoleSTTProvider
from .stt_factory import STTFactory

__all__ = [
    'BaseSTTProvider',
    'ConsoleSTTProvider',
    'STTFactory',
]
