"""
Gemini provider using Google's OpenAI-compatible API.
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class GeminiProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.api_key:
            raise ValueError("Gemini API key is required")
