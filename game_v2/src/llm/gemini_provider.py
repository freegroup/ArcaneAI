"""
Gemini LLM Provider implementation.
Uses OpenAI-compatible API endpoint provided by Google.
"""
from typing import List
import json
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction, LLMFunctionCall


class GeminiProvider(BaseLLMProvider):
    """
    Gemini provider using Google's OpenAI-compatible API.
    Supports function calling through OpenAI-compatible interface.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000):
        """Initialize Gemini provider."""
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key
        )

    def build_prompt(self, base_prompt: str, functions: List[LLMFunction], messages: List[LLMMessage]) -> List[LLMMessage]:
        """
        Build prompt with Gemini-specific optimizations.
        Adds explicit instruction to share context information freely.
        """
        # Build function list
        functions_json = [
            {
                "name": f.name,
                "description": f.description,
                "parameters": f.parameters or {}
            }
            for f in functions
        ]

        instructions = self._default_response_instructions()

        # Build complete system prompt with Gemini-specific hint
        system_prompt = f"""{base_prompt}

WICHTIG: Du kommunizierst mit einer Maschine. Antworte IMMER im JSON-Format!

VERFÜGBARE FUNKTIONEN:
{json.dumps(functions_json, ensure_ascii=False, indent=2)}

{instructions}

HINWEIS FÜR KONTEXT: Du kannst alle Informationen aus deinem Kontext (Raumbeschreibung, Schilder, Objekte, etc.) frei mit dem Spieler teilen, wenn er danach fragt. Nutze dafür 'keine_aktion' als Funktion und beantworte die Frage direkt im 'response' Feld.
"""

        return [LLMMessage(role="system", content=system_prompt), *messages]

    def call_chat(self, messages: List[LLMMessage]) -> LLMResponse:
        """
        Send messages to Gemini and get a response.
        
        Args:
            messages: List of LLMMessage objects
            
        Returns:
            LLMResponse object
            
        Raises:
            Exception: If the API call fails
        """
        # Convert LLMMessage objects to OpenAI format
        # Filter out messages with empty content (Gemini doesn't accept them)
        formatted_messages = []
        for msg in messages:
            if msg.content and msg.content.strip():
                # Gemini via OpenAI API doesn't support system role well
                # Convert system messages to user messages
                role = "user" if msg.role == "system" else msg.role
                formatted_messages.append({"role": role, "content": msg.content})
        
        # Ensure we have at least one message
        if not formatted_messages:
            raise ValueError("No valid messages to send to Gemini")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content or ""
            
            # Extract usage information if available
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
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate Gemini configuration."""
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        