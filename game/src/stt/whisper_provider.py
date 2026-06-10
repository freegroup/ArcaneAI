"""
Whisper STT provider via Ollama API.
Transcribes audio using a locally running Whisper model.
"""
import tempfile
import os
from typing import Optional
from openai import OpenAI
from .base_provider import BaseSTTProvider


# Map MIME types to file extensions
_MIME_TO_EXT = {
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".mp4",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
}


class WhisperSTTProvider(BaseSTTProvider):
    """
    STT provider using Whisper via Ollama's OpenAI-compatible API.
    Requires a Whisper model to be available in Ollama (e.g. whisper).
    """

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(
        self,
        model: str = "whisper",
        language: Optional[str] = "de",
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize Whisper STT provider.

        Args:
            model: Whisper model name in Ollama (e.g. "whisper", "whisper:large")
            language: Language hint for transcription (ISO 639-1, e.g. "de", "en")
            base_url: Ollama API base URL
        """
        self.model = model
        self.language = language
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama"
        )

    def transcribe(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Transcribe audio bytes to text using Whisper via Ollama.

        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of audio (used to determine file extension)

        Returns:
            Transcribed text, or empty string on failure
        """
        ext = _MIME_TO_EXT.get(mime_type, ".ogg")

        # Whisper API requires a file — write to a temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                }
                if self.language:
                    kwargs["language"] = self.language

                result = self.client.audio.transcriptions.create(**kwargs)
                return result.text.strip()
        except Exception as e:
            print(f"[STT] Whisper transcription failed: {e}")
            return ""
        finally:
            os.unlink(tmp_path)
