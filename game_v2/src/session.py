"""
Game Session Management
Holds user-specific game state and data.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from messaging import MessageQueue
from game_engine import GameEngine
from config_loader import load_config

if TYPE_CHECKING:
    from audio.base_sink import BaseAudioSink
    from sound.base import BaseJukebox


class GameSession:
    """
    Represents a user's game session.
    Passive container for session data and game_engine.
    """
    
    def __init__(
        self,
        session_id: str,
        config: Optional[Dict[str, Any]] = None,
        message_queue: Optional[MessageQueue] = None,
        audio_sink: Optional[BaseAudioSink] = None,
        jukebox: Optional[BaseJukebox] = None
    ) -> None:
        """
        Initialize a game session.
        Game definition is loaded from config.yaml (maps_directory + game_name).

        Args:
            session_id: Unique session identifier
            config: Loaded configuration dictionary (if None, loads from default path)
            message_queue: MessageQueue for sending messages (set when WebSocket connects)
            audio_sink: Audio output sink (PyAudioSink, WebSocketSink, etc.)
            jukebox: Sound player (LocalJukebox, WebJukebox)
        """
        self.session_id: str = session_id
        self.config: Dict[str, Any] = config if config is not None else load_config()
        self.message_queue: Optional[MessageQueue] = message_queue
        self.audio_sink: Optional[BaseAudioSink] = audio_sink
        self.jukebox: Optional[BaseJukebox] = jukebox
        
        # Timestamps
        self.created_at: datetime = datetime.now()
        self.last_activity: datetime = datetime.now()
        
        # WebSocket token for web interface
        self.ws_token: Optional[str] = None
        
        # GameEngine creates and manages all game components
        # Reads game definition from config.yaml (maps_directory + game_name)
        self.game_engine: GameEngine = GameEngine(session=self)
    
    def update_activity(self) -> None:
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
