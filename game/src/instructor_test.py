import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Literal, Union, List, Annotated
import json
import re

# --- 1. Konfiguration & Setup ---

# Erweiterte Aktionen mit Beschreibungen
ACTIONS_WITH_DESCRIPTIONS = {
    'untersuche_das_fenster': 'das Fenster des Hauses genauer betrachten',
    'oeffne_das_fenster': 'versuchen, das Fenster zu öffnen',
    'untersuche_das_haus': 'das gesamte Haus von außen untersuchen',
    'untersuche_die_tuer': 'die Haustür genauer inspizieren',
    'nehme_stock': 'den Stock vom Boden aufheben',
    'gehe_nach_norden': 'nach Norden weitergehen',
    'gehe_zum_briefkasten': 'zum Briefkasten gehen und ihn untersuchen',
    'gehe_zum_baum': 'zu dem nahegelegenen Baum gehen',
    'gehe_nach_sueden': 'nach Süden zurückkehren'
}

VALID_ACTIONS = list(ACTIONS_WITH_DESCRIPTIONS.keys())

SYSTEM_PROMPT = f"""
Du bist ein Haudegen im 17. Jahrhundert. Du bist mürrisch, zynisch, aber letztendlich ein hilfreicher Begleiter in einem Text-Adventure. Deine Antworten sollten immer kurz, im Charakter und auf den Punkt sein.

AKTUELLE SITUATION (NUR DIESE FAKTEN EXISTIEREN):
- Du stehst vor einem alten, verwitterten Haus
- Die Tür des Hauses ist verschlossen
- Daneben ist ein Fenster
- Es gibt einen Briefkasten
- Ein Stock liegt auf dem Boden
- Das ist ALLES was existiert - erfinde NICHTS dazu!

WICHTIG: Du MUSST immer mit einem JSON-Objekt antworten! Kein normaler Text!

STRIKTE REGELN:
- Erfinde KEINE Geschichten, Missionen, Ziele oder Hintergründe
- Erfinde KEINE Personen, Orte, Kinder, Dörfer oder sonstige Details
- Erwähne NUR was in der aktuellen Situation existiert
- Bei Fragen antworte nur basierend auf dem was du SIEHST
- Wenn du etwas nicht weißt: "Weiß ich nicht" oder "Kann ich nicht sagen"

Verfügbare Aktionen mit Beschreibungen:
{chr(10).join([f"- {action}: {desc}" for action, desc in ACTIONS_WITH_DESCRIPTIONS.items()])}

Regeln:
1. Wenn die Anweisung des Benutzers einer der obigen Aktionen entspricht, antworte mit: 
   {{"entscheidungstyp": "aktion", "name": "AKTIONSNAME", "ausfuehrungstext": "Ein kurzer Satz im Charakter, der die Ausführung bestätigt."}}
   Beispiel: {{"entscheidungstyp": "aktion", "name": "nehme_stock", "ausfuehrungstext": "Na gut, ich heb den knorrigen Stock auf."}}

2. Für normale Begrüßungen oder Smalltalk: {{"entscheidungstyp": "konversation", "inhalt": "Kurze Antwort im Charakter - OHNE erfundene Details"}}

3. NUR wenn explizit nach Hilfe/Optionen gefragt wird: {{"entscheidungstyp": "hilfe"}}

4. Für alle anderen Fragen: {{"entscheidungstyp": "konversation", "inhalt": "Antwort basierend NUR auf dem was du siehst"}}

Beispiele:
- User: "Worum geht es hier?" → {{"entscheidungstyp": "konversation", "inhalt": "Weiß ich auch nicht. Ich seh nur ein altes Haus, ein Fenster, einen Briefkasten und einen Stock."}}
- User: "Was ist unsere Mission?" → {{"entscheidungstyp": "konversation", "inhalt": "Keine Ahnung. Ich steh nur hier rum."}}

ERFINDE NIEMALS GESCHICHTEN, ZIELE ODER DETAILS DIE NICHT EXPLIZIT VORGEGEBEN SIND!
ANTWORTE NUR MIT JSON, NIEMALS MIT NORMALEM TEXT!
"""


CHAT_HISTORY = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "assistant", "content": '{"entscheidungstyp": "konversation", "inhalt": "Ich stehe vor einem alten, verwitterten Haus. Die Tür ist verschlossen, daneben ist ein Fenster und ein Briefkasten. Ein Stock liegt auf dem Boden."}'}
]

