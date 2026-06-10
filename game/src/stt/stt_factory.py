"""
STT provider factory.
Creates STT providers based on configuration.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from .base_provider import BaseSTTProvider
from .console_provider import ConsoleSTTProvider


class STTFactory:
    """
    Factory for creating STT providers based on configuration.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"

        self.config_path: Path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"enabled": False, "provider": "console"}

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config: Dict[str, Any] = yaml.safe_load(f)
            return config.get('stt', {"enabled": False, "provider": "console"})

    def create_provider(self) -> BaseSTTProvider:
        """
        Create STT provider based on configuration.

        Returns:
            STT provider instance
        """
        if not self.config.get('enabled', False):
            return ConsoleSTTProvider()

        provider_name: str = self.config.get('provider', 'console').lower()

        if provider_name == 'console':
            return ConsoleSTTProvider()

        elif provider_name == 'whisper':
            from .whisper_provider import WhisperSTTProvider
            return WhisperSTTProvider(
                model=self.config.get('model', 'whisper'),
                language=self.config.get('language', 'de'),
                base_url=self.config.get('base_url', 'http://localhost:11434/v1'),
            )

        elif provider_name == 'faster-whisper':
            from .faster_whisper_provider import FasterWhisperSTTProvider
            return FasterWhisperSTTProvider(
                model=self.config.get('model', 'base'),
                language=self.config.get('language', 'de'),
                device=self.config.get('device', 'auto'),
                compute_type=self.config.get('compute_type', 'default'),
            )

        else:
            print(f"[WARNING] Unknown STT provider: {provider_name}, falling back to console")
            return ConsoleSTTProvider()
