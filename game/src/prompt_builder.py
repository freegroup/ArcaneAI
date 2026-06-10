from __future__ import annotations
from typing import TYPE_CHECKING, List

from jinja2 import Template

from llm import LLMFunction

if TYPE_CHECKING:
    from state_engine import State, Action
    from inventory import Inventory


class PromptBuilder:
    """
    Builds LLM prompts from game state. Pure/stateless — no session reference needed.
    """

    def build_system_prompt(self, state: State, inventory: Inventory, game_data: dict) -> str:
        # Personality is a Jinja2 template — same engine as room descriptions.
        # Game-designer authors {% if companion_mood == 'X' %}...{% endif %} blocks
        # (or any inventory-driven conditionals) directly in the personality text.
        identity: str = game_data.get('personality', '')
        if identity:
            try:
                identity = Template(identity).render(inventory.to_dict())
            except Exception as e:
                print(f"[WARNING] Failed to render personality template: {e}")
                # Fall through with raw identity text — better than empty prompt.

        behaviour: str = game_data.get('behaviour', '')

        prompt = ''
        if identity:
            prompt += identity + '\n\n'
        if behaviour:
            prompt += behaviour + '\n\n'

        prompt += f'AKTUELLER RAUM:\n{state.get_description()}\n'
        return prompt

    def build_functions(self, actions: List[Action]) -> List[LLMFunction]:
        functions: List[LLMFunction] = []

        for action in actions:
            description = action.description
            if action.after_fire:
                description += f'. Falls du diese Aktion auswählst, dann bitte dies in deiner Antwort berücksichtigen: {action.after_fire}'

            functions.append(LLMFunction(
                name=action.name,
                description=description,
                parameters={
                    'type': 'object',
                    'properties': {
                        'response': {
                            'type': 'string',
                            'description': 'Deine narrative Antwort an den Spieler (kurz, in character)'
                        }
                    },
                    'required': ['response']
                }
            ))

        functions.append(LLMFunction(
            name='keine_aktion',
            description='Keine der Aktionen passt zur Eingabe des Spielers',
            parameters={
                'type': 'object',
                'properties': {
                    'response': {
                        'type': 'string',
                        'description': 'Erkläre dem Spieler, warum du seine Eingabe nicht verstehst'
                    }
                },
                'required': ['response']
            }
        ))

        return functions