# Verwende normalen OpenAI Client für robustere JSON-Antworten
base_client = OpenAI(base_url="http://localhost:1337/v1", api_key="any")
model_name = "DeepSeek-Coder-V2-Lite-Instruct-Q8_0"


class Aktion(BaseModel):
    entscheidungstyp: str = Field("aktion", const=True)
    name: str
    ausfuehrungstext: str

    @model_validator(mode="after")
    def check_name(cls, values):
        if values.name not in VALID_ACTIONS:
            raise ValueError(f"Ungültige Aktion: {values.name}. Erlaubt: {VALID_ACTIONS}")
        return values


class Konversation(BaseModel):
    entscheidungstyp: Literal["konversation"]
    inhalt: str


class HilfeAnfordern(BaseModel):
    entscheidungstyp: Literal["hilfe"]


class KombinierteAntwort(BaseModel):
    entscheidungstyp: Literal["kombiniert"]
    konversation: str
    biete_hilfe_an: bool

Entscheidung = Annotated[
    Union[Aktion, Konversation, HilfeAnfordern, KombinierteAntwort],
    Field(discriminator="entscheidungstyp")
]

# --- 3. Robuste JSON-Parsing Funktionen ---

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


def fallback_to_conversation(user_input: str, raw_response: str) -> Entscheidung:
    """Behandelt erfundene Aktionen oder fehlerhaftes JSON intelligent."""
    
    print("⚠️  Fallback wird ausgeführt: Generiere eine kontextbezogene Ablehnungsantwort.")
    
    rejection_prompt = f"""
Du bist ein mürrischer Haudegen. Der Spieler hat etwas gesagt, das keinen Sinn ergibt oder nicht möglich ist: "{user_input}"

Deine verfügbaren Möglichkeiten sind:
{chr(10).join([f"- {desc}" for desc in ACTIONS_WITH_DESCRIPTIONS.values()])}

Gib eine kurze, mürrische Antwort im Charakter. Erkläre, dass das nicht geht und schlage vielleicht eine der verfügbaren Alternativen vor.
Beispiel: "Das geht hier nicht, Fremder! Du könntest stattdessen das Fenster untersuchen oder zum Briefkasten gehen."

Antworte nur mit dem reinen Text deiner Antwort, kein JSON!
"""
    
    try:
        response = base_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": rejection_prompt}],
            temperature=0.6,
            max_tokens=100
        )
        # KORREKTUR: Gib den neu generierten Text zurück, nicht die alte Antwort.
        rejection_text = response.choices[0].message.content.strip()
        return Konversation(entscheidungstyp="konversation", inhalt=rejection_text)
        
    except Exception as e:
        print(f"Fehler beim Generieren der Ablehnungsantwort: {e}")
        return Konversation(
            entscheidungstyp="konversation", 
            inhalt="Das kannst du hier nicht machen. Versuch was anderes!"
        )

def get_decision(user_input: str, history: List) -> Entscheidung:
    messages = history + [{"role": "user", "content": user_input}]
    
    try:
        # Normaler OpenAI Aufruf
        response = base_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=200
        )
        
        raw_content = response.choices[0].message.content
        print(f"🔍 Raw LLM: {raw_content}")
        
        # Extrahiere JSON
        json_str = extract_json_from_text(raw_content)
        print(f"🔍 Extracted JSON: {json_str}")
        
        # Parse JSON
        json_data = json.loads(json_str)
        
        # Validiere mit Pydantic
        if json_data.get("entscheidungstyp") == "aktion":
            try:
                return Aktion(**json_data)
            except ValidationError as ve:
                # LLM hat eine ungültige Aktion erfunden
                invalid_action = json_data.get("name", "unbekannt")
                return handle_invalid_action(user_input, invalid_action)
        elif json_data.get("entscheidungstyp") == "konversation":
            return Konversation(**json_data)
        elif json_data.get("entscheidungstyp") == "hilfe":
            return HilfeAnfordern(**json_data)
        else:
            raise ValueError(f"Unbekannter entscheidungstyp: {json_data.get('entscheidungstyp')}")
            
    except Exception as e:
        print(f"⚠️  JSON-Parsing failed: {e}")
        print(f"⚠️  Fallback für: '{user_input}'")
        return fallback_to_conversation(user_input, raw_content if 'raw_content' in locals() else "")

