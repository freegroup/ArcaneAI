"""
Abstract base class for STT (Speech-to-Text) providers.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class BaseSTTProvider(ABC):
    """
    Base class for all STT providers.
    Each provider transcribes audio bytes to text.
    """

    @abstractmethod
    def transcribe(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes (e.g. OGG from Telegram voice message)
            mime_type: MIME type of the audio data

        Returns:
            Transcribed text, or empty string if transcription failed
        """
        pass
