# parser.py
import instructor
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Type

exakter_modell_name = "DeepSeek-Coder-V2-Lite-Instruct-Q8_0"

# Client Konfiguration bleibt gleich
client = instructor.patch(OpenAI(base_url="http://localhost:1337/v1", api_key="any"))


def get_tool_call(user_input: str, tools: List[Type[BaseModel]]) -> BaseModel | None:
    """Diese Funktion ist generisch und enthält jetzt die finale, sichere Prüfung."""
    try:
        tools_json = [
            {"type": "function", "function": tool.model_json_schema()}
            for tool in tools
        ]
        
        response = client.chat.completions.create(
            model=exakter_modell_name,
            messages=[{"role": "user", "content": user_input}],
            tools=tools_json,
            tool_choice="auto",
        )
        
        # --- HIER IST DER FINALE FIX ---
        # Wir prüfen zuerst sicher, ob das Attribut 'tool_calls' überhaupt existiert,
        # bevor wir versuchen, darauf zuzugreifen.
        if hasattr(response, 'tool_calls') and response.tool_calls:
        # -----------------------------
            tool_call = response.tool_calls[0]
            for tool in tools:
                if tool.__name__ == tool_call.function.name:
                    return tool.model_validate_json(tool_call.function.arguments)
        
        # Wenn das Feld nicht existiert oder leer ist, geben wir None zurück.
        return None
        
    except Exception as e:
        print(f"Fehler bei der Tool-Anfrage: {e}")
        return None