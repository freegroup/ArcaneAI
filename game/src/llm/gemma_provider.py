"""
Gemma provider for local Gemma models via Ollama.
"""
from __future__ import annotations
import re
from typing import List, Optional

from .base_provider import LLMFunction
from .ollama_native_provider import OllamaNativeProvider


class GemmaProvider(OllamaNativeProvider):
    """
    Gemma sometimes writes a function call as text instead of calling it:
    the function's name as the first line, or `name{...}`. Both count as
    the call.
    """

    def _parse(self, content: str, called: Optional[str],
               functions: List[LLMFunction]) -> tuple[str, Optional[str]]:
        content = self._strip_tokens(content)
        if called or not functions:
            return content, called

        names = {f.name for f in functions}
        first_line, _, rest = content.partition('\n')
        if first_line.strip() in names:
            return rest.strip(), first_line.strip()

        match = re.match(r'^(\w+)\s*\{.*\}\s*$', content, re.DOTALL)
        if match and match.group(1) in names:
            return '', match.group(1)

        return content, None
