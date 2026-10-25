"""
Factory for creating LLM provider instances based on configuration.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .ollama_provider import OllamaProvider
from .ollama_native_provider import OllamaNativeProvider
from .gemma_provider import GemmaProvider
from .qwen_provider import QwenProvider
from .hermes_provider import HermesProvider
from .litellm_provider import LiteLLMProvider


class LLMFactory:
    """
    Creates LLM providers from config.yaml.

    `llms` defines any number of models, each under a name of its own.
    `llm` says which one does what: `llm.stage1`, `llm.stage2` and `llm.mood`
    name the model of each pipeline stage; a stage without an entry (and
    any caller that names no stage) uses `llm.default`.
    """

    PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider,
        "gemma": GemmaProvider,
        "qwen": QwenProvider,
        "hermes": HermesProvider,
        "litellm": LiteLLMProvider,
    }

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is None:
            # Default to dungeon/config.yaml (project root)
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        self.config_path: Path = Path(config_path)
        self.config: Dict = self._load_config()

    def _load_config(self) -> Dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def model_name(self, stage: Optional[str] = None) -> str:
        """The name (in `llms`) of the model that runs stage."""
        llm_config: Dict[str, Any] = self.config.get('llm', {})
        name = (llm_config.get(stage) if stage else None) or llm_config.get('default')
        if not name:
            raise ValueError(f"No model for '{stage or 'default'}': set llm.default in config.yaml")
        return name

    def model_config(self, stage: Optional[str] = None) -> Dict[str, Any]:
        """The settings of the model that runs stage."""
        name = self.model_name(stage)
        models: Dict[str, Any] = self.config.get('llms', {})
        if name not in models:
            raise ValueError(f"Unknown model '{name}' — defined in llms: {', '.join(models) or '(none)'}")
        return models[name]

    def create_provider(self, stage: Optional[str] = None) -> BaseLLMProvider:
        """
        Create the provider for stage (or the default one).

        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        cfg = self.model_config(stage)
        provider: Optional[str] = cfg.get('provider')

        if not provider:
            raise ValueError(f"No provider for model '{self.model_name(stage)}'")
        if provider not in self.PROVIDERS:
            available = ', '.join(self.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider: {provider}. Available providers: {available}")

        provider_class = self.PROVIDERS[provider]
        kwargs: Dict[str, Any] = {
            'model': cfg.get('model'),
            'temperature': cfg.get('temperature', 0.1),
            'max_tokens': cfg.get('max_tokens', 2000),
            'api_key': cfg.get('api_key'),
            'base_url': cfg.get('base_url'),
        }
        if issubclass(provider_class, OllamaNativeProvider):
            kwargs['context_length'] = cfg.get('context_length')

        instance = provider_class(**kwargs)
        instance.name = provider
        instance.debug_mode = self.config.get('debug', {}).get('llm', False)
        return instance

    def get_available_providers(self) -> List[str]:
        return list(self.PROVIDERS.keys())

    def get_config(self) -> Dict:
        return self.config.copy()

    def reload_config(self) -> None:
        self.config = self._load_config()
