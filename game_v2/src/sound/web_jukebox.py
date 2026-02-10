"""
Web Jukebox - sends sound commands to browser via WebSocket message queue.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from .base import BaseJukebox
from messaging.messages.sound import SoundEffectMessage, AmbientSoundMessage

if TYPE_CHECKING:
    from session import GameSession


class WebJukebox(BaseJukebox):
    """Jukebox implementation that sends sound commands to browser via WebSocket."""

    def play_sound(
        self,
        session: GameSession,
        file_name: str,
        volume: int = 100,
        loop: bool = True,
        duration: float = 0
    ) -> None:
        """Send play_sound command to browser via WebSocket."""
        if not file_name or not file_name.strip():
            return

        if not session.message_queue:
            print(f"[WEB_SOUND] No message queue, cannot send sound: '{file_name}'")
            return

        # Log sound playback
        sound_type: str = "ambient" if loop else "effect"
        print(f"[WEB_SOUND] Sending {sound_type}: '{file_name}'")
        print(f"[WEB_SOUND]   → volume: {volume}%, loop: {loop}, duration: {duration}s")

        if loop:
            session.message_queue.send(AmbientSoundMessage(
                sound_file=file_name,
                volume=volume
            ))
        else:
            session.message_queue.send(SoundEffectMessage(
                sound_file=file_name,
                volume=volume,
                duration=duration
            ))

    def stop_all(self, session: GameSession) -> None:
        """Send stop_all command to browser."""
        if not session.message_queue:
            return
        print("[WEB_SOUND] Stopping all sounds")
        session.message_queue.send(AmbientSoundMessage(sound_file=None, volume=0))

    def stop_ambient(self, session: GameSession) -> None:
        """Send stop_ambient command to browser (stop looping sounds only)."""
        if not session.message_queue:
            return
        print("[WEB_SOUND] Stopping ambient sounds")
        session.message_queue.send(AmbientSoundMessage(sound_file=None, volume=0))