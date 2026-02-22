"""
Game Engine - Central coordinator for game components.
Loads game definition and coordinates StateEngine, Inventory, and LLM.
"""
from __future__ import annotations
import json
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
    
    def reinitialize_from_memory(self, model_data: Dict[str, Any], config_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Reinitialize the game engine with in-memory model/config data.
        Used by Developer Server to hot-reload without saving to disk.
        
        Args:
            model_data: Model data dict (states, connections)
            config_data: Config data dict (personality, inventory) - optional
        """
        print("[ENGINE] Reinitializing from in-memory data...")
        
        # Convert overlay data to engine format
        self.game_data = self._convert_overlay_data(model_data, config_data)
        
        # Reinitialize state engine with new data
        self.state_engine = StateEngine(
            session=self.session,
            states=self.game_data.get('states', {}),
            actions=self.game_data.get('actions', []),
            initial_state=self.game_data.get('initial_state')
        )
        
        # Reinitialize inventory with new data
        self.inventory = Inventory(
            session=self.session,
            items=self.game_data.get('inventory', {})
        )
        
        # Re-register inventory hook
        self.state_engine.add_action_hook(self.inventory.on_action)
        
        # Recreate controller (it references state_engine/inventory via session)
        self.controller = GameController(session=self.session)
        
        print(f"[ENGINE] Reinitialized with {len(self.game_data.get('states', {}))} states, {len(self.game_data.get('actions', []))} actions")
    
    def process_input(self, user_input: str) -> dict:
        """
        Process user input through the game controller.
        
        Args:
            user_input: User's input text
            
        Returns:
            Dict with 'response' (str), 'executed_action' (str or None)
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
        Load game definition from Overlay Pattern format (model.json + config.json).
        
        Args:
            definition_path: Path to game definition directory or index.json
            
        Returns:
            Game data dictionary (Internal Engine Format)
        """
        path: Path = Path(definition_path)
        
        # Determine the game directory
        if path.suffix == '.json':
            game_dir = path.parent
        else:
            game_dir = path
            
        model_path = game_dir / 'model.json'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Game definition not found: {model_path}")
        
        print(f"[ENGINE] Loading Overlay Pattern format from: {model_path}")
        return self._convert_overlay_format(game_dir)

    def _convert_overlay_format(self, game_dir: Path) -> Dict[str, Any]:
        """
        Convert Overlay Pattern format (model.json + config.json) to Engine format.
        
        Args:
            game_dir: Path to game directory containing model.json and config.json
            
        Returns:
            Engine-compatible game definition
        """
        model_path = game_dir / 'model.json'
        config_path = game_dir / 'config.json'
        
        # Load model.json
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # Load config.json (optional)
        config_data = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        return self._convert_overlay_data(model_data, config_data)
    
    def _convert_overlay_data(self, model_data: Dict[str, Any], config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert Overlay Pattern data (model + config dicts) to Engine format.
        This method can be used for both file-based and in-memory model data.
        
        Args:
            model_data: Model data dict (states, connections)
            config_data: Config data dict (personality, inventory) - optional
            
        Returns:
            Engine-compatible game definition
        """
        if config_data is None:
            config_data = {}
        
        states_dict = model_data.get('states', {})
        connections_dict = model_data.get('connections', {})
        
        # 1. Parse Config
        identity = config_data.get('personality', '') + '\n'
        behaviour = "WICHTIG: Du darfst NUR die explizit definierten Aktionen verwenden. Erfinde NIEMALS eigene Aktionen."
        welcome_prompt = config_data.get('welcome_prompt', '')
        
        # Convert Inventory list to dict
        inventory = {}
        for item in config_data.get('inventory', []):
            key = item.get('key')
            value = item.get('value')
            if key:
                inventory[key] = value
        
        # 2. Parse States
        states = {}
        state_id_map = {}  # Map ID to Name
        initial_state = None  # Will be set by state with stateType='START'
        
        for state_id, state_obj in states_dict.items():
            name = state_obj.get('name')
            user_data = state_obj.get('userData', {})
            
            state_id_map[state_id] = name
            
            # State marked as START is the initial state
            if state_obj.get('stateType') == 'START':
                initial_state = name
                # Don't skip - this is a real state, just marked as start!
            
            state_data = {
                'description': user_data.get('system_prompt', ''),
            }
            
            ambient_sound = user_data.get('ambient_sound')
            if ambient_sound:
                state_data['ambient_sound'] = ambient_sound
            
            ambient_volume = user_data.get('ambient_sound_volume')
            if ambient_volume is not None:
                state_data['ambient_sound_volume'] = ambient_volume
            
            states[name] = state_data
        
        # 3. Parse Actions from Connections
        actions = []
        
        for conn_id, conn_obj in connections_dict.items():
            source_id = conn_obj.get('source', {}).get('node')
            target_id = conn_obj.get('target', {}).get('node')
            user_data = conn_obj.get('userData', {})
            
            state_before = state_id_map.get(source_id)
            state_after = state_id_map.get(target_id)
            
            if not state_before or not state_after:
                continue
            
            name = conn_obj.get('name', '')
            if not name:
                continue
            
            action = {
                'name': name,
                'state_before': state_before,
                'state_after': state_after,
                'prompts': {
                    'description': user_data.get('description', name),
                    'after_fire': user_data.get('system_prompt', '')
                }
            }
            
            if user_data.get('sound_effect'):
                action['sound_effect'] = user_data.get('sound_effect')
            if user_data.get('sound_effect_volume') is not None:
                action['sound_effect_volume'] = user_data.get('sound_effect_volume')
            if user_data.get('sound_effect_duration') is not None:
                action['sound_effect_duration'] = user_data.get('sound_effect_duration')
            if user_data.get('conditions'):
                action['conditions'] = user_data.get('conditions')
            if user_data.get('actions'):
                action['scripts'] = user_data.get('actions')
            
            actions.append(action)
        
        # 4. Parse Internal Triggers from States
        for state_id, state_obj in states_dict.items():
            state_name = state_obj.get('name')
            
            for trigger in state_obj.get('trigger', []):
                name = trigger.get('name')
                if not name:
                    continue
                
                action = {
                    'name': name,
                    'state_before': state_name,
                    'state_after': state_name,
                    'prompts': {
                        'description': trigger.get('description', name),
                        'after_fire': trigger.get('system_prompt', '')
                    }
                }
                
                if trigger.get('sound_effect'):
                    action['sound_effect'] = trigger.get('sound_effect')
                if trigger.get('sound_effect_volume') is not None:
                    action['sound_effect_volume'] = trigger.get('sound_effect_volume')
                if trigger.get('sound_effect_duration') is not None:
                    action['sound_effect_duration'] = trigger.get('sound_effect_duration')
                if trigger.get('conditions'):
                    action['conditions'] = trigger.get('conditions')
                if trigger.get('actions'):
                    action['scripts'] = trigger.get('actions')
                
                actions.append(action)
        
        # ERROR if no state is marked as START
        if not initial_state:
            print("\n" + "=" * 70)
            print("FATAL ERROR: No initial state found!")
            print("=" * 70)
            print("Mark exactly one state with stateType='START' to define")
            print("where the game begins.")
            print("=" * 70 + "\n")
            import sys
            sys.exit(1)
        
        print(f"[ENGINE] Loaded Overlay format: {len(states)} states, {len(actions)} actions, initial={initial_state}")
        
        return {
            'initial_state': initial_state,
            'personality': identity,
            'behaviour': behaviour,
            'welcome_prompt': welcome_prompt,
            'states': states,
            'actions': actions,
            'inventory': inventory
        }

    
