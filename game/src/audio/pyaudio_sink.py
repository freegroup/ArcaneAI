"""
PyAudio sink for local audio playback.
"""
import pyaudio

from .base_sink import BaseAudioSink


class PyAudioSink(BaseAudioSink):
    """
    Audio sink that plays audio locally using PyAudio.
    Uses a singleton pattern for the PyAudio instance.
    """
    _pyaudio_instance = None

    @classmethod
    def get_instance(cls):
        """Ensures a single PyAudio instance is created and shared."""
        if cls._pyaudio_instance is None:
            cls._pyaudio_instance = pyaudio.PyAudio()
        return cls._pyaudio_instance

    def __init__(self, sample_rate: int = 24000):
        """
        Initialize PyAudio sink.

        Args:
            sample_rate: Audio sample rate in Hz (default: 24000)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.stream = self.get_instance().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True
        )

    def write(self, session, chunk: bytes) -> None:
        """
        Write audio chunk to PyAudio stream.

        Args:
            session: Game session
            chunk: Audio data chunk
        """
        if self.stream is not None:
            self.stream.write(chunk)

    def close(self, session) -> None:
        """
        Close PyAudio stream.

        Args:
            session: Game session
        """
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
