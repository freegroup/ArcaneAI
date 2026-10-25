"""
Abstract base class for LLM providers.

A provider makes one stateless call: messages in (system prompt, history,
current input), optionally functions offered as native tools without
arguments, and out comes text and/or the name of the function called.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import time


@dataclass
class LLMFunction:
    """A function the LLM can call. Functions take no arguments."""
    name: str
    description: str


@dataclass
class LLMMessage:
    """A message of the conversation.

    An assistant message with `function_call` stands for a turn in which the
    model called that function and then answered with `content` — models
    copy the history, so earlier calls must be in it.
    """
    role: str  # "system", "user", "assistant"
    content: str
    function_call: Optional[str] = None


@dataclass
class LLMResponse:
    """The model's answer: its text and the function it called, if any."""
    content: str
    model: str
    function_call: Optional[str] = None
    usage: Optional[Dict[str, int]] = None  # tokens used
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Base class for all LLM providers.
    Subclasses implement call_chat(); callers use chat().
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model: str = model
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens
        self.api_key: Optional[str] = api_key
        self.base_url: Optional[str] = base_url
        self.debug_mode: bool = False  # Set by LLMFactory
        # Provider key from config.yaml (e.g. "gemma", "qwen"); also names the
        # folder of provider-specific prompts under game/prompts/. Set by LLMFactory.
        self.name: str = ''
        self._validate_config()

    def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        max_tokens: Optional[int] = None,
        label: str = 'LLM',
    ) -> LLMResponse:
        """
        One call to the model. Logs exactly what the model gets and answers
        when debug mode is on, plus a one-line summary always.
        """
        if self.debug_mode:
            from debug_utils import print_llm_debug
            print_llm_debug(messages, functions or [], title=f'{label} · {self.name or self.__class__.__name__} · {self.model}')

        started = time.monotonic()
        response = self.call_chat(messages, functions, max_tokens)
        elapsed = time.monotonic() - started

        if self.debug_mode:
            from debug_utils import print_llm_response
            print_llm_response(response.content, function_call=response.function_call)

        print(f'[LLM] {label} · {self.model} · {elapsed:.2f}s · '
              f'{len(response.content or "")} chars · fn: {response.function_call or "-"}')
        return response

    @abstractmethod
    def call_chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Low-level API call. Offers functions as native tools (no arguments)
        and reports the first function called. max_tokens overrides the
        configured limit for this call.
        """

    def _validate_config(self) -> None:
        """Raise ValueError if the configuration is invalid."""
        if not self.model:
            raise ValueError(f'Model name is required for {self.__class__.__name__}')
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        if self.max_tokens <= 0:
            raise ValueError('max_tokens must be positive')
