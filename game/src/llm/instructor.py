import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Union, List, Annotated
import json
import re
from logger_setup import logger
from utils.text import extract_json_text_from_raw_text

# --- Pydantic-Modelle definieren den Vertrag ---
class Aktion(BaseModel):
    decision_type:  Literal["action"] 
    name: str
    execution_text: str

def make_action_model(valid_actions: list[str]):
    class DynamicAktion(Aktion):
        decision_type:  Literal["action"] 
        name: str
        execution_text: str

        @classmethod
        def validate_action(cls, name: str):
            if name not in valid_actions:
                raise ValueError(f"Ungültige Aktion: {name}. Erlaubt: {valid_actions}")
            return name

        # Pydantic v2: Validator mit Decorator
        @classmethod
        def model_validate(cls, data):
            obj = super().model_validate(data)
            cls.validate_action(obj.name)
            return obj

    return DynamicAktion


class Konversation(BaseModel):
    decision_type: Literal["conversation"]
    content: str

class HilfeAnfordern(BaseModel):
    decision_type: Literal["help"]



class InstructorLLM:
    def __init__(self):
        self.model_name = "DeepSeek-Coder-V2-Lite-Instruct-Q8_0"
        self.history = []
        self.client = OpenAI(base_url="http://localhost:1337/v1", api_key="any")


    def reset(self, session):
        self.history = []


    def system(self, system_instruction: str):
        if system_instruction:
            self.history.append({"role": "system", "content": system_instruction})


    def chat(self, session, user_input: str) -> dict:
        if not user_input:
            return {"text": "No input provided.", "expressions": [], "action": None}
        self._trim_history()
        self._add_to_history("user", user_input)

        combined_history = [
            {"role": "system", "content": session.state_engine.get_global_system_prompt()},
            {"role": "system", "content": session.state_engine.get_state_system_prompt()},
            {"role": "system", "content": self._possible_actions_instruction(session)},
        ] + self.history
        for entry in combined_history:
            print(entry["role"])
            print(entry["content"])
            print("------------------------------------------------------------------------")
        print("=========================================================================")
        response =  self.client.chat.completions.create(
            model=self.model_name,
            messages=combined_history,
            temperature=0.1,
            max_tokens=2000)
        raw_content = response.choices[0].message.content
        self._add_to_history(role="assistant", message=raw_content)
        # Extrahiere JSON
        json_str = extract_json_text_from_raw_text(raw_content)
        #print(f"🔍 Extracted JSON: {json_str}")

        # Parse JSON
        try:
            json_data = json.loads(json_str)
    
            # Validiere mit Pydantic
            if json_data.get("decision_type") == "action":
                try:
                    possible_actions_ids = session.state_engine.get_possible_action_ids()
                    valid_action_names = [session.state_engine.get_action_name(id) for id in possible_actions_ids]
                    DynAction = make_action_model(valid_action_names)
                    action = DynAction(**json_data)
                    return {"text": action.execution_text, "action": action.name}
                except ValidationError as ve:
                    # LLM hat eine ungültige Aktion erfunden
                    #invalid_action = json_data.get("name", "unbekannt")
                    return {"text": "Nicht verstanden", "action": None}
            elif json_data.get("decision_type") == "conversation":
                return {"text": json_data["content"], "action": None}
            else:
                raise ValueError(f"Unbekannter decision_type: {json_data.get('decision_type')}")
        except Exception as e:
            print(e)
            return {"text": json_str, "action": None}

    def _add_to_history(self, role, message):
        if not message:
            logger.warning("No message provided.")
            return
        
        if self.history and self.history[-1]["role"] == role and self.history[-1]["content"] == message:
            logger.error("Duplicate message detected; not adding to history.")
            return
        
        self.history.append({"role": role, "content": message})


    def _possible_actions_instruction(self, session):
        action_str = chr(10).join( [
            f"- {session.state_engine.get_action_name(action)}: {session.state_engine.get_action_description(action)}"
            for action in session.state_engine.get_possible_action_ids()
        ])
        return f"""
Benutze diese bereitgestellen Funktionen oder Tools um dem Benutzer zu helfen: 
{action_str}
        
**Regeln für dein Verhalten**

WICHTIG: Du MUSST immer mit einem JSON-Objekt antworten! Kein normaler Text!

STRIKTE REGELN:
- Erfinde KEINE Geschichten, Missionen, Ziele oder Hintergründe
- Erfinde KEINE Personen, Orte, Kinder, Dörfer oder sonstige Details
- Erwähne NUR was in der aktuellen Situation existiert
- Bei Fragen antworte nur basierend auf dem was du SIEHST
- Wenn du etwas nicht weißt: "Weiß ich nicht" oder "Kann ich nicht sagen"

Regeln:
1. Wenn die Anweisung des Benutzers einer der obigen Aktionen entspricht, antworte mit: 
   {{"decision_type": "action", "name": "AKTIONSNAME", "execution_text": "Ein kurzer Satz im Charakter, der die Ausführung bestätigt."}}
   Beispiel: {{"decision_type": "action", "name": "nehme_stock", "execution_text": "Na gut, ich heb den knorrigen Stock auf."}}

2. Für normale Begrüßungen oder Smalltalk: {{"decision_type": "conversation", "content": "Kurze Antwort im Charakter - OHNE erfundene Details"}}

3. NUR wenn explizit nach Hilfe/Optionen gefragt wird: {{"decision_type": "help"}}

4. Für alle anderen Fragen: {{"decision_type": "conversation", "content": "Antwort basierend NUR auf dem was du siehst"}}

Beispiele:
- {{"decision_type": "conversation", "content": "Weiß ich auch nicht. Ich seh nur ein altes Haus, ein Fenster, einen Briefkasten und einen Stock."}}
- {{"decision_type": "conversation", "content": "Keine Ahnung. Ich steh nur hier rum."}}

ERFINDE NIEMALS GESCHICHTEN, ZIELE ODER DETAILS DIE NICHT EXPLIZIT VORGEGEBEN SIND!
ANTWORTE NUR MIT JSON, NIEMALS MIT NORMALEM TEXT!
    """


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


    def _trim_history(self):
        entry_limit = 8
        self.history = self.history[-entry_limit:]
