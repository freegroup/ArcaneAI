"""
Telegram message queue — sends game messages via Telegram Bot API.
"""
from __future__ import annotations
import json
from typing import Any, Dict, Optional

from .base import MessageQueue


class TelegramMessageQueue(MessageQueue):
    """
    Buffers game messages during request processing.
    The Telegram runner reads them after each turn and sends via bot.
    """

    def __init__(self) -> None:
        self._buffer: list[Dict[str, Any]] = []

    def send(self, message, data: Optional[Dict[str, Any]] = None) -> None:
        if hasattr(message, 'to_dict'):
            msg_dict = message.to_dict()
            msg_type = msg_dict['type']
            data = msg_dict.get('data', {})
        else:
            msg_type = message
            data = data or {}

        self._buffer.append({"type": msg_type, "data": data})

    def flush(self) -> list[Dict[str, Any]]:
        """Return buffered messages and clear the buffer."""
        messages = self._buffer.copy()
        self._buffer.clear()
        return messages
