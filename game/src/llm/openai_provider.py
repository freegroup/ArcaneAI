"""
OpenAI provider for GPT models.
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
