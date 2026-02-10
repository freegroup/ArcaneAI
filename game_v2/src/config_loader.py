"""
Configuration loader for game settings.
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, looks for config.yaml in game_v2/
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    if config_path is None:
        # Default to game_v2/config.yaml (relative to this file)
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config: Dict[str, Any] = yaml.safe_load(f)
    
    return config