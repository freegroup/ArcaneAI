import os
import shutil
import uvicorn
import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load configuration using EditorConfig
BASE_DIR = Path(__file__).parent

# Import local config_loader
from config_loader import EditorConfig

# Load config
editor_config = EditorConfig()

# Get directories from config (already validated and resolved)
MAPS_ROOT_DIR = str(editor_config.maps_directory)
SOUNDFX_ROOT_DIR = str(editor_config.soundfx_directory)
STATIC_FILES_DIR = str(BASE_DIR / 'static')

print(f"[EDITOR CONFIG] Maps directory: {MAPS_ROOT_DIR}")
print(f"[EDITOR CONFIG] SoundFX directory: {SOUNDFX_ROOT_DIR}")


# FastAPI App initialisieren
app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:8080",  # Vue.js dev server
    "http://0.0.0.0:8080",    # Vue.js on 0.0.0.0 (alternative address)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Define the no-cache middleware
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
app.add_middleware(NoCacheMiddleware)


@app.post("/api/v1/maps/{map_name}")
async def create_file(map_name: str):
    """
    Erstellt eine neue Map aus dem Template.
    Note: soundfx sind zentral und werden NICHT mehr pro Map erstellt.
    """
    # Path to the template.json file in the current directory
    template_path = os.path.join(BASE_DIR, "template.json")
    
    # Verify the template.json exists
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="template.json not found")
    
    # Create map directory (no soundfx subdirectory - sounds are central)
    map_dir = os.path.join(MAPS_ROOT_DIR, map_name)
    
    try:
        os.makedirs(map_dir, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create map directory: {e}")
    
    # Copy template to map directory
    map_file_path = os.path.join(map_dir, "index.json")
    try:
        shutil.copy(template_path, map_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy template.json: {e}")

    return FileResponse(map_file_path)



@app.put("/api/v1/maps/")
async def save_file(file: UploadFile = File(...)):
    """Speichert eine hochgeladene Datei im angegebenen Verzeichnis"""
    map_name, suffix = os.path.splitext(file.filename)
    file_location = os.path.join(MAPS_ROOT_DIR, map_name, f"index{suffix}")

    try:
        with open(file_location, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {e}")

    return {"message": f"Datei {file.filename} gespeichert unter {file_location}"}


@app.get("/api/v1/maps/")
async def list_files() -> List[str]:
    """Listet alle Unterverzeichnisse im definierten Verzeichnis auf"""
    try:
        # Alle Einträge im Verzeichnis prüfen, ob sie Unterverzeichnisse sind
        directories = [
            d for d in os.listdir(MAPS_ROOT_DIR) 
            if os.path.isdir(os.path.join(MAPS_ROOT_DIR, d))
        ]
        return directories
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Directory not found")


@app.get("/api/v1/maps/{map_name}")
async def get_file(map_name: str):
    """Lädt eine JSON-Datei anhand ihres Namens"""
    file_location = os.path.join(MAPS_ROOT_DIR, map_name,  "index.json")
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    return FileResponse(file_location)


@app.get("/api/v1/sounds/{map_name}")
async def list_sound_files(map_name: str) -> List[str]:
    """
    Listet alle Sound-Dateien aus dem zentralen soundfx Verzeichnis (global/)
    und aus dem Map-spezifischen sounds Verzeichnis (map/).
    
    Returns:
        Liste von Pfaden mit Prefix:
        - global/... für zentrale Sound-Dateien
        - map/... für Map-spezifische Sound-Dateien
    """
    files = []
    
    # 1. Globale Sounds aus dem zentralen soundfx Verzeichnis
    try:
        if os.path.exists(SOUNDFX_ROOT_DIR):
            for root, dirs, filenames in os.walk(SOUNDFX_ROOT_DIR):
                for filename in filenames:
                    if filename.endswith((".mp3", ".wav", ".ogg")):
                        # Get relative path from soundfx root
                        rel_path = os.path.relpath(os.path.join(root, filename), SOUNDFX_ROOT_DIR)
                        files.append(f"global/{rel_path}")
    except Exception as e:
        print(f"[WARNING] Could not read global soundfx directory: {e}")
    
    # 2. Map-spezifische Sounds aus dem Map-Verzeichnis (soundfx Ordner)
    map_sounds_dir = os.path.join(MAPS_ROOT_DIR, map_name, "soundfx")
    try:
        if os.path.exists(map_sounds_dir):
            for root, dirs, filenames in os.walk(map_sounds_dir):
                for filename in filenames:
                    if filename.endswith((".mp3", ".wav", ".ogg")):
                        # Get relative path from map soundfx root
                        rel_path = os.path.relpath(os.path.join(root, filename), map_sounds_dir)
                        files.append(f"map/{rel_path}")
    except Exception as e:
        print(f"[WARNING] Could not read map soundfx directory for '{map_name}': {e}")
    
    return sorted(files)


@app.get("/api/v1/sounds/{map_name}/{file_name:path}")
async def get_sound_file(map_name: str, file_name: str):
    """
    Lädt eine Sound-Datei basierend auf dem Prefix:
    - global/... -> aus dem zentralen soundfx Verzeichnis
    - map/... -> aus dem Map-spezifischen sounds Verzeichnis
    
    file_name kann Unterverzeichnisse enthalten (z.B. "global/ambient/wind.wav")
    """
    # Determine source based on prefix
    if file_name.startswith("global/"):
        # Remove "global/" prefix and get from central soundfx directory
        relative_path = file_name[7:]  # len("global/") = 7
        file_location = os.path.join(SOUNDFX_ROOT_DIR, relative_path)
    elif file_name.startswith("map/"):
        # Remove "map/" prefix and get from map-specific soundfx directory
        relative_path = file_name[4:]  # len("map/") = 4
        file_location = os.path.join(MAPS_ROOT_DIR, map_name, "soundfx", relative_path)
    else:
        # Fallback: assume it's from map soundfx (backwards compatibility - nur Dateiname)
        file_location = os.path.join(MAPS_ROOT_DIR, map_name, "soundfx", file_name)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Sound file not found: {file_name}")
    
    # Determine media type based on extension
    ext = os.path.splitext(file_name)[1].lower()
    media_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg'
    }
    media_type = media_types.get(ext, 'audio/mpeg')
    
    return FileResponse(file_location, media_type=media_type, filename=os.path.basename(file_name))


# Static files für /editor - liefert Dateien aus dem src/static Verzeichnis
#app.mount("/editor", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Server direkt im Python-File starten
if __name__ == "__main__":
    # Starte den FastAPI-Server auf dem Standard-Port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
