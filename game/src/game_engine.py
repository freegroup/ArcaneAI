"""
Game Engine - Central coordinator for game components.
Loads game definition and coordinates StateEngine, Inventory, and LLM.
"""
from __future__ import annotations
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from state_engine import StateEngine
from inventory import Inventory
from game_controller import GameController

if TYPE_CHECKING:
    from session import GameSession


class GameEngine:
    """
    Central game engine that coordinates all game components.
    Loads game definition and delegates to specialized components.
    """
    
    def __init__(self, session: GameSession) -> None:
        """
        Initialize the game engine.
        Reads maps_directory and game_name from config.yaml.
        
        Args:
            session: GameSession for message passing (REQUIRED)
        """
        self.session: GameSession = session
        
        # Load game definition from config
        definition_path = self._get_definition_path_from_config()
        self.game_data: Dict[str, Any] = self._load_game_definition(definition_path)
        
        # Initialize components (pass session to all)
        self.state_engine: StateEngine = StateEngine(
            session=session,
            states=self.game_data.get('states', {}),
            actions=self.game_data.get('actions', []),
            initial_state=self.game_data.get('initial_state')
        )
        
        self.inventory: Inventory = Inventory(
            session=session,
            items=self.game_data.get('inventory', {})
        )
        
        # Register inventory directly with state engine
        self.state_engine.add_action_hook(self.inventory.on_action)
        
        # Create GameController (decides its own LLM implementation)
        self.controller: GameController = GameController(session=session)
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input through the game controller.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        return self.controller.process_input(user_input)
    
    def start_game(self) -> str:
        """
        Start the game.
        
        Returns:
            Initial state description
        """
        return self.controller.start_game()
    
    def _get_definition_path_from_config(self) -> str:
        """
        Read config.yaml and construct path to game definition.
        
        Returns:
            Full path to game definition file (maps_directory/game_name/index.json)
        """
        from config_loader import GameConfig
        
        # Load configuration
        config = GameConfig()
        
        # Get game definition path (already validated and resolved)
        game_path = config.game_definition_path
        
        print(f"[CONFIG] Loading game from: {game_path}")
        
        return str(game_path)
    
    def _load_game_definition(self, definition_path: str) -> Dict[str, Any]:
        """
        Load game definition from Designer JSON file (v2 format).
        ALWAYS converts from Designer format to Engine format.
        
        Args:
            definition_path: Path to game_definition_tipsy_v2.json
            
        Returns:
            Game data dictionary (Internal Engine Format)
        """
        path: Path = Path(definition_path)
        if not path.exists():
            raise FileNotFoundError(f"Game definition not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Always convert from Designer format (v2)
        # Note: Elements like 'Raft' (graphical groupings) are ignored by the converter
        # because it only looks for 'StateShape' and 'TriggerConnection'.
        # Data is extracted from 'userData' as expected by the Designer format.
        return self._convert_designer_format(data)

    def _convert_designer_format(self, designer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Designer JSON format (index.json) to Engine format.
        
        Args:
            designer_data: Raw JSON data from designer
            
        Returns:
            Engine-compatible game definition
        """
        config = designer_data.get("config", {})
        diagram = designer_data.get("diagram", [])
        
        # 1. Parse Config (Identity, Behaviour, Inventory)
        identity = config.get("identity", "")
        behaviour = "WICHTIG: Du darfst NUR die explizit definierten Aktionen verwenden. Erfinde NIEMALS eigene Aktionen. Wenn der Spieler etwas tun möchte, das nicht in der Liste der verfügbaren Aktionen steht, antworte im Piraten-Slang ablehnend und verwende [AKTION: keine_aktion]."
        
        # Convert Inventory list to dict
        inventory = {}
        for item in config.get("inventory", []):
            # item is like {"key": "coins", "value": 0, "type": "integer"}
            key = item.get("key")
            value = item.get("value")
            if key:
                inventory[key] = value
                
        # 2. Parse States (StateShape)
        states = {}
        state_id_map = {} # Map ID to Name
        start_node_id = None
        
        for element in diagram:
            if element.get("type") == "StateShape":
                state_id = element.get("id")
                name = element.get("name")
                user_data = element.get("userData", {})
                
                state_id_map[state_id] = name
                
                if element.get("stateType") == "START":
                    start_node_id = state_id
                    # Start node itself is usually skipped or empty in logic, 
                    # but we track it to find the real initial state via connection
                    continue
                
                # Build state object
                state_data = {
                    "description": user_data.get("system_prompt", ""),
                }
                
                # Ambient sound
                ambient_sound = user_data.get("ambient_sound")
                if ambient_sound:
                    state_data["ambient_sound"] = ambient_sound
                
                ambient_volume = user_data.get("ambient_sound_volume")
                if ambient_volume is not None:
                    state_data["ambient_sound_volume"] = ambient_volume
                    
                states[name] = state_data

        # 3. Parse Actions (TriggerConnection AND Internal Triggers)
        actions = []
        
        # 3a. TriggerConnections (Transitions)
        initial_state = None
        
        for element in diagram:
            if element.get("type") == "TriggerConnection":
                source_id = element.get("source", {}).get("node")
                target_id = element.get("target", {}).get("node")
                user_data = element.get("userData", {})
                
                # Resolve names
                state_before = state_id_map.get(source_id)
                state_after = state_id_map.get(target_id)
                
                # Special case: Connection from Start Node defines initial state
                if source_id == start_node_id:
                    initial_state = state_after
                    continue
                    
                if not state_before or not state_after:
                    continue
                
                name = element.get("name", "")
                if not name:
                    continue # Skip unnamed connections
                
                # Build action object
                action = {
                    "name": name,
                    "state_before": state_before,
                    "state_after": state_after,
                    "prompts": {
                        "description": user_data.get("description", name),
                        "after_fire": user_data.get("system_prompt", "")
                    }
                }
                
                # Optional fields
                if user_data.get("sound_effect"):
                    action["sound_effect"] = user_data.get("sound_effect")
                if user_data.get("sound_effect_volume") is not None:
                    action["sound_effect_volume"] = user_data.get("sound_effect_volume")
                if user_data.get("sound_effect_duration") is not None:
                    action["sound_effect_duration"] = user_data.get("sound_effect_duration")
                    
                if user_data.get("conditions"):
                    action["conditions"] = user_data.get("conditions")
                    
                if user_data.get("actions"):
                    # Designer uses "actions" for scripts
                    action["scripts"] = user_data.get("actions")
                    
                actions.append(action)

        # 3b. Internal Triggers (Actions within a StateShape)
        for element in diagram:
            if element.get("type") == "StateShape" and element.get("stateType") != "START":
                state_name = element.get("name")
                
                for trigger in element.get("trigger", []):
                    # Trigger structure: id, name, description, sound_effect..., system_prompt, conditions, actions
                    
                    name = trigger.get("name")
                    if not name: continue
                    
                    action = {
                        "name": name,
                        "state_before": state_name,
                        "state_after": state_name, # Internal trigger stays in same state
                        "prompts": {
                            "description": trigger.get("description", name),
                            "after_fire": trigger.get("system_prompt", "")
                        }
                    }
                    
                    if trigger.get("sound_effect"):
                        action["sound_effect"] = trigger.get("sound_effect")
                    if trigger.get("sound_effect_volume") is not None:
                        action["sound_effect_volume"] = trigger.get("sound_effect_volume")
                    if trigger.get("sound_effect_duration") is not None:
                        action["sound_effect_duration"] = trigger.get("sound_effect_duration")
                        
                    if trigger.get("conditions"):
                        action["conditions"] = trigger.get("conditions")
                        
                    if trigger.get("actions"):
                        action["scripts"] = trigger.get("actions")
                        
                    actions.append(action)

        # Fallback for initial state if not found via connection
        if not initial_state and states:
            # Fallback to "WestOfHouse" or just the first state
            if "WestOfHouse" in states:
                initial_state = "WestOfHouse"
            else:
                initial_state = list(states.keys())[0]

        return {
            "initial_state": initial_state,
            "identity": identity,
            "behaviour": behaviour,
            "states": states,
            "actions": actions,
            "inventory": inventory
        }
    
