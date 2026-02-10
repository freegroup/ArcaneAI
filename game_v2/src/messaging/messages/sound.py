"""
Sound Messages for ambient sounds and sound effects.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .base import Message


@dataclass
class AmbientSoundMessage(Message):
    """Message to start/stop ambient (looping) sound for a state."""
    sound_file: Optional[str] = None  # None = stop ambient
    volume: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": {
                "sound_file": self.sound_file,
                "volume": self.volume
            }
        }

    @property
    def type(self) -> str:
        return "ambient_sound"


@dataclass
class SoundEffectMessage(Message):
    """Message to play a one-shot sound effect for an action."""
    sound_file: str
    volume: int = 100
    duration: Optional[float] = None  # None or 0 = play full

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": {
                "sound_file": self.sound_file,
                "volume": self.volume,
                "duration": self.duration
            }
        }

    @property
    def type(self) -> str:
        return "sound_effect"
