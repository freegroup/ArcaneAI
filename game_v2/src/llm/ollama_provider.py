"""
Ollama LLM Provider implementation.
"""
from typing import List, Optional
import json
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local models.
    Uses the OpenAI-compatible API provided by Ollama.
    Uses JSON-based function calling with model-specific optimizations.
    """

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000, base_url: Optional[str] = None):
        """
        Initialize Ollama provider.

        Args:
            api_key: Not used by Ollama but required by base class interface (can be any string)
            model: Model name to use (e.g., "qwen2.5:7b", "llama3.2:8b")
            temperature: Sampling temperature (default 0.1 for less randomness)
            max_tokens: Maximum tokens in response
            base_url: Ollama API URL (defaults to http://localhost:11434/v1)
        """
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = base_url or self.DEFAULT_BASE_URL

        # Initialize OpenAI client pointing to Ollama
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama"  # key is required by client but ignored by Ollama
        )

    def build_prompt(self, base_prompt: str, functions: List[LLMFunction], messages: List[LLMMessage]) -> List[LLMMessage]:
        """
        Build prompt with Ollama model-specific optimizations.
        Qwen and Llama models get tailored instructions.
        """
        # Build function list
        functions_json = [
            {
                "name": f.name,
                "description": f.description,
                "parameters": f.parameters or {}
            }
            for f in functions
        ]

        # Get model-specific instructions based on model name
        model_lower = self.model.lower()

        if 'qwen' in model_lower:
            instructions = self._qwen_instructions()
        elif 'llama' in model_lower:
            instructions = self._llama_instructions()
        else:
            instructions = self._default_response_instructions()

        # Build complete system prompt
        system_prompt = f"""{base_prompt}

WICHTIG: Du kommunizierst mit einer Maschine. Antworte IMMER im JSON-Format!

VERFÜGBARE FUNKTIONEN:
{json.dumps(functions_json, ensure_ascii=False, indent=2)}

{instructions}

HINWEIS FÜR KONTEXT: Du kannst alle Informationen aus deinem Kontext (Raumbeschreibung, Schilder, Objekte, etc.) frei mit dem Spieler teilen, wenn er danach fragt. Nutze dafür 'keine_aktion' als Funktion und beantworte die Frage direkt im 'response' Feld.
"""

        return [LLMMessage(role="system", content=system_prompt), *messages]

    def _qwen_instructions(self) -> str:
        """Qwen-specific instructions - excellent at structured output."""
        return """ANTWORT-FORMAT (EXAKT SO):
{
  "response": "Deine Antwort an den Spieler (kurz, in character)",
  "function": "function_name"
}

WICHTIG:
- Antworte NUR mit validem JSON
- Keine zusätzlichen Erklärungen
- Keine Markdown Code-Blöcke (```json)
- Nutze einfache geschweifte Klammern { }, NICHT {{ }} oder {{{ }}}
- Beginne direkt mit {
- NIEMALS den Function-Namen im "response"-Text schreiben!
- Der "response" ist für den Spieler - der "function" Name ist nur Systeminfo"""

    def _llama_instructions(self) -> str:
        """Llama-specific instructions - needs more explicit examples."""
        return """Du MUSST im folgenden JSON-Format antworten:
{{
  "response": "Deine Antwort",
  "function": "function_name"
}}

BEISPIEL - Spieler sagt "geh nach Norden":
{{
  "response": "Ich gehe nach Norden!",
  "function": "gehe_nach_norden"
}}

Schreibe NUR das JSON, keine weiteren Texte!
NIEMALS den Function-Namen im "response"-Text verwenden - das ist nur Systeminfo!"""
    
    def call_chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None
    ) -> LLMResponse:
        """
        Send messages to Ollama and get a response.
        
        Args:
            messages: List of LLMMessage objects
            functions: Optional list of functions (ignored - uses JSON-based function calling)
            
        Returns:
            LLMResponse object
            
        Raises:
            Exception: If the API call fails
        """
        # Convert LLMMessage objects to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content or ""
            
            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate Ollama configuration."""
        # Ollama is flexible, mainly check if model is specified
        if not self.model:
            raise ValueError("Model name is required for Ollama")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
