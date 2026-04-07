"""
Gemma provider for local Gemma models via Ollama.
Uses Ollama's native OpenAI-compatible tool calling API.
"""
from typing import List, Optional, Dict, Any
import json
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction, LLMFunctionCall


class GemmaProvider(BaseLLMProvider):
    """
    Provider for Gemma models running via Ollama.
    Uses native function calling via the OpenAI tools API instead of JSON prompting.
    """

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000, base_url: Optional[str] = None):
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama"
        )

    def build_prompt(self, base_prompt: str, functions: List[LLMFunction], messages: List[LLMMessage]) -> List[LLMMessage]:
        """
        Build system prompt for Gemma. Functions are passed natively via tools API,
        so the prompt only needs character/behavior instructions.
        """
        system_prompt = f"""{base_prompt}

Antworte immer auf Deutsch, kurz und in deiner Rolle. Sprich den Spieler direkt an.
Wähle die passende Funktion basierend auf der Absicht des Spielers.
Nutze 'keine_aktion' nur wenn wirklich keine Funktion passt.
"""
        return [LLMMessage(role="system", content=system_prompt), *messages]

    def call_chat(self, messages: List[LLMMessage], functions: Optional[List[LLMFunction]] = None) -> LLMResponse:
        """
        Call Gemma via Ollama with native tool calling.
        """
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Build OpenAI-compatible tools schema
        tools = None
        if functions:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": f.name,
                        "description": f.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "response": {
                                    "type": "string",
                                    "description": "Deine narrative Antwort an den Spieler (kurz, in character)"
                                }
                            },
                            "required": ["response"]
                        }
                    }
                }
                for f in functions
            ]

        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "required"

            response = self.client.chat.completions.create(**kwargs)

            message = response.choices[0].message
            content = message.content or ""

            # Extract native tool call if present
            function_call = None
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                function_call = LLMFunctionCall(
                    name=tool_call.function.name,
                    arguments=arguments
                )

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
                function_call=function_call,
                usage=usage,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            raise Exception(f"Gemma/Ollama API error: {str(e)}")

    def parse_response(self, llm_response: str) -> LLMFunctionCall:
        """
        Fallback parser if native tool calling returns plain text.
        Tries standard JSON parsing.
        """
        return self._parse_function_call(llm_response)

    def _validate_config(self) -> None:
        if not self.model:
            raise ValueError("Model name is required for Gemma provider")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
