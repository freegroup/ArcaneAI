"""
Voice (TTS) Package
Provides text-to-speech functionality with multiple provider implementations.
"""
from .base_provider import BaseTTSProvider
from .console_provider import ConsoleTTSProvider
from .voice_factory import VoiceFactory

# Optional providers (imported on demand)
try:
    from .google_provider import GoogleTTSProvider
except ImportError:
    GoogleTTSProvider = None

try:
    from .openai_provider import OpenAITTSProvider
except ImportError:
    OpenAITTSProvider = None

try:
    from .xtts_provider import XTTSProvider
except ImportError:
    XTTSProvider = None

__all__ = [
    'BaseTTSProvider',
    'ConsoleTTSProvider',
    'VoiceFactory',
    'GoogleTTSProvider',
    'OpenAITTSProvider',
    'XTTSProvider',
]
