"""
Base for every provider that speaks the OpenAI chat-completions API
(OpenAI, Gemini, DeepSeek, LiteLLM, Ollama's /v1 endpoint, ...).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .base_provider import BaseLLMProvider, LLMFunction, LLMMessage, LLMResponse


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Native tool calling over the OpenAI API. Subclasses set DEFAULT_BASE_URL
    and, if needed, tighten _validate_config().
    """

    DEFAULT_BASE_URL: Optional[str] = None
    # Whether the server honours tool_choice="required" (force a tool call
    # when functions are offered). Ollama ignores it.
    SUPPORTS_TOOL_CHOICE: bool = True
    # Extra request parameters every call sends (e.g. to switch thinking off).
    EXTRA_PARAMS: Dict[str, Any] = {}

    def __init__(self, model: str, temperature: float = 0.1, max_tokens: int = 2000,
                 api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        super().__init__(model, temperature, max_tokens, api_key, base_url or self.DEFAULT_BASE_URL)
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key or 'none')

    def call_chat(self, messages: List[LLMMessage], functions: Optional[List[LLMFunction]] = None,
                  max_tokens: Optional[int] = None) -> LLMResponse:
        params: Dict[str, Any] = {
            'model': self.model,
            'messages': self._format_messages(messages),
            'temperature': self.temperature,
            'max_tokens': max_tokens or self.max_tokens,
            **self.EXTRA_PARAMS,
        }
        if functions:
            params['tools'] = [self._tool(f) for f in functions]
            if self.SUPPORTS_TOOL_CHOICE:
                params['tool_choice'] = 'required'

        try:
            response = self.client.chat.completions.create(**params)
        except Exception as e:
            raise Exception(f'{self.__class__.__name__} API error: {e}')

        choice = response.choices[0]
        message = choice.message
        function_call = message.tool_calls[0].function.name if message.tool_calls else None
        usage = None
        if response.usage:
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }
        return LLMResponse(
            content=(message.content or '').strip(),
            model=response.model,
            function_call=function_call,
            usage=usage,
            finish_reason=choice.finish_reason,
        )

    @staticmethod
    def _format_messages(messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """An earlier function call becomes assistant tool_call + tool result, then the text."""
        formatted: List[Dict[str, Any]] = []
        for i, msg in enumerate(messages):
            if msg.role == 'assistant' and msg.function_call:
                call_id = f'call_{i}'
                formatted.append({
                    'role': 'assistant',
                    'content': None,
                    'tool_calls': [{
                        'id': call_id,
                        'type': 'function',
                        'function': {'name': msg.function_call, 'arguments': '{}'},
                    }],
                })
                formatted.append({'role': 'tool', 'tool_call_id': call_id, 'content': '{"status": "ok"}'})
            formatted.append({'role': msg.role, 'content': msg.content})
        return formatted

    @staticmethod
    def _tool(function: LLMFunction) -> Dict[str, Any]:
        return {
            'type': 'function',
            'function': {
                'name': function.name,
                'description': function.description,
                'parameters': {'type': 'object', 'properties': {}},
            },
        }
