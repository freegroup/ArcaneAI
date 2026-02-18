"""
Routes for managing sounds (list, get).
Handles both global sounds and game-specific sounds.
"""
import os
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/sounds", tags=["sounds"])

# These will be set by main.py
MAPS_ROOT_DIR = None
SOUNDFX_ROOT_DIR = None

def init_routes(maps_dir: str, soundfx_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR, SOUNDFX_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir
    SOUNDFX_ROOT_DIR = soundfx_dir


@router.get("/{game_name}", response_model=List[str])
async def list_sounds(game_name: str):
    """
    List all available sounds for a game.
    Returns paths with prefix:
    - global/... for central sound files
    - map/... for game-specific sound files
    """
    files = []
    
    # 1. Global sounds from central soundfx directory
    try:
        if os.path.exists(SOUNDFX_ROOT_DIR):
            for root, dirs, filenames in os.walk(SOUNDFX_ROOT_DIR):
                for filename in filenames:
                    if filename.endswith((".mp3", ".wav", ".ogg")):
                        rel_path = os.path.relpath(
                            os.path.join(root, filename), 
                            SOUNDFX_ROOT_DIR
                        )
                        files.append(f"global/{rel_path}")
    except Exception as e:
        print(f"[WARNING] Could not read global soundfx directory: {e}")
    
    # 2. Game-specific sounds from game directory
    game_sounds_dir = os.path.join(MAPS_ROOT_DIR, game_name, "soundfx")
    try:
        if os.path.exists(game_sounds_dir):
            for root, dirs, filenames in os.walk(game_sounds_dir):
                for filename in filenames:
                    if filename.endswith((".mp3", ".wav", ".ogg")):
                        rel_path = os.path.relpath(
                            os.path.join(root, filename), 
                            game_sounds_dir
                        )
                        files.append(f"map/{rel_path}")
    except Exception as e:
        print(f"[WARNING] Could not read game soundfx directory for '{game_name}': {e}")
    
    return sorted(files)


@router.get("/{game_name}/{file_path:path}")
async def get_sound(game_name: str, file_path: str):
    """
    Get a specific sound file.
    file_path should include prefix (global/ or map/).
    """
    # Determine source based on prefix
    if file_path.startswith("global/"):
        relative_path = file_path[7:]  # Remove "global/" prefix
        file_location = os.path.join(SOUNDFX_ROOT_DIR, relative_path)
    elif file_path.startswith("map/"):
        relative_path = file_path[4:]  # Remove "map/" prefix
        file_location = os.path.join(MAPS_ROOT_DIR, game_name, "soundfx", relative_path)
    else:
        # Fallback: assume game-specific (backwards compatibility)
        file_location = os.path.join(MAPS_ROOT_DIR, game_name, "soundfx", file_path)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Sound file not found: {file_path}")
    
    # Determine media type
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg'
    }
    media_type = media_types.get(ext, 'audio/mpeg')
    
    return FileResponse(
        file_location, 
        media_type=media_type, 
        filename=os.path.basename(file_path)
    )