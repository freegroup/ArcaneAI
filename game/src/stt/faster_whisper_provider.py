"""
Faster-Whisper STT provider.
Uses faster-whisper (CTranslate2) for portable, efficient transcription.
Works on CPU and CUDA — no PyTorch, no platform-specific dependencies.
"""
import tempfile
import os
from typing import Optional
from .base_provider import BaseSTTProvider


_MIME_TO_EXT = {
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".mp4",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
}


class FasterWhisperSTTProvider(BaseSTTProvider):
    """
    STT provider using faster-whisper (CTranslate2).
    Model is loaded once on first use and kept in memory.

    Supported models: tiny, base, small, medium, large-v2, large-v3
    Device: "cpu" (portable), "cuda" (GPU VMs), "auto"
    """

    def __init__(
        self,
        model: str = "base",
        language: Optional[str] = "de",
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        """
        Args:
            model: Whisper model size ("tiny", "base", "small", "medium", "large-v3")
            language: Language hint (ISO 639-1). None = auto-detect.
            device: "cpu", "cuda", or "auto"
            compute_type: "default", "int8" (faster on CPU), "float16" (faster on GPU)
        """
        self.model_name = model
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self._model = None  # lazy load

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise ImportError(
                    "faster-whisper is not installed. Run: pip install faster-whisper"
                )
            print(f"[STT] Loading faster-whisper model '{self.model_name}' on {self.device}...")
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            print(f"[STT] Model loaded.")
        return self._model

    def transcribe(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        ext = _MIME_TO_EXT.get(mime_type, ".ogg")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            model = self._get_model()
            segments, _ = model.transcribe(
                tmp_path,
                language=self.language,
                beam_size=5,
            )
            text = " ".join(segment.text for segment in segments).strip()
            return text
        except Exception as e:
            print(f"[STT] faster-whisper transcription failed: {e}")
            return ""
        finally:
            os.unlink(tmp_path)
