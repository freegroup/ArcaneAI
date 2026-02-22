"""
LiteLLM Proxy Provider implementation.
Uses the OpenAI-compatible API format to communicate with LiteLLM Proxy.
"""
from typing import List, Optional
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction


class LiteLLMProvider(BaseLLMProvider):
    """
    LiteLLM Proxy provider.
    Supports any model that LiteLLM Proxy can route to (OpenAI, Anthropic, Azure, Bedrock, etc.)
    Uses OpenAI-compatible API format.
    """

    DEFAULT_BASE_URL = "http://localhost:4000/v1"

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        base_url: Optional[str] = None
    ):
        """
        Initialize LiteLLM provider.
        
        Args:
            api_key: API key for LiteLLM Proxy authentication
            model: Model name to use (as configured in LiteLLM Proxy)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            base_url: LiteLLM Proxy URL (default: http://localhost:4000/v1)
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, model, temperature, max_tokens)
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def call_chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None
    ) -> LLMResponse:
        """
        Send messages to LiteLLM Proxy and get a response.
        
        Args:
            messages: List of LLMMessage objects
            functions: Optional list of functions (ignored - uses JSON-based function calling)
            
        Returns:
            LLMResponse object
            
        Raises:
            Exception: If the API call fails
        """
        # Convert LLMMessage objects to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content or ""
            
            # Extract usage information
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            raise Exception(f"LiteLLM Proxy API error: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate LiteLLM configuration."""
        if not self.api_key:
            raise ValueError("LiteLLM API key is required")
        
        if not self.base_url:
            raise ValueError("LiteLLM base_url is required")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")