"""
Base Jukebox - abstract interface for sound playback.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session import GameSession


class BaseJukebox(ABC):
    """Abstract base class for sound/music playback systems."""

    @abstractmethod
    def play_sound(
        self,
        session: GameSession,
        file_name: str,
        volume: int = 100,
        loop: bool = True,
        duration: float = 0
    ) -> None:
        """
        Play a sound file.
        
        Args:
            session: Game session
            file_name: Name of the sound file to play
            volume: Volume level (0-100)
            loop: Whether to loop the sound
            duration: Duration to play (0 = full length)
        """
        pass

    @abstractmethod
    def stop_all(self, session: GameSession) -> None:
        """
        Stop all currently playing sounds.
        
        Args:
            session: Game session
        """
        pass

    @abstractmethod
    def stop_ambient(self, session: GameSession) -> None:
        """
        Stop only ambient (looping) sounds.
        
        Args:
            session: Game session
        """
        pass
