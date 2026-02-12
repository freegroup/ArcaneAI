"""
WebSocket audio sink for streaming audio to browser.
"""
from .base_sink import BaseAudioSink


class WebSocketSink(BaseAudioSink):
    """
    Audio sink that streams audio chunks to browser via WebSocket.
    """

    def __init__(self):
        """Initialize WebSocket sink."""
        super().__init__()
        self.closed = False

    def write(self, session, chunk: bytes) -> None:
        """
        Write audio chunk to WebSocket.

        Args:
            session: Game session (contains message_queue with WebSocket)
            chunk: Audio data chunk
        """
        if not self.closed and getattr(session, 'message_queue', None) is not None:
            if hasattr(session.message_queue, 'send_bytes'):
                session.message_queue.send_bytes(chunk)

    def close(self, session) -> None:
        """
        Close WebSocket sink.

        Args:
            session: Game session
        """
        self.closed = True
