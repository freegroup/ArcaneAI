"""
DeepSeek provider using its OpenAI-compatible API.
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
