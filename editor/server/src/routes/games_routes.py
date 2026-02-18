"""
Routes for managing the collection of games (list, create, delete).
"""
import os
from typing import List
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/games", tags=["games"])

# These will be set by main.py
MAPS_ROOT_DIR = None

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


@router.get("/", response_model=List[str])
async def list_games():
    """List all available games (directories in maps folder)."""
    try:
        directories = [
            d for d in os.listdir(MAPS_ROOT_DIR) 
            if os.path.isdir(os.path.join(MAPS_ROOT_DIR, d))
        ]
        return sorted(directories)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Maps directory not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing games: {e}")


@router.post("/{game_name}")
async def create_game(game_name: str):
    """Create a new game from template."""
    from fastapi.responses import FileResponse
    import shutil
    
    # Get template path (in src directory)
    template_path = os.path.join(Path(__file__).parent.parent, "template.json")
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="template.json not found")
    
    # Create game directory
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if os.path.exists(game_dir):
        raise HTTPException(status_code=409, detail=f"Game '{game_name}' already exists")
    
    try:
        os.makedirs(game_dir, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game directory: {e}")
    
    # Copy template to game directory
    game_file_path = os.path.join(game_dir, "index.json")
    try:
        shutil.copy(template_path, game_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy template: {e}")

    return FileResponse(game_file_path)


@router.delete("/{game_name}")
async def delete_game(game_name: str):
    """Delete a game and all its files."""
    import shutil
    
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    try:
        shutil.rmtree(game_dir)
        return {"message": f"Game '{game_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete game: {e}")