"""
Factory for creating LLM provider instances based on configuration.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .ollama_provider import OllamaProvider


class LLMFactory:
    """
    Factory class for creating LLM provider instances.
    Reads configuration from config.yaml and environment variables.
    """
    
    # Map provider names to their classes
    PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider
    }
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the factory with a config file.
        
        Args:
            config_path: Path to config.yaml. If None, looks for config.yaml in game_v2/
        """
        if config_path is None:
            # Default to dungeon/config.yaml (project root)
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        
        self.config_path: Path = Path(config_path)
        self.config: Dict = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config: Dict = yaml.safe_load(f)

        return config

    def create_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Name of the provider to create. If None, uses config default.

        Returns:
            Instance of the requested provider

        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        # Get LLM configuration scope
        llm_config: Dict = self.config.get('llm', {})

        # Use provided provider name or fall back to config
        provider: Optional[str] = provider_name or llm_config.get('provider')

        if not provider:
            raise ValueError("No provider specified in config or arguments")

        if provider not in self.PROVIDERS:
            available = ', '.join(self.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Available providers: {available}"
            )

        # Get model, temperature, max_tokens from LLM config
        model: Optional[str] = llm_config.get('model')
        temperature: float = llm_config.get('temperature', 0.1)
        max_tokens: int = llm_config.get('max_tokens', 2000)

        # Get debug flag from debug scope
        debug_mode: bool = self.config.get('debug', {}).get('llm', False)
        
        if not model:
            raise ValueError("No model specified in config")
        
        # Special handling for SAP AI Core
        if provider == "sap_aicore":
            client_id: Optional[str] = llm_config.get('client_id')
            client_secret: Optional[str] = llm_config.get('client_secret')
            base_url: Optional[str] = llm_config.get('base_url')
            auth_url: Optional[str] = llm_config.get('auth_url')
            resource_group: str = llm_config.get('resource_group', 'default')
            deployment_id: Optional[str] = llm_config.get('deployment_id')  # Optional

            if not all([client_id, client_secret, base_url, auth_url]):
                raise ValueError("SAP AI Core requires: client_id, client_secret, base_url, auth_url")
            
            return SAPAICoreProvider(
                client_id=client_id,
                client_secret=client_secret,
                base_url=base_url,
                auth_url=auth_url,
                resource_group=resource_group,
                model=model,
                deployment_id=deployment_id,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        # Special handling for Ollama
        if provider == "ollama":
            base_url: Optional[str] = llm_config.get('base_url')
            provider_instance: BaseLLMProvider = OllamaProvider(
                api_key="ollama",  # Dummy key
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url
            )
            provider_instance.debug_mode = debug_mode
            return provider_instance

        # Standard providers (OpenAI, Gemini, DeepSeek)
        api_key: Optional[str] = llm_config.get('api_key')

        if not api_key:
            raise ValueError("No API key found in config (api_key)")
        
        # Create and return provider instance
        provider_class: Type[BaseLLMProvider] = self.PROVIDERS[provider]
        provider_instance: BaseLLMProvider = provider_class(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        provider_instance.debug_mode = debug_mode
        return provider_instance
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.PROVIDERS.keys())
    
    def get_config(self) -> Dict:
        """Get the loaded configuration."""
        return self.config.copy()
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
