"""
Qwen provider for local Qwen 3.x models via Ollama (e.g. qwen3.6:35b-a3b).
Prompts of its own go to game/prompts/qwen/ (same file names as game/prompts/).
"""
from __future__ import annotations
import json
import re
from typing import List, Optional

from .base_provider import LLMFunction
from .ollama_native_provider import OllamaNativeProvider


class QwenProvider(OllamaNativeProvider):
    """
    Thinking is switched off (think=False), but Qwen may still leave a
    <think>…</think> block in the text, and now and then writes a function
    call as text in its Hermes format: <tool_call>{"name": …}</tool_call>.
    Both are handled here.
    """

    def _parse(self, content: str, called: Optional[str],
               functions: List[LLMFunction]) -> tuple[str, Optional[str]]:
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        if called or not functions:
            return self._strip_tokens(content), called

        match = re.search(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', content, re.DOTALL)
        if match:
            try:
                name = json.loads(match.group(1)).get('name')
            except json.JSONDecodeError:
                name = None
            if name in {f.name for f in functions}:
                return self._strip_tokens(content.replace(match.group(0), '')), name

        return self._strip_tokens(content), None
