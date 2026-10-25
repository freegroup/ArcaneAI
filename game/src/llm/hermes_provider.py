"""
Hermes provider for Nous Research Hermes 3 models via Ollama's
OpenAI-compatible endpoint (ChatML + native tool calling).
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class HermesProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "http://localhost:11434/v1"
    SUPPORTS_TOOL_CHOICE = False  # Ollama ignores tool_choice
    # Thinking models would spend the token budget on reasoning first.
    EXTRA_PARAMS = {'reasoning_effort': 'none'}
