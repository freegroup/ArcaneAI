"""
Base for local models served by Ollama through its native API.
The native client (unlike /v1) honours think=False and num_ctx.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

import ollama as ollama_client

from .base_provider import BaseLLMProvider, LLMFunction, LLMMessage, LLMResponse


class OllamaNativeProvider(BaseLLMProvider):
    """
    Native tool calling via Ollama. Subclasses (GemmaProvider, QwenProvider)
    add model-specific cleanup in _parse().
    """

    DEFAULT_BASE_URL = 'http://localhost:11434'
    DEFAULT_CONTEXT_LENGTH = 8192

    def __init__(self, model: str, temperature: float = 0.5, max_tokens: int = 4000,
                 api_key: Optional[str] = None, base_url: Optional[str] = None,
                 context_length: Optional[int] = None) -> None:
        super().__init__(model, temperature, max_tokens, api_key, base_url or self.DEFAULT_BASE_URL)
        # Ollama's native API lives at the root, not at /v1.
        self.client = ollama_client.Client(host=self.base_url.replace('/v1', ''))
        # Ollama silently drops the start of a prompt that exceeds num_ctx.
        self.context_length: int = context_length or self.DEFAULT_CONTEXT_LENGTH

    def call_chat(self, messages: List[LLMMessage], functions: Optional[List[LLMFunction]] = None,
                  max_tokens: Optional[int] = None) -> LLMResponse:
        kwargs: Dict[str, Any] = {
            'model': self.model,
            'messages': self._format_messages(messages),
            'think': False,
            'options': {
                'temperature': self.temperature,
                'num_predict': max_tokens or self.max_tokens,
                'num_ctx': self.context_length,
            },
        }
        if functions:
            kwargs['tools'] = [self._tool(f) for f in functions]

        try:
            response = self.client.chat(**kwargs)
        except Exception as e:
            raise Exception(f'{self.__class__.__name__}/Ollama API error: {e}')

        message = response.message
        called = message.tool_calls[0].function.name if message.tool_calls else None
        content, function_call = self._parse(message.content or '', called, functions or [])
        prompt_tokens = response.prompt_eval_count or 0
        completion_tokens = response.eval_count or 0
        return LLMResponse(
            content=content,
            model=self.model,
            function_call=function_call,
            usage={
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
            },
            finish_reason='tool_calls' if message.tool_calls else 'stop',
        )

    def _parse(self, content: str, called: Optional[str],
               functions: List[LLMFunction]) -> tuple[str, Optional[str]]:
        """The answer's text and the function called. Override for model quirks."""
        return content.strip(), called

    @staticmethod
    def _strip_tokens(text: str) -> str:
        """Remove leaked special tokens such as <|im_end|> or <channel|>."""
        return re.sub(r'<[|]?[\w"]+[|]>', '', text).strip()

    @staticmethod
    def _format_messages(messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """An earlier function call becomes assistant tool_call + tool result, then the text."""
        formatted: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.role == 'assistant' and msg.function_call:
                formatted.append({
                    'role': 'assistant',
                    'content': '',
                    'tool_calls': [{'function': {'name': msg.function_call, 'arguments': {}}}],
                })
                formatted.append({'role': 'tool', 'content': '{"status": "ok"}', 'tool_name': msg.function_call})
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
