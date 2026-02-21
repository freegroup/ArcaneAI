"""
Routes for managing game views, model and config (Overlay Pattern).
Views represent different visual layouts of the same canonical model.
"""
import os
import json
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/game", tags=["views"])

# Will be set by main.py
MAPS_ROOT_DIR = None

# Constants
VIEWS_DIR = "views"

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


# --- Model Endpoints ---

@router.get("/{game_name}/model")
async def load_model(game_name: str):
    """Load a game's model.json file (canonical model without layout)."""
    file_location = os.path.join(MAPS_ROOT_DIR, game_name, "model.json")
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Model for game '{game_name}' not found")
    
    return FileResponse(file_location)


@router.put("/{game_name}/model")
async def save_model(game_name: str, file: UploadFile = File(...)):
    """Save/update a game's model.json file."""
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        os.makedirs(game_dir, exist_ok=True)
    
    file_location = os.path.join(game_dir, "model.json")
    
    try:
        content = await file.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return {"message": f"Model for game '{game_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save model: {e}")


# --- Config Endpoints ---

@router.get("/{game_name}/config")
async def load_config(game_name: str):
    """Load a game's config.json file (prompts, inventory, etc.)."""
    file_location = os.path.join(MAPS_ROOT_DIR, game_name, "config.json")
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Config for game '{game_name}' not found")
    
    return FileResponse(file_location)


@router.put("/{game_name}/config")
async def save_config(game_name: str, file: UploadFile = File(...)):
    """Save/update a game's config.json file."""
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        os.makedirs(game_dir, exist_ok=True)
    
    file_location = os.path.join(game_dir, "config.json")
    
    try:
        content = await file.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return {"message": f"Config for game '{game_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")


# --- Views Endpoints ---

@router.get("/{game_name}/views", response_model=List[str])
async def list_views(game_name: str):
    """List all views for a specific game."""
    views_dir = os.path.join(MAPS_ROOT_DIR, game_name, VIEWS_DIR)
    
    if not os.path.exists(views_dir):
        # Return empty list if views directory doesn't exist yet
        return []
    
    try:
        # List all .json files in the views directory
        files = [
            f[:-5]  # Remove .json extension
            for f in os.listdir(views_dir)
            if f.endswith('.json')
        ]
        return sorted(files)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing views: {e}"
        )


@router.get("/{game_name}/views/{view_name}")
async def get_view(game_name: str, view_name: str):
    """Get a specific view file."""
    view_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        VIEWS_DIR,
        f"{view_name}.json"
    )
    
    if not os.path.exists(view_file):
        raise HTTPException(
            status_code=404,
            detail=f"View '{view_name}' not found in game '{game_name}'"
        )
    
    return FileResponse(view_file)


@router.put("/{game_name}/views/{view_name}")
async def save_view(game_name: str, view_name: str, file: UploadFile = File(...)):
    """Create or update a view for a game."""
    # Ensure game exists
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    if not os.path.exists(game_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Game '{game_name}' not found"
        )
    
    # Create views directory if it doesn't exist
    views_dir = os.path.join(game_dir, VIEWS_DIR)
    os.makedirs(views_dir, exist_ok=True)
    
    view_file = os.path.join(views_dir, f"{view_name}.json")
    
    try:
        content = await file.read()
        with open(view_file, "wb") as f:
            f.write(content)
        return {"message": f"View '{view_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save view: {e}"
        )


@router.delete("/{game_name}/views/{view_name}")
async def delete_view(game_name: str, view_name: str):
    """Delete a view."""
    view_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        VIEWS_DIR,
        f"{view_name}.json"
    )
    
    if not os.path.exists(view_file):
        raise HTTPException(
            status_code=404,
            detail=f"View '{view_name}' not found"
        )
    
    try:
        os.remove(view_file)
        return {"message": f"View '{view_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete view: {e}"
        )