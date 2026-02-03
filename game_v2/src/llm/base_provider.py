"""
Abstract base class for LLM providers.
Defines the interface that all LLM providers must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """Represents a message in the conversation history."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Represents a response from the LLM."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None  # tokens used
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Each provider must implement the chat method.
    """
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._validate_config()
    
    @abstractmethod
    def chat(self, messages: List[LLMMessage]) -> LLMResponse:
        """
        Send messages to the LLM and get a response.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            LLMResponse object containing the response
            
        Raises:
            Exception: If the API call fails
        """
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the provider configuration.
        Should raise ValueError if configuration is invalid.
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider (e.g., 'gemini', 'openai')."""
        pass
    
    def supports_streaming(self) -> bool:
        """
        Check if the provider supports streaming responses.
        Override in subclass if streaming is supported.
        """
        return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        Override in subclass to provide actual model list.
        """
        return [self.model]