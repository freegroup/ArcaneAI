"""
LiteLLM Proxy provider. Routes to any model the proxy knows
(OpenAI, Anthropic, Azure, Bedrock, ...) via the OpenAI API format.
"""
from .openai_compatible_provider import OpenAICompatibleProvider


class LiteLLMProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "http://localhost:4000/v1"

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.api_key:
            raise ValueError("LiteLLM requires api_key in config")
