"""
Routes for managing games - Collection and Single Game operations.
Follows RESTful conventions:
  - GET    /games         - List all games
  - POST   /games         - Create new game (copies template)
  - GET    /games/{name}  - Load game (redirect - actual data in sub-resources)
  - PUT    /games/{name}  - Update game (placeholder - actual updates via sub-resources)
  - DELETE /games/{name}  - Delete game
  
Sub-resources:
  - GET/PUT /games/{name}/config   - Game configuration
  - GET/PUT /games/{name}/model    - Game model (states, connections)
  - GET/PUT /games/{name}/views/*  - View layouts (handled by views_routes.py)
"""
import os
import json
import shutil
import re
from typing import List
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/games", tags=["games"])

# These will be set by main.py
MAPS_ROOT_DIR = None

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


# ============================================================
# Collection Operations
# ============================================================

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


class CreateGameRequest(BaseModel):
    name: str


@router.post("/")
async def create_game(request: CreateGameRequest):
    """
    Create a new game by copying the maps/template folder.
    
    POST is used because we're creating a new resource.
    The game name is in the body, not URL, because it will be sanitized.
    
    Returns:
        - 201 Created with game_name if successful
        - 400 Bad Request if name is invalid
        - 409 Conflict if game already exists
    """
    # Sanitize game name - only allow alphanumeric, underscore, and hyphen
    sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', request.name)
    if not sanitized_name:
        raise HTTPException(
            status_code=400, 
            detail="Invalid game name - must contain alphanumeric characters"
        )
    
    # Template folder is maps/template
    template_dir = os.path.join(MAPS_ROOT_DIR, "template")
    
    if not os.path.exists(template_dir):
        raise HTTPException(
            status_code=500, 
            detail="Template folder 'maps/template' not found"
        )
    
    # Target game directory
    game_dir = os.path.join(MAPS_ROOT_DIR, sanitized_name)
    
    if os.path.exists(game_dir):
        raise HTTPException(
            status_code=409, 
            detail=f"Game '{sanitized_name}' already exists"
        )
    
    try:
        # Copy entire template directory to new game directory
        shutil.copytree(template_dir, game_dir)
        
        # Update the config.json with the new game name
        config_path = os.path.join(game_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Update the name in config
            config['name'] = sanitized_name
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        return {
            "message": f"Game '{sanitized_name}' created successfully",
            "game_name": sanitized_name
        }
    except Exception as e:
        # Cleanup on failure
        if os.path.exists(game_dir):
            shutil.rmtree(game_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to create game: {e}")


# ============================================================
# Single Game Operations
# ============================================================

@router.get("/{game_name}")
async def get_game(game_name: str):
    """
    Get basic info about a game.
    
    Note: This is a placeholder. Actual game data is loaded via:
    - /games/{name}/config - Configuration
    - /games/{name}/model  - States and connections
    - /games/{name}/views/* - View layouts
    """
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    return {
        "game_name": game_name,
        "exists": True,
        "message": "Use sub-resources (/config, /model, /views) to access game data"
    }


@router.delete("/{game_name}")
async def delete_game(game_name: str):
    """Delete a game and all its files."""
    # Prevent deleting template
    if game_name == "template":
        raise HTTPException(status_code=403, detail="Cannot delete template")
    
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    try:
        shutil.rmtree(game_dir)
        return {"message": f"Game '{game_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete game: {e}")


# ============================================================
# Config Sub-Resource
# ============================================================

@router.get("/{game_name}/config")
async def get_config(game_name: str):
    """Load a game's config.json file."""
    config_path = os.path.join(MAPS_ROOT_DIR, game_name, "config.json")
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Config for game '{game_name}' not found")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading config: {e}")


@router.put("/{game_name}/config")
async def save_config(game_name: str, config: dict = Body(...)):
    """Save/update a game's config.json file."""
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    config_path = os.path.join(game_dir, "config.json")
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return {"message": f"Config for '{game_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")


# ============================================================
# Model Sub-Resource
# ============================================================

@router.get("/{game_name}/model")
async def get_model(game_name: str):
    """Load a game's model.json file (states and connections)."""
    model_path = os.path.join(MAPS_ROOT_DIR, game_name, "model.json")
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"Model for game '{game_name}' not found")
    
    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading model: {e}")


@router.put("/{game_name}/model")
async def save_model(game_name: str, model: dict = Body(...)):
    """Save/update a game's model.json file."""
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    
    if not os.path.exists(game_dir):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    model_path = os.path.join(game_dir, "model.json")
    
    try:
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model, f, indent=2, ensure_ascii=False)
        return {"message": f"Model for '{game_name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save model: {e}")