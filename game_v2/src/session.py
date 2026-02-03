"""
Game Session Management
Holds user-specific game state and data.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from game_controller import GameController


class GameSession:
    """
    Represents a user's game session.
    Holds all user-specific state including inventory, stats, flags, etc.
    """
    
    def __init__(self, session_id: str, game_controller: GameController):
        """
        Initialize a game session.
        
        Args:
            session_id: Unique session identifier
            game_controller: GameController instance for this session
        """
        self.session_id = session_id
        self.game_controller = game_controller
        
        # Future: Inventory System
        self.inventory: Dict[str, int] = {}  # {"item_name": quantity}
        
        # Future: Player Stats
        self.player_stats: Dict[str, Any] = {
            "health": 100,
            "mana": 100,
        }
        
        # Future: Quest System
        self.quests: list = []
        
        # Future: Flags for story decisions
        self.flags: Dict[str, bool] = {}  # {"has_talked_to_npc": True}
        
        # WebSocket token for web interface
        self.ws_token: Optional[str] = None
        
        # Timestamps
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def get_current_state(self) -> str:
        """Get current game state name."""
        return self.game_controller.get_current_state()
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and return response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        self.update_activity()
        return self.game_controller.process_input(user_input)
    
    def start_game(self) -> str:
        """
        Start the game.
        
        Returns:
            Initial state description
        """
        self.update_activity()
        return self.game_controller.start_game()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize session to dictionary (for future save/load).
        
        Returns:
            Dictionary representation of session
        """
        return {
            "session_id": self.session_id,
            "current_state": self.get_current_state(),
            "inventory": self.inventory,
            "player_stats": self.player_stats,
            "quests": self.quests,
            "flags": self.flags,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }