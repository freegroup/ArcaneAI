"""
Configuration loader for game settings.
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class GameConfig:
    """
    Game configuration with validated properties.
    All paths are absolute and resolved relative to config.yaml location.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Load and validate configuration.
        
        Args:
            config_path: Path to config.yaml. If None, looks for config.yaml in project root
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If required configuration is missing
        """
        if config_path is None:
            # Default to dungeon/config.yaml (project root, 2 levels up from game/src)
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self._config_path = Path(config_path)
        
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        
        # Load YAML
        with open(self._config_path, 'r', encoding='utf-8') as f:
            self._data: Dict[str, Any] = yaml.safe_load(f)
        
        # Project root is where config.yaml is located
        self._project_root = self._config_path.parent
        
        # Validate required fields
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration fields."""
        if 'maps_directory' not in self._data:
            raise ValueError("'maps_directory' is required in config.yaml")
        
        if 'game_name' not in self._data:
            raise ValueError("'game_name' is required in config.yaml")
        
        if 'sound' not in self._data:
            raise ValueError("'sound' section is required in config.yaml")
        
        if 'soundfx_dir' not in self._data['sound']:
            raise ValueError("'sound.soundfx_dir' is required in config.yaml")
        
        if 'llm' not in self._data:
            raise ValueError("'llm' section is required in config.yaml")
    
    @property
    def project_root(self) -> Path:
        """Project root directory (where config.yaml is located)."""
        return self._project_root
    
    @property
    def maps_directory(self) -> Path:
        """Absolute path to maps directory."""
        return self._project_root / self._data['maps_directory']
    
    @property
    def game_name(self) -> str:
        """Name of the game to load."""
        return self._data['game_name']
    
    @property
    def game_definition_path(self) -> Path:
        """Absolute path to game definition file (maps_directory/game_name/index.json)."""
        return self.maps_directory / self.game_name / "index.json"
    
    @property
    def soundfx_directory(self) -> Path:
        """Absolute path to sound effects directory."""
        return self._project_root / self._data['sound']['soundfx_dir']
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM configuration dictionary."""
        return self._data['llm']
    
    @property
    def voice_config(self) -> Dict[str, Any]:
        """Voice/TTS configuration dictionary."""
        return self._data.get('voice', {})
    
    @property
    def debug_config(self) -> Dict[str, Any]:
        """Debug configuration dictionary."""
        return self._data.get('debug', {})
    
    @property
    def raw_config(self) -> Dict[str, Any]:
        """Raw configuration dictionary (for backward compatibility)."""
        return self._data.copy()
    
    def __repr__(self) -> str:
        return (
            f"GameConfig(\n"
            f"  project_root={self.project_root}\n"
            f"  maps_directory={self.maps_directory}\n"
            f"  game_name={self.game_name}\n"
            f"  soundfx_directory={self.soundfx_directory}\n"
            f")"
        )


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file (legacy function for backward compatibility).
    
    Args:
        config_path: Path to config.yaml. If None, looks for config.yaml in project root
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config = GameConfig(Path(config_path) if config_path else None)
    return config.raw_config