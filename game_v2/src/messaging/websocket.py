"""
WebSocket message queue implementation.
"""
from typing import Dict, Any
from .base import MessageQueue


class WebSocketMessageQueue(MessageQueue):
    """
    Message queue for WebSocket connections.
    Sends messages immediately using background task.
    """
    
    def __init__(self, websocket, loop=None):
        """
        Initialize with WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            loop: Event loop (optional, will get current loop if not provided)
        """
        self.websocket = websocket
        self.loop = loop
    
    def send(self, message, data: Dict[str, Any] = None):
        """
        Send message over WebSocket immediately via background task.
        
        Args:
            message: Message object or legacy string type
            data: Message data (only used with legacy string type)
        """
        import asyncio
        
        # Handle Message objects
        if hasattr(message, 'to_dict'):
            message_dict = message.to_dict()
        else:
            # Legacy string type
            message_dict = {
                "type": message,
                "data": data or {}
            }
        
        # Get event loop
        try:
            loop = self.loop or asyncio.get_event_loop()
            # Schedule coroutine as task
            asyncio.ensure_future(self._send_async(message_dict), loop=loop)
        except Exception as e:
            print(f"[ERROR] Failed to schedule WebSocket send: {e}")
    
    async def _send_async(self, message: Dict[str, Any]):
        """
        Actually send message over WebSocket.
        
        Args:
            message: Message to send
        """
        try:
            await self.websocket.send_json(message)
            print(f"[WEBSOCKET] Sent: {message['type']}")
        except Exception as e:
            print(f"[ERROR] Failed to send WebSocket message: {e}")
    
    async def flush(self):
        """
        Flush any pending messages.
        For WebSocket, this is a no-op since messages are sent immediately.
        """
        pass