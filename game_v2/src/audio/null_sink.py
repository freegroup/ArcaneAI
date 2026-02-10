"""
Null audio sink - discards all audio (silent mode).
"""
from .base_sink import BaseAudioSink


class NullSink(BaseAudioSink):
    """
    Null sink that discards all audio.
    Useful for silent mode or testing.
    """

    def write(self, session, chunk: bytes) -> None:
        """
        Discard audio chunk (no-op).

        Args:
            session: Game session
            chunk: Audio data chunk (ignored)
        """
        pass

    def close(self, session) -> None:
        """
        Close null sink (no-op).

        Args:
            session: Game session
        """
        pass
