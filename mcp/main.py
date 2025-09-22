# main.py
import json
from tool_factory import create_tool_from_json
from parser import get_tool_call
from pydantic import BaseModel
from typing import Dict, Type

class GameController:
    def __init__(self, game_definition_path: str):
        # --- 1. Lade die gesamte Spieldatei ---
        with open(game_definition_path, 'r', encoding='utf-8') as f:
            game_def = json.load(f)

        # --- 2. Erstelle die Tool Registry DYNAMISCH ---
        self.TOOL_REGISTRY: Dict[str, Type[BaseModel]] = {}
        for func_def in game_def["functions"]:
            tool_name = func_def["name"]
            self.TOOL_REGISTRY[tool_name] = create_tool_from_json(func_def)
        
        print("Folgende Werkzeuge wurden dynamisch geladen:", list(self.TOOL_REGISTRY.keys()))

        self.game_states = game_def["states"]
        self.current_state = "A" # Startzustand
        print("\nWillkommen beim dynamischen JSON-Adventure!")

    def process_tool_call(self, tool_call):
        if tool_call is None:
            print("Ich bin nicht sicher, was ich tun soll.")
            return

        tool_name = tool_call.__class__.__name__
        
        # Generische Verarbeitung der Tool-Aufrufe
        if tool_name == "gehe_nach":
            # Spezifische Logik für den "gehe_nach" Befehl
            valid_next_states = {'A': ['B'], 'B': ['A', 'C'], 'C': ['A']}
            ziel = tool_call.ziel
            if ziel in valid_next_states.get(self.current_state, []):
                self.current_state = ziel
                print(f"--- Du gehst nach {self.current_state}. ---")
            else:
                print(f"Von hier aus kannst du nicht nach '{ziel}' gehen.")
        
        elif tool_name == "untersuche_objekt":
            print(f"Du untersuchst: {tool_call.objekt}. Nichts Besonderes zu sehen.")
        
        elif tool_name == "nimm_objekt":
            print(f"Du nimmst: {tool_call.gegenstand}.")
        
        else:
            print(f"Unbekanntes Werkzeug '{tool_name}' wurde aufgerufen.")

    def run_game_loop(self):
        while True:
            state_info = self.game_states[self.current_state]
            
            print("\n" + "="*40)
            print(state_info['description'])
            
            user_input = input("> ")
            if user_input.lower() in ['quit', 'exit']:
                break
            
            allowed_tool_names = state_info['valid_tool_names']
            allowed_tools = [self.TOOL_REGISTRY[name] for name in allowed_tool_names]
            
            tool_call_result = get_tool_call(user_input, allowed_tools)
            
            self.process_tool_call(tool_call_result)
        
        print("Auf Wiedersehen!")

# --- Anwendung starten ---
if __name__ == "__main__":
    # Die Engine startet und lädt das Spiel aus der JSON-Datei
    controller = GameController(game_definition_path='game_definition.json')
    controller.run_game_loop()