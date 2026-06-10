"""
Null jukebox — no-op sound playback for runners without audio (e.g. Telegram).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseJukebox

if TYPE_CHECKING:
    from session import GameSession


class NullJukebox(BaseJukebox):
    def play_sound(self, session, file_name, volume=100, loop=True, duration=0) -> None:
        pass

    def stop_all(self, session) -> None:
        pass

    def stop_ambient(self, session) -> None:
        pass
