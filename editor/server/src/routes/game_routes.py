"""
Routes for managing a single game (load, save, update).
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/game", tags=["game"])

# These will be set by main.py
MAPS_ROOT_DIR = None

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


@router.get("/{game_name}")
async def load_game(game_name: str):
    """Load a game's index.json file."""
    file_location = os.path.join(MAPS_ROOT_DIR, game_name, "index.json")
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    return FileResponse(file_location)


@router.put("/{game_name}")
async def save_game(game_name: str, file: UploadFile = File(...)):
    """Save/update a game's index.json file."""
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    # Ensure game directory exists
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    file_location = os.path.join(game_dir, "index.json")
    
    try:
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return {"message": f"Game '{game_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save game: {e}")