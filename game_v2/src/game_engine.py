"""
Game Engine - Central coordinator for game components.
Loads game definition and coordinates StateEngine, Inventory, and LLM.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, TYPE_CHECKING

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
    
    def __init__(self, session: GameSession, definition_path: str) -> None:
        """
        Initialize the game engine.
        
        Args:
            session: GameSession for message passing (REQUIRED)
            definition_path: Path to game_definition.json
        """
        self.session: GameSession = session
        
        # Load game definition
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
    
    def _load_game_definition(self, definition_path: str) -> Dict[str, Any]:
        """
        Load game definition from JSON file.
        
        Args:
            definition_path: Path to game_definition.json
            
        Returns:
            Game data dictionary
        """
        path: Path = Path(definition_path)
        if not path.exists():
            raise FileNotFoundError(f"Game definition not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
