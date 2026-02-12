"""
Gemini LLM Provider implementation.
Uses OpenAI-compatible API endpoint provided by Google.
"""
from typing import List, Dict, Any, Optional
import json
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction, LLMFunctionCall


class GeminiProvider(BaseLLMProvider):
    """
    Gemini provider using Google's OpenAI-compatible API.
    Supports native function calling through OpenAI-compatible interface.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    USE_NATIVE_FUNCTION_CALLING = True  # Gemini supports native function calling via OpenAI API

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000):
        """Initialize Gemini provider."""
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key
        )
    def build_prompt(self, base_prompt: str, functions: List[LLMFunction], messages: List[LLMMessage]) -> List[LLMMessage]:
        """
        Build prompt for Gemini.
        Uses native function calling, so no need to inject function descriptions into prompt.
        """
        # Build system prompt WITHOUT function descriptions (native function calling handles this)
        system_prompt = f"""{base_prompt}

HINWEIS FÜR KONTEXT: Du kannst alle Informationen aus deinem Kontext (Raumbeschreibung, Schilder, Objekte, etc.) frei mit dem Spieler teilen, wenn er danach fragt. Nutze dafür 'keine_aktion' als Funktion und beantworte die Frage direkt."""

        return [LLMMessage(role="system", content=system_prompt), *messages]

    def call_chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None
    ) -> LLMResponse:
        """
        Send messages to Gemini and get a response with native function calling.
        
        Args:
            messages: List of LLMMessage objects
            functions: Optional list of functions for native function calling
            
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
        
        # Convert functions to OpenAI tools format for native function calling
        tools: Optional[List[Dict[str, Any]]] = None
        if functions:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": f.name,
                        "description": f.description,
                        "parameters": f.parameters or {"type": "object", "properties": {}}
                    }
                }
                for f in functions
            ]
        
        try:
            # Call API with or without tools
            api_params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content or ""
            
            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # Handle native function call if present
            function_call = None
            message = response.choices[0].message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_call = message.tool_calls[0]
                if tool_call.function:
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        
                        # Debug logging
                        if self.debug_mode:
                            print(f"[DEBUG] Native function call detected:")
                            print(f"  Function name: {tool_call.function.name}")
                            print(f"  Raw arguments: {tool_call.function.arguments}")
                            print(f"  Parsed arguments: {arguments}")
                        
                        function_call = LLMFunctionCall(
                            name=tool_call.function.name,
                            arguments=arguments
                        )
                        # If there's a function call but no content, use the function response
                        if not content and "response" in arguments:
                            content = arguments["response"]
                    except json.JSONDecodeError as e:
                        if self.debug_mode:
                            print(f"[DEBUG] Failed to parse function arguments: {e}")
                            print(f"  Raw arguments string: {tool_call.function.arguments}")
                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] Unexpected error processing function call: {e}")
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                function_call=function_call
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
