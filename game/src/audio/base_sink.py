"""
Abstract base class for audio sinks.
"""
from abc import ABC, abstractmethod


class BaseAudioSink(ABC):
    """
    Base class for all audio sinks.
    Audio sinks handle where the audio goes (WebSocket, local playback, file, etc.).
    """

    def __init__(self):
        """Initialize audio sink."""
        pass

    @abstractmethod
    def write(self, session, chunk: bytes) -> None:
        """
        Write audio chunk to sink.

        Args:
            session: Game session (for session-aware routing)
            chunk: Audio data chunk
        """
        pass

    @abstractmethod
    def close(self, session) -> None:
        """
        Close audio sink and cleanup resources.

        Args:
            session: Game session
        """
        pass
