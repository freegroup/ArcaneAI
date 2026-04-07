"""
Ollama LLM Provider implementation.
"""
from typing import List, Optional
import json
from openai import OpenAI
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse, LLMFunction, LLMFunctionCall


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local models.
    Uses the OpenAI-compatible API provided by Ollama.
    Uses JSON-based function calling with model-specific optimizations.
    """

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000, base_url: Optional[str] = None):
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama"
        )

    def build_prompt(self, base_prompt: str, functions: List[LLMFunction], messages: List[LLMMessage]) -> List[LLMMessage]:
        """Build prompt with model-specific instructions."""
        model_lower = self.model.lower()

        # For hermes: strip parameters to reduce noise — response is top-level, not a parameter
        if 'hermes' in model_lower:
            functions_json = [
                {"name": f.name, "description": f.description}
                for f in functions
            ]
        else:
            functions_json = [
                {
                    "name": f.name,
                    "description": f.description,
                    "parameters": f.parameters or {}
                }
                for f in functions
            ]

        if 'qwen' in model_lower:
            instructions = self._qwen_instructions()
        elif 'llama' in model_lower:
            instructions = self._llama_instructions()
        elif 'hermes' in model_lower:
            instructions = self._hermes_instructions()
        else:
            instructions = self._default_response_instructions()

        system_prompt = f"""{base_prompt}

WICHTIG: Du kommunizierst mit einer Maschine. Antworte IMMER im JSON-Format!

VERFÜGBARE FUNKTIONEN:
{json.dumps(functions_json, ensure_ascii=False, indent=2)}

{instructions}

HINWEIS FÜR KONTEXT: Du kannst alle Informationen aus deinem Kontext (Raumbeschreibung, Schilder, Objekte, etc.) frei mit dem Spieler teilen, wenn er danach fragt. Nutze dafür 'keine_aktion' als Funktion und beantworte die Frage direkt im 'response' Feld.
"""
        return [LLMMessage(role="system", content=system_prompt), *messages]

    def _qwen_instructions(self) -> str:
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
        return """Du MUSST im folgenden JSON-Format antworten:
{
  "response": "Deine Antwort",
  "function": "function_name"
}

BEISPIEL - Spieler sagt "geh nach Norden":
{
  "response": "Ich gehe nach Norden!",
  "function": "gehe_nach_norden"
}

Schreibe NUR das JSON, keine weiteren Texte!
NIEMALS den Function-Namen im "response"-Text verwenden - das ist nur Systeminfo!"""

    def _hermes_instructions(self) -> str:
        return """ANTWORT-FORMAT (EXAKT SO):
{
  "response": "Deine Antwort an den Spieler (kurz, in character)",
  "name": "function_name"
}

BEISPIEL - Spieler sagt "untersuche das fenster":
{
  "response": "Du nähert dich dem Fenster und untersuchst es genau...",
  "name": "untersuche_das_fenster"
}

BEISPIEL - Spieler sagt "geh nach Norden":
{
  "response": "Ich schreite nach Norden!",
  "name": "gehe_nach_norden"
}

MATCHING-REGEL: Der Funktionsname entspricht direkt der Spieleraktion.
Wenn der Spieler "untersuche X" sagt → suche eine Funktion mit "untersuche_X" im Namen.
Wenn der Spieler "öffne X" sagt → suche eine Funktion mit "oeffne_X" im Namen.
Wenn der Spieler "gehe nach Y" sagt → suche eine Funktion mit "gehe_nach_Y" im Namen.
Nutze "keine_aktion" NUR wenn wirklich keine Funktion zur Absicht passt.

WICHTIG:
- Antworte NUR mit validem JSON, kein Text davor oder danach
- NIEMALS den Funktionsnamen im "response"-Text schreiben!
- KEINE Aktionsbeschreibungen in Sternchen (*geht los*)
- Sprich den Spieler direkt an, bleibe in deiner Rolle"""

    def parse_response(self, llm_response: str) -> LLMFunctionCall:
        """Override to handle hermes 'name' key instead of 'function'."""
        if 'hermes' in self.model.lower():
            return self._parse_hermes_response(llm_response)
        return self._parse_function_call(llm_response)

    def _parse_hermes_response(self, llm_response: str) -> LLMFunctionCall:
        """Parse hermes response — uses 'name' key instead of 'function'."""
        try:
            json_text = self._extract_json(llm_response)
            data = json.loads(json_text)
            if "name" in data:
                return LLMFunctionCall(
                    name=data["name"],
                    arguments={"response": data.get("response", "")}
                )
        except (json.JSONDecodeError, ValueError):
            pass
        return LLMFunctionCall(
            name="keine_aktion",
            arguments={"response": llm_response.strip()}
        )

    def call_chat(self, messages: List[LLMMessage], functions: Optional[List[LLMFunction]] = None) -> LLMResponse:
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
        if not self.model:
            raise ValueError("Model name is required for Ollama")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