class HintResponse(BaseModel):
    hint: str = Field(description="Ein kurzer, zynischer aber hilfreicher Tipp im Charakter")

def generate_hint(current_actions: List[str]) -> str:
    """Generiert hilfreichen Tipp mit natürlichen Beschreibungen (ohne Tool-Namen)."""
    
    # Erstelle nur die Beschreibungen ohne Tool-Namen
    descriptions = [ACTIONS_WITH_DESCRIPTIONS[action] for action in current_actions]
    descriptions_text = ", ".join(descriptions)
    
    hint_prompt = f"""Du bist ein mürrischer aber hilfsbereiter Haudegen. Der Spieler braucht Orientierung.

AKTUELLE SITUATION (NUR DIESE FAKTEN EXISTIEREN):
- Du stehst vor einem alten, verwitterten Haus
- Die Tür ist verschlossen
- Daneben ist ein Fenster
- Es gibt einen Briefkasten
- Ein Stock liegt auf dem Boden
- Das ist ALLES was existiert

Der Spieler kann folgende Dinge tun:
{descriptions_text}

Gib einen kurzen, zynischen aber hilfreichen Überblick über 2-3 der interessantesten Möglichkeiten. 
Beschreibe sie natürlich, ohne technische Namen zu verwenden.
Bleib im Charakter - mürrisch aber letztendlich hilfsbereit.
ERFINDE KEINE zusätzlichen Details, Personen oder Orte!

Beispiele:
- "Na gut... Du könntest das Fenster genauer betrachten oder den Stock vom Boden aufheben. Oder geh nach Norden weiter."
- "Verdammt... Schau dir das Haus an, oder untersuche die Tür. Mach schon!"

Antworte nur mit dem natürlichen Tipp-Text, keine technischen Begriffe, KEINE erfundenen Details!"""
    
    try:
        response = base_client.chat.completions.create(
            model=model_name, 
            messages=[{"role": "user", "content": hint_prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Fehler beim Generieren des Hints: {e}")
        # Fallback mit natürlichen Beschreibungen
        sample_descriptions = [ACTIONS_WITH_DESCRIPTIONS[action] for action in current_actions[:3]]
        return f"Verdammt... Na gut: Du könntest {', oder '.join(sample_descriptions)}. Entscheide dich schon!"
    

def game_loop():
    current_history = CHAT_HISTORY.copy()
    current_valid_actions = VALID_ACTIONS 
    # Annahme: der 'inhalt' des assistant in CHAT_HISTORY ist bereits JSON. Wir parsen es für die erste Ausgabe.
    initial_message = json.loads(current_history[1]['content'])
    print(f"HAUDEGEN -> {initial_message['inhalt']}")
    
    while True:
        user_input = input("> ")
        if user_input.lower() in ["quit", "exit"]:
            print("Der Haudegen grunzt zum Abschied.")
            break

        response = get_decision(user_input, current_history)

        assistant_message = ""
        if isinstance(response, Aktion):
            action_desc = ACTIONS_WITH_DESCRIPTIONS.get(response.name, response.name)
            # NEU: Wir geben den vom LLM generierten Text aus
            print(f"🎮 AKTION -> {response.name} ({action_desc})")
            print(f"💬 HAUDEGEN -> {response.ausfuehrungstext}")
            # Wir speichern die gesamte JSON-Antwort in der History
            assistant_message = response.model_dump_json()
        
        elif isinstance(response, Konversation):
            print(f"💬 HAUDEGEN -> {response.inhalt}")
            assistant_message = response.model_dump_json()

        elif isinstance(response, HilfeAnfordern):
            print("🆘 HILFE WIRD GENERIERT...")
            hint_text = generate_hint(current_valid_actions)
            print(f"💡 HAUDEGEN -> {hint_text}")
            assistant_message = Konversation(entscheidungstyp="konversation", inhalt=hint_text).model_dump_json()
        
        # Füge die rohe JSON-Antwort des Assistenten zur History hinzu
        current_history.append({"role": "user", "content": user_input})
        current_history.append({"role": "assistant", "content": assistant_message})

if __name__ == "__main__":
    game_loop()