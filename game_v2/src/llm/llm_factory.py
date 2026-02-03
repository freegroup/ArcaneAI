"""
Factory for creating LLM provider instances based on configuration.
"""
import os
import yaml
from typing import Optional
from pathlib import Path
from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider


class LLMFactory:
    """
    Factory class for creating LLM provider instances.
    Reads configuration from config.yaml and environment variables.
    """
    
    # Map provider names to their classes
    PROVIDERS = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the factory with a config file.
        
        Args:
            config_path: Path to config.yaml. If None, looks for config.yaml in game_v2/
        """
        if config_path is None:
            # Default to game_v2/config.yaml
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
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
        # Use provided provider name or fall back to config
        provider = provider_name or self.config.get('provider')
        
        if not provider:
            raise ValueError("No provider specified in config or arguments")
        
        if provider not in self.PROVIDERS:
            available = ', '.join(self.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Available providers: {available}"
            )
        
        # Get API key - either directly from config or from environment variable
        api_key = self.config.get('api_key')
        if not api_key:
            # Try to get from environment variable
            api_key_env = self.config.get('api_key_env')
            if api_key_env:
                api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError("No API key found in config (api_key) or environment (api_key_env)")
        
        # Get model, temperature, and max_tokens from config
        model = self.config.get('model')
        temperature = self.config.get('temperature', 0.1)
        max_tokens = self.config.get('max_tokens', 2000)
        
        if not model:
            raise ValueError("No model specified in config")
        
        # Create and return provider instance
        provider_class = self.PROVIDERS[provider]
        return provider_class(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_providers(self) -> list:
        """Get list of available provider names."""
        return list(self.PROVIDERS.keys())
    
    def get_config(self) -> dict:
        """Get the loaded configuration."""
        return self.config.copy()
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()