"""
Generic provider for any local model via Ollama's OpenAI-compatible
endpoint. The model must support tool calling.
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "http://localhost:11434/v1"
    SUPPORTS_TOOL_CHOICE = False  # Ollama ignores tool_choice
    # Thinking models would spend the token budget on reasoning first.
    EXTRA_PARAMS = {'reasoning_effort': 'none'}
