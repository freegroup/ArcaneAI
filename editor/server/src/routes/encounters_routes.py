"""
Routes for managing encounters within a game.
Encounters are derived from views with viewType='encounter' in the views/ directory.
This follows the Overlay Pattern where encounters are just filtered views.
"""
import os
import json
from typing import List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/game", tags=["encounters"])

# These will be set by main.py
MAPS_ROOT_DIR = None

# Constants
VIEWS_DIR = "views"

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


@router.get("/{game_name}/encounters", response_model=List[str])
async def list_encounters(game_name: str):
    """
    List all encounters for a specific game.
    Encounters are derived from views with prefix 'encounter_' in the views/ directory.
    Returns the encounter name without the 'encounter_' prefix.
    """
    views_dir = os.path.join(MAPS_ROOT_DIR, game_name, VIEWS_DIR)
    
    if not os.path.exists(views_dir):
        return []
    
    try:
        encounters = []
        for f in os.listdir(views_dir):
            if f.startswith('encounter_') and f.endswith('.json'):
                # Extract encounter name: "encounter_001_go.json" -> "001_go"
                encounter_name = f[10:-5]  # Remove "encounter_" prefix and ".json" suffix
                encounters.append(encounter_name)
        return sorted(encounters)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing encounters: {e}"
        )


@router.get("/{game_name}/encounters/{encounter_name}")
async def get_encounter(game_name: str, encounter_name: str):
    """
    Get encounter config (name, description) from the view file.
    The encounter data is stored in the encounterConfig field of the view.
    """
    view_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        VIEWS_DIR,
        f"encounter_{encounter_name}.json"
    )
    
    if not os.path.exists(view_file):
        raise HTTPException(
            status_code=404,
            detail=f"Encounter '{encounter_name}' not found in game '{game_name}'"
        )
    
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            view_data = json.load(f)
        
        # Return the encounterConfig (or empty config if not present)
        encounter_config = view_data.get('encounterConfig', {})
        return {
            'name': encounter_config.get('name', encounter_name),
            'description': encounter_config.get('description', ''),
            'encounter_prompt': encounter_config.get('encounter_prompt', '')
        }
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in encounter file: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading encounter: {e}"
        )