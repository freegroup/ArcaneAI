"""
Local Jukebox - plays sounds locally via pygame mixer.
"""
from __future__ import annotations
import threading
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

import pygame
from pygame import mixer

from .base import BaseJukebox

if TYPE_CHECKING:
    from session import GameSession

# Initialize pygame mixer
mixer.init()

# Base directory for game (used for default soundfx path)
GAME_DIR: Path = Path(__file__).parent.parent.parent


class LocalJukebox(BaseJukebox):
    """Jukebox implementation that plays sounds locally via pygame mixer."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize LocalJukebox.
        
        Args:
            config: Configuration dictionary with sound.soundfx_dir setting (required)
        
        Raises:
            ValueError: If config is missing or soundfx_dir is not configured
        """
        if not config:
            raise ValueError("Configuration is required for LocalJukebox")
            
        self.playing_channels: Dict[Any, Dict[str, Any]] = {}
        
        # Load GameConfig to get soundfx directory
        from config_loader import GameConfig
        game_config = GameConfig()
        self.soundfx_dir: Path = game_config.soundfx_directory

    def play_sound(
        self,
        session: GameSession,
        file_name: str,
        volume: int = 100,
        loop: bool = True,
        duration: float = 0
    ) -> None:
        """Play a sound file locally via pygame."""
        if not file_name or not file_name.strip():
            return

        file_path: str = str(self.soundfx_dir / file_name)
        
        # Log sound playback
        sound_type: str = "ambient" if loop else "effect"
        print(f"[LOCAL_SOUND] Loading {sound_type}: '{file_name}'")
        print(f"[LOCAL_SOUND]   → volume: {volume}%, loop: {loop}, duration: {duration}s")

        try:
            sound: Any = mixer.Sound(file_path)
            channel: Optional[Any] = mixer.find_channel()
            if channel is None:
                return

            channel.set_volume(max(0, min(volume, 100)) / 100.0)
            loops: int = -1 if loop else 0
            channel.play(sound, loops=loops)
            self.playing_channels[channel] = {'loop': loop, 'timer': None}

            if duration > 0 and not loop:
                timer: threading.Timer = threading.Timer(duration, self._stop_channel, args=[channel])
                self.playing_channels[channel]['timer'] = timer
                timer.start()

        except Exception as e:
            print(f"[LOCAL_SOUND] ERROR: Unable to play '{file_path}': {e}")

    def _stop_channel(self, channel: Any) -> None:
        """Stop a channel and clean up."""
        if channel in self.playing_channels:
            channel.stop()
            del self.playing_channels[channel]

    def stop_all(self, session: GameSession) -> None:
        """Stop all currently playing sounds."""
        if self.playing_channels:
            print(f"[LOCAL_SOUND] Stopping all sounds ({len(self.playing_channels)} channels)")
        for channel, info in list(self.playing_channels.items()):
            if channel.get_busy():
                channel.stop()
            if info['timer'] is not None:
                info['timer'].cancel()
        self.playing_channels.clear()

    def stop_ambient(self, session: GameSession) -> None:
        """Stop only looping (ambient) sounds."""
        ambient_count: int = sum(1 for info in self.playing_channels.values() if info['loop'])
        if ambient_count > 0:
            print(f"[LOCAL_SOUND] Stopping ambient sounds ({ambient_count} channels)")
        for channel, info in list(self.playing_channels.items()):
            if info['loop'] and channel.get_busy():
                channel.stop()
                if info['timer'] is not None:
                    info['timer'].cancel()
                del self.playing_channels[channel]
