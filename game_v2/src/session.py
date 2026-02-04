"""
Game Session Management
Holds user-specific game state and data.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from messaging import MessageQueue, ConsoleMessageQueue
from game_engine import GameEngine


class GameSession:
    """
    Represents a user's game session.
    Passive container for session data and game_engine.
    """
    
    def __init__(self, session_id: str, definition_path: str, message_queue: MessageQueue = None):
        """
        Initialize a game session.
        
        Args:
            session_id: Unique session identifier
            definition_path: Path to game_definition.json
            message_queue: MessageQueue for sending messages (REQUIRED - must be set before use)
        """
        self.session_id = session_id
        self.message_queue = message_queue  # Will be set when WebSocket connects
        
        # Timestamps
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # WebSocket token for web interface
        self.ws_token: Optional[str] = None
        
        # GameEngine creates and manages all game components
        self.game_engine = GameEngine(session=self, definition_path=definition_path)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize session to dictionary (for future save/load).
        
        Returns:
            Dictionary representation of session
        """
        return {
            "session_id": self.session_id,
            "current_state": self.game_engine.state_engine.get_current_state().name,
            "inventory": self.game_engine.inventory.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
