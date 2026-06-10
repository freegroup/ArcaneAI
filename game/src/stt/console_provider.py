"""
Console STT provider — no-op for testing without audio hardware.
Returns the audio data as a placeholder string.
"""
from .base_provider import BaseSTTProvider


class ConsoleSTTProvider(BaseSTTProvider):
    """
    No-op STT provider for console/testing.
    Prints a notice and returns an empty string.
    """

    def transcribe(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        print(f"[STT] Console provider — {len(audio_data)} bytes received, transcription not supported.")
        return ""
