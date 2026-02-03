"""
OpenAI LLM Provider implementation.
"""
from typing import List
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider for GPT models.
    """
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000):
        """Initialize OpenAI provider."""
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key
        )
    
    def chat(self, messages: List[LLMMessage]) -> LLMResponse:
        """
        Send messages to OpenAI and get a response.
        
        Args:
            messages: List of LLMMessage objects
            
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
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        if not self.api_key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
    
