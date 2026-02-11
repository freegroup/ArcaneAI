"""
Configuration loader for editor server.
Only loads maps_directory and soundfx_directory - no game-specific configs.
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class EditorConfig:
    """
    Editor server configuration with validated properties.
    Only provides maps_directory and soundfx_directory.
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
            # Default to dungeon/config.yaml (project root, 3 levels up from editor/server/src)
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        
        self._config_path = Path(config_path)
        
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        
        # Load YAML
        with open(self._config_path, 'r', encoding='utf-8') as f:
            self._data: Dict[str, Any] = yaml.safe_load(f)
        
        # Project root is where config.yaml is located
        self._project_root = self._config_path.parent
        
        # Validate required fields for editor
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration fields for editor."""
        if 'maps_directory' not in self._data:
            raise ValueError("'maps_directory' is required in config.yaml")
        
        if 'sound' not in self._data:
            raise ValueError("'sound' section is required in config.yaml")
        
        if 'soundfx_dir' not in self._data['sound']:
            raise ValueError("'sound.soundfx_dir' is required in config.yaml")
    
    @property
    def project_root(self) -> Path:
        """Project root directory (where config.yaml is located)."""
        return self._project_root
    
    @property
    def maps_directory(self) -> Path:
        """Absolute path to maps directory."""
        return self._project_root / self._data['maps_directory']
    
    @property
    def soundfx_directory(self) -> Path:
        """Absolute path to sound effects directory."""
        return self._project_root / self._data['sound']['soundfx_dir']
    
    def __repr__(self) -> str:
        return (
            f"EditorConfig(\n"
            f"  project_root={self.project_root}\n"
            f"  maps_directory={self.maps_directory}\n"
            f"  soundfx_directory={self.soundfx_directory}\n"
            f")"
        )