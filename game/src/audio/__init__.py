"""
Audio Package
Provides audio sink implementations for TTS output.
"""
from .base_sink import BaseAudioSink
from .websocket_sink import WebSocketSink
from .null_sink import NullSink
from .pyaudio_sink import PyAudioSink

__all__ = [
    'BaseAudioSink',
    'WebSocketSink',
    'NullSink',
    'PyAudioSink',
]
