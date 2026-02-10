"""
Abstract base class for TTS (Text-to-Speech) providers.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from session import GameSession
    from audio.base_sink import BaseAudioSink


class BaseTTSProvider(ABC):
    """
    Base class for all TTS providers.
    Each provider generates audio from text and sends it to an audio sink.
    """

    def __init__(self, audio_sink: Optional[BaseAudioSink]) -> None:
        """
        Initialize TTS provider with an audio sink.

        Args:
            audio_sink: Audio sink for outputting generated audio
        """
        self.audio_sink: Optional[BaseAudioSink] = audio_sink

    @abstractmethod
    def speak(self, session: GameSession, text: str) -> None:
        """
        Convert text to speech and send to audio sink.

        Args:
            session: Game session (for session-aware audio routing)
            text: Text to convert to speech
        """
        pass

    @abstractmethod
    def stop(self, session: GameSession) -> None:
        """
        Stop current speech output.

        Args:
            session: Game session
        """
        pass
