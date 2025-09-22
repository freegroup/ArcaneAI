import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Union, List, Annotated
import json
import re


# --- Pydantic-Modelle definieren den Vertrag ---


def extract_json_from_text(text: str) -> str:
    """Extrahiert JSON aus Text, auch wenn es in Code-Blöcken oder normalem Text versteckt ist."""
    text = text.strip()
    
    # Entferne Code-Block Marker
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    
    text = text.strip()
    
    # Suche nach JSON-Objekten mit regex
    json_pattern = r'\{.*?\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        # Nimm das erste vollständige JSON-Objekt
        return matches[0]
    
    return text

# --- Die vollständige, korrigierte LLM-Client-Klasse ---
class InstructorLLM:
    def __init__(self):
        self.model_name = "DeepSeek-Coder-V2-Lite-Instruct-Q8_0"
        self.history = []
        self.client = instructor.patch(
            OpenAI(base_url="http://localhost:1337/v1", api_key="any"),
            mode=instructor.Mode.TOOLS,
        )

    def reset(self, session):
        self.history = []
        initial_prompt = session.state_engine.get_action_system_prompt(session.state_engine.get_action_id("start"))
        if initial_prompt:
             self.history.append({"role": "assistant", "content": initial_prompt})

    def system(self, system_instruction: str):
        """Fügt eine temporäre System-Nachricht für den NÄCHSTEN Aufruf hinzu."""
        if system_instruction:
            self.history.append({"role": "system", "content": system_instruction})

    def chat(self, session, user_input: str) -> dict:
        self.history.append({"role": "user", "content": user_input})

        system_prompt = session.state_engine.get_global_system_prompt()
        
        # Sammle alle temporären und permanenten Nachrichten
        temp_system_messages = [msg for msg in self.history if msg["role"] == "system"]
        user_assistant_history = [msg for msg in self.history if msg["role"] in ["user", "assistant"]]
        messages = [{"role": "system", "content": system_prompt}] + temp_system_messages + user_assistant_history

        possible_actions_ids = session.state_engine.get_possible_action_ids()
        valid_action_names = [session.state_engine.get_action_name(id) for id in possible_actions_ids]

        entscheidung = self._get_decision(messages, valid_action_names)
        
        # Entferne temporäre System-Nachrichten nach dem Aufruf, um die History sauber zu halten
        self.history = [msg for msg in self.history if msg["role"] != "system"]
        
        return self._process_entscheidung(session, entscheidung)

    def _get_decision(self, messages: List, valid_actions: List[str]) -> Entscheidung:
        """Private Methode, die den eigentlichen, robusten instructor-Aufruf macht."""
        if not valid_actions:
            valid_actions = ["keine_aktion_moeglich"] # Fallback, falls keine Aktionen verfügbar sind
            
        # Pydantic's korrekter Weg, um ein Feld in einem bestehenden Modell dynamisch zu ändern
        AktionDynamisch = type(
            "AktionDynamisch",
            (Aktion,),
            {"__annotations__": {"name": Literal[*valid_actions]}}
        )

        EntscheidungDynamisch = Annotated[
            Union[AktionDynamisch, Konversation, HilfeAnfordern],
            Field(discriminator="entscheidungstyp")
        ]
        try:
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_model=EntscheidungDynamisch,
                max_retries=2,
            )
        except Exception as e:
            print(f"!! Kritischer Fehler im LLM-Aufruf: {e}")
            return Konversation(entscheidungstyp="konversation", inhalt="Mein Verstand ist gerade Matsch.")

    def _process_entscheidung(self, session, entscheidung: Entscheidung) -> dict:
        """
        Übersetzt das Pydantic-Objekt in das erwartete Dictionary und aktualisiert die History.
        """
        assistant_message = ""
        action_name = None

        if isinstance(entscheidung, Aktion):
            action_name = entscheidung.name
            assistant_message = entscheidung.ausfuehrungstext
        elif isinstance(entscheidung, Konversation):
            assistant_message = entscheidung.inhalt
        elif isinstance(entscheidung, HilfeAnfordern):
            actions_with_desc = {
                session.state_engine.get_action_name(id): session.state_engine.get_action_description(id)
                for id in session.state_engine.get_possible_action_ids()
            }
            assistant_message = self._generate_hint(actions_with_desc)
        
        # Füge die finale Antwort des Assistenten zur internen History hinzu
        self.history.append({"role": "assistant", "content": assistant_message})
        
        # Gib das Dictionary im alten, kompatiblen Format zurück
        return {"text": assistant_message, "action": action_name}

    def _generate_hint(self, current_actions_with_desc: dict) -> str:
        """Private Methode zur Generierung von Hinweisen."""
        descriptions_text = ", ".join(current_actions_with_desc.values())
        hint_prompt = f"Du bist ein mürrischer Haudegen. Der Spieler hat um Hilfe gebeten. Schlage ihm 2-3 interessante Dinge vor, basierend auf: {descriptions_text}. Fass dich kurz und bleib im Charakter."
        
        # Nutze den Basis-OpenAI-Client für einfache Textgenerierung
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": hint_prompt}]
        )
        return response.choices[0].message.content