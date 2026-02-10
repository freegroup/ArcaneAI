"""
Voice (TTS) provider factory.
Creates TTS providers based on configuration.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from .base_provider import BaseTTSProvider
from .console_provider import ConsoleTTSProvider

if TYPE_CHECKING:
    from audio.base_sink import BaseAudioSink


class VoiceFactory:
    """
    Factory for creating TTS providers based on configuration.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize factory with configuration.

        Args:
            config_path: Path to config.yaml. If None, looks for config.yaml in game_v2/
        """
        if config_path is None:
            # Default to game_v2/config.yaml
            config_path = Path(__file__).parent.parent.parent / "config.yaml"

        self.config_path: Path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            # Return default config if file doesn't exist
            return {
                "provider": "console",
                "enabled": False
            }

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config: Dict[str, Any] = yaml.safe_load(f)
            return config.get('voice', {})

    def create_provider(self, audio_sink: Optional[BaseAudioSink]) -> BaseTTSProvider:
        """
        Create TTS provider based on configuration.

        Args:
            audio_sink: Audio sink for TTS output

        Returns:
            TTS provider instance
        """
        if not self.config.get('enabled', False):
            return ConsoleTTSProvider(audio_sink)

        provider_name: str = self.config.get('provider', 'console').lower()

        if provider_name == 'console':
            return ConsoleTTSProvider(audio_sink)

        elif provider_name == 'google':
            from .google_provider import GoogleTTSProvider
            api_key: Optional[str] = self.config.get('api_key')
            language_code: str = self.config.get('language_code', 'de-DE')
            voice_name: str = self.config.get('voice_name', 'de-DE-Journey-D')
            sample_rate: int = self.config.get('sample_rate', 24000)
            model_name: Optional[str] = self.config.get('model_name')
            voice_prompt: Optional[str] = self.config.get('voice_prompt')
            pitch: float = self.config.get('pitch', 0.0)
            speaking_rate: float = self.config.get('speaking_rate', 1.0)
            return GoogleTTSProvider(audio_sink, language_code, voice_name, sample_rate, api_key,
                                    model_name, voice_prompt, pitch, speaking_rate)

        elif provider_name == 'openai':
            from .openai_provider import OpenAITTSProvider
            api_key: Optional[str] = self.config.get('api_key')
            voice: str = self.config.get('voice', 'onyx')
            speed: float = self.config.get('speed', 1.2)
            model: str = self.config.get('model', 'tts-1')
            return OpenAITTSProvider(audio_sink, api_key, voice, speed, model)

        else:
            print(f"[WARNING] Unknown TTS provider: {provider_name}, falling back to console")
            return ConsoleTTSProvider(audio_sink)
