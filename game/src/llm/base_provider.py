"""
Abstract base class for LLM providers.
Defines the interface that all LLM providers must implement.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import re


@dataclass
class LLMFunction:
    """Represents a function/action that the LLM can call."""
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None  # JSON Schema for parameters


@dataclass
class LLMFunctionCall:
    """Represents a function call returned by the LLM."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMMessage:
    """Represents a message in the conversation history."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Represents a response from the LLM."""
    content: str
    model: str
    function_call: Optional[LLMFunctionCall] = None
    usage: Optional[Dict[str, int]] = None  # tokens used
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Each provider must implement the chat method.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.1, max_tokens: int = 2000) -> None:
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider
            model: Model name to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.api_key: str = api_key
        self.model: str = model
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens
        self.debug_mode: bool = False  # Will be set by LLMFactory
        self._validate_config()

    # ========== NEW 3-STEP API ==========
    # Providers can override these to customize behavior

    def build_prompt(
        self,
        base_prompt: str,
        functions: List[LLMFunction],
        messages: List[LLMMessage]
    ) -> List[LLMMessage]:
        """
        Build complete prompt with function calling instructions.
        Override this to customize prompt format for your provider.

        Args:
            base_prompt: Base system prompt (identity, behavior, current state)
            functions: Available functions the LLM can call
            messages: Conversation history (WITHOUT system message)

        Returns:
            Complete messages ready for API call (including system message)
        """
        # Default: Generic JSON-based function calling
        # Providers should override this for model-specific optimizations

        # Build function list
        functions_json: List[Dict[str, Any]] = [
            {
                "name": f.name,
                "description": f.description,
                "parameters": f.parameters or {}
            }
            for f in functions
        ]

        instructions: str = self._default_response_instructions()

        # Build complete system prompt
        system_prompt: str = f"""{base_prompt}

WICHTIG: Du kommunizierst mit einer Maschine. Antworte IMMER im JSON-Format!

VERFÜGBARE FUNKTIONEN:
{json.dumps(functions_json, ensure_ascii=False, indent=2)}

{instructions}
"""

        # Return messages with system prompt
        return [LLMMessage(role="system", content=system_prompt), *messages]

    def _default_response_instructions(self) -> str:
        """Default instructions for JSON response format."""
        return """ANTWORT-FORMAT (EXAKT SO):
{
  "response": "Deine Antwort an den Spieler (kurz, in character)",
  "function": "function_name"
}

BEISPIEL:
{
  "response": "Arrgh, ich gehe nach Norden zum Baum!",
  "function": "gehe_zum_baum"
}

Wenn keine Funktion passt:
{
  "response": "Ich verstehe nicht, was du willst.",
  "function": "keine_aktion"
}

WICHTIG:
- Antworte NUR mit validem JSON
- Keine Erklärungen außerhalb des JSON
- Keine Markdown-Formatierung
- NIEMALS den Function-Namen im "response"-Text verwenden!
- Der "response"-Text ist für den Spieler, der "function"-Name ist internes System-Metadata"""

    @abstractmethod
    def call_chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None
    ) -> LLMResponse:
        """
        Low-level API call to LLM.
        Must be implemented by each provider.

        Args:
            messages: Complete messages (including system prompt)
            functions: Optional list of functions for native function calling support.
                      Providers that support native function calling should use this.
                      Providers using JSON-based function calling can ignore this.

        Returns:
            Raw LLMResponse from API (potentially with function_call if native support)

        Raises:
            Exception: If the API call fails
        """
        pass

    def parse_response(self, llm_response: str) -> LLMFunctionCall:
        """
        Parse function call from LLM response.
        Override this to customize parsing for your provider.

        Args:
            llm_response: Raw text response from LLM

        Returns:
            LLMFunctionCall object

        Raises:
            ValueError: If parsing fails
        """
        return self._parse_function_call(llm_response)

    # ========== HIGH-LEVEL API ==========
    # This is what GameController calls

    def chat_with_functions(
        self,
        messages: List[LLMMessage],
        functions: List[LLMFunction],
        base_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Chat with function calling support.
        Orchestrates the 3-step process: build_prompt → call_chat → parse_response

        Args:
            messages: Conversation history
            functions: Available functions the LLM can call
            base_prompt: Base system prompt (if not in messages)

        Returns:
            LLMResponse with optional function_call
        """
        # Determine base prompt (parameter takes priority over history)
        effective_base_prompt: str
        if base_prompt is None:
            # No base_prompt provided, try to use system message from history
            if messages and messages[0].role == "system":
                effective_base_prompt = messages[0].content
                messages = messages[1:]  # Remove system message
            else:
                effective_base_prompt = ""
        else:
            effective_base_prompt = base_prompt
            # base_prompt provided - remove old system message if present
            if messages and messages[0].role == "system":
                messages = messages[1:]  # Remove old system message

        # STEP 1: Build prompt with functions
        complete_messages: List[LLMMessage] = self.build_prompt(effective_base_prompt, functions, messages)

        # DEBUG: Print LLM request if debug_mode is enabled
        if self.debug_mode:
            try:
                from debug_utils import print_llm_debug
                print_llm_debug(complete_messages, functions, title="LLM REQUEST")
            except ImportError:
                print("[DEBUG] Could not import debug_utils")

        # STEP 2: Call LLM API (pass functions for native function calling support)
        response: LLMResponse = self.call_chat(complete_messages, functions)

        # STEP 3: Parse response (only if function_call not already set by native function calling)
        if not response.function_call:
            try:
                function_call: LLMFunctionCall = self.parse_response(response.content)
                # Update response with parsed function call
                response.function_call = function_call
                # Set content to the narrative response
                response.content = function_call.arguments.get("response", response.content)
            except ValueError as e:
                # Parsing failed, return response as-is
                if self.debug_mode:
                    print(f"[DEBUG] Function parsing failed: {e}")
        else:
            # Native function calling was used - extract narrative response from arguments if present
            if response.function_call and "response" in response.function_call.arguments:
                response.content = response.function_call.arguments["response"]
            elif self.debug_mode:
                print(f"[DEBUG] Native function call present but no 'response' in arguments")
                print(f"  Arguments: {response.function_call.arguments if response.function_call else 'None'}")

        # DEBUG: Print LLM response if debug_mode is enabled
        if self.debug_mode:
            try:
                from debug_utils import print_llm_response
                function_name: Optional[str] = response.function_call.name if response.function_call else None
                print_llm_response(response.content, function_call=function_name)
            except ImportError:
                print("[DEBUG] Could not import debug_utils")

        return response

    def chat(self, messages: List[LLMMessage]) -> LLMResponse:
        """
        Backward compatibility wrapper for chat().
        Delegates to call_chat() without functions.
        """
        return self.call_chat(messages, functions=None)

    def _parse_function_call(self, llm_response: str) -> LLMFunctionCall:
        """
        Parse function call from LLM response.
        Default implementation expects JSON format.

        Args:
            llm_response: Raw response from LLM

        Returns:
            LLMFunctionCall object

        Raises:
            ValueError: If parsing fails
        """
        # Try to extract JSON from response
        json_text = self._extract_json(llm_response)

        try:
            data = json.loads(json_text)

            # Validate required fields
            if "function" not in data:
                raise ValueError("Missing 'function' field in JSON response")

            return LLMFunctionCall(
                name=data["function"],
                arguments={"response": data.get("response", "")}
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text (handles markdown code blocks and escaped braces)."""
        # Replace multiple braces with single braces (some models escape them)
        json_match: Optional[re.Match[str]]
        while '{{{' in text or '}}}' in text:
            text = text.replace('{{{', '{').replace('}}}', '}')
        text = text.replace('{{', '{').replace('}}', '}')

        # Try to extract from markdown code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Try to extract from code block without language
        json_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Try to find JSON directly (non-greedy to get first complete object)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if json_match:
            return json_match.group(0)

        raise ValueError("No JSON found in response")

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the provider configuration.
        Should raise ValueError if configuration is invalid.
        """
        pass
    
