"""
Text Improver Service with Jinja Template Preservation
Improves text quality while preserving Jinja2 template syntax
"""
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add game/src to path to import LLM modules
game_src_path = Path(__file__).parent.parent.parent.parent / "game" / "src"
sys.path.insert(0, str(game_src_path))

from llm.llm_factory import LLMFactory
from llm.base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class TextImprover:
    """
    Service for improving text while preserving Jinja2 template syntax.
    Uses configured LLM to enhance text quality based on user instructions.
    """
    
    # Strict system prompt to ensure Jinja preservation
    SYSTEM_PROMPT = """Du bist ein präziser Text-Verbesserer. Deine einzige Aufgabe ist es, Texte zu verbessern, zu optimieren oder zu übersetzen.

KRITISCHE REGEL - JINJA TAGS DÜRFEN NIEMALS VERÄNDERT WERDEN:
- Jinja-Tags wie {{ variable }}, {% if %}, {% for %}, etc. MÜSSEN exakt erhalten bleiben
- Du darfst KEINE Jinja-Syntax ändern, entfernen oder neu formatieren
- Jinja-Tags sind HEILIG und absolut unantastbar

DEINE AUFGABE:
- Verbessere NUR den reinen Text zwischen oder um Jinja-Tags herum
- Optimiere Grammatik, Rechtschreibung, Satzbau
- Passe den Ton/Stil an die Anforderungen des Nutzers an
- Übersetze Text falls gewünscht, aber BEHALTE Jinja-Tags im Original

ANTWORT-FORMAT:
Du gibst NUR den verbesserten Text zurück - keine Erklärungen, keine Kommentare wie "Ich habe verbessert...", keine Markdown-Formatierung.
Nur der reine, verbesserte Text mit exakt erhaltenen Jinja-Tags.

BEISPIEL:
Input: "Du gehst in {{ ort }} und siehst einen mann."
Verbesserung (bessere Grammatik): "Du gehst in {{ ort }} und siehst einen Mann."

Input: "{% if health > 0 %}Du lebst noch{% endif %}"
KEINE ÄNDERUNG ERLAUBT an Jinja-Tags! Nur Text zwischen Tags kann verbessert werden.

WICHTIG: Sei extrem vorsichtig! Ein einziger Fehler bei Jinja-Tags zerstört die gesamte Template-Funktionalität."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the TextImprover with LLM configuration.
        
        Args:
            config_path: Path to config.yaml. If None, uses default location.
        """
        if config_path is None:
            # Default to dungeon/config.yaml (project root)
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        
        # Initialize LLM Factory
        self.llm_factory = LLMFactory(config_path)
        self.provider: Optional[BaseLLMProvider] = None
    
    def _get_provider(self) -> BaseLLMProvider:
        """Get or create LLM provider instance."""
        if self.provider is None:
            self.provider = self.llm_factory.create_provider()
        return self.provider
    
    def improve_text(
        self,
        text: str,
        user_instruction: str,
        include_comment: bool = False
    ) -> Dict[str, Any]:
        """
        Improve text based on user instruction while preserving Jinja tags.
        
        Args:
            text: Original text with possible Jinja template syntax
            user_instruction: User's instruction (e.g., "Verbessere die Grammatik", "Übersetze ins Englische")
            include_comment: If True, generate an explanation of changes
        
        Returns:
            Dictionary with:
                - improved_text: The improved text with preserved Jinja tags
                - comment: Optional explanation of changes (if include_comment=True)
                - model: Model name used
        """
        provider = self._get_provider()
        
        # Build user message with clear instruction
        user_message = f"""Anforderung: {user_instruction}

Original-Text:
{text}

Verbessere den Text gemäß der Anforderung. BEHALTE ALLE Jinja-Tags exakt bei!"""
        
        # Create messages for LLM
        messages = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_message)
        ]
        
        # Call LLM (using call_chat directly, no function calling needed)
        response: LLMResponse = provider.call_chat(messages, functions=None)
        
        improved_text = response.content.strip()
        
        result = {
            "improved_text": improved_text,
            "model": response.model
        }
        
        # Generate comment/explanation if requested
        if include_comment:
            comment = self._generate_comment(
                original=text,
                improved=improved_text,
                instruction=user_instruction,
                provider=provider
            )
            result["comment"] = comment
        
        return result
    
    def _generate_comment(
        self,
        original: str,
        improved: str,
        instruction: str,
        provider: BaseLLMProvider
    ) -> str:
        """
        Generate a comment explaining the changes made.
        
        Args:
            original: Original text
            improved: Improved text
            instruction: User's instruction
            provider: LLM provider instance
        
        Returns:
            Explanation of changes
        """
        comment_prompt = f"""Du bist ein Erklärungs-Assistent. Erkläre kurz und präzise, welche Änderungen am Text vorgenommen wurden.

Anforderung war: {instruction}

Original:
{original}

Verbessert:
{improved}

Erkläre in 2-3 Sätzen die wichtigsten Änderungen. Sei konkret und hilfreich."""
        
        messages = [
            LLMMessage(role="system", content="Du bist ein hilfreicher Erklärungs-Assistent. Antworte kurz und präzise."),
            LLMMessage(role="user", content=comment_prompt)
        ]
        
        response: LLMResponse = provider.call_chat(messages, functions=None)
        return response.content.strip()