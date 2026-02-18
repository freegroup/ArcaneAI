"""
Routes for managing encounters within a game.
Encounters are stored in the 'encounter' subdirectory of each game.
"""
import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/game", tags=["encounters"])

# These will be set by main.py
MAPS_ROOT_DIR = None

# Constants
ENCOUNTERS_DIR = "encounters"  # Subdirectory name for encounters within each game

def init_routes(maps_dir: str):
    """Initialize routes with configuration."""
    global MAPS_ROOT_DIR
    MAPS_ROOT_DIR = maps_dir


@router.get("/{game_name}/encounters", response_model=List[str])
async def list_encounters(game_name: str):
    """List all encounters for a specific game."""
    encounters_dir = os.path.join(MAPS_ROOT_DIR, game_name, ENCOUNTERS_DIR)
    
    if not os.path.exists(encounters_dir):
        # Return empty list if encounter directory doesn't exist yet
        return []
    
    try:
        # List all .json files in the encounter directory
        files = [
            f[:-5]  # Remove .json extension
            for f in os.listdir(encounters_dir)
            if f.endswith('.json')
        ]
        return sorted(files)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing encounters: {e}"
        )


@router.get("/{game_name}/encounters/{encounter_name}")
async def get_encounter(game_name: str, encounter_name: str):
    """Get a specific encounter file."""
    encounter_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        ENCOUNTERS_DIR,
        f"{encounter_name}.json"
    )
    
    if not os.path.exists(encounter_file):
        raise HTTPException(
            status_code=404,
            detail=f"Encounter '{encounter_name}' not found in game '{game_name}'"
        )
    
    return FileResponse(encounter_file)


@router.post("/{game_name}/encounters/{encounter_name}")
async def create_encounter(game_name: str, encounter_name: str, file: UploadFile = File(...)):
    """Create a new encounter for a game."""
    # Ensure game exists
    game_dir = os.path.join(MAPS_ROOT_DIR, game_name)
    if not os.path.exists(game_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Game '{game_name}' not found"
        )
    
    # Create encounter directory if it doesn't exist
    encounters_dir = os.path.join(game_dir, ENCOUNTERS_DIR)
    os.makedirs(encounters_dir, exist_ok=True)
    
    # Check if encounter already exists
    encounter_file = os.path.join(encounters_dir, f"{encounter_name}.json")
    if os.path.exists(encounter_file):
        raise HTTPException(
            status_code=409,
            detail=f"Encounter '{encounter_name}' already exists"
        )
    
    try:
        # Save the encounter file
        with open(encounter_file, "wb") as f:
            f.write(await file.read())
        return {"message": f"Encounter '{encounter_name}' created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create encounter: {e}"
        )


@router.put("/{game_name}/encounters/{encounter_name}")
async def update_encounter(game_name: str, encounter_name: str, file: UploadFile = File(...)):
    """Update an existing encounter."""
    encounter_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        ENCOUNTERS_DIR,
        f"{encounter_name}.json"
    )
    
    if not os.path.exists(encounter_file):
        raise HTTPException(
            status_code=404,
            detail=f"Encounter '{encounter_name}' not found"
        )
    
    try:
        with open(encounter_file, "wb") as f:
            f.write(await file.read())
        return {"message": f"Encounter '{encounter_name}' updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update encounter: {e}"
        )


@router.delete("/{game_name}/encounters/{encounter_name}")
async def delete_encounter(game_name: str, encounter_name: str):
    """Delete an encounter."""
    encounter_file = os.path.join(
        MAPS_ROOT_DIR,
        game_name,
        ENCOUNTERS_DIR,
        f"{encounter_name}.json"
    )
    
    if not os.path.exists(encounter_file):
        raise HTTPException(
            status_code=404,
            detail=f"Encounter '{encounter_name}' not found"
        )
    
    try:
        os.remove(encounter_file)
        return {"message": f"Encounter '{encounter_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete encounter: {e}"
        )