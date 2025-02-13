import os
import shutil
import uvicorn
import json
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Aktueller Dateipfad (__file__) und das src-Verzeichnis ermitteln
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))

# Verzeichnis für YAML-Dateien und statische Dateien definieren
MAPS_ROOT_DIR = os.path.join(PROJECT_DIR, 'maps')
STATIC_FILES_DIR = os.path.join(BASE_DIR, 'static')


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
    """Speichert eine hochgeladene Datei im angegebenen Verzeichnis"""
    # Path to the template.json file in the current directory
    template_path = os.path.join(BASE_DIR, "template.json")
     # Verify the template.json exists
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="template.json not found")
    # Directory structure to be created
    map_dir = os.path.join(MAPS_ROOT_DIR, map_name)
    soundfx_dir = os.path.join(map_dir, "soundfx")
    

    try:
        os.makedirs(soundfx_dir, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directories: {e}")
    
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
    """Listet alle Sound-Dateien im definierten Verzeichnis auf"""
    try:
        sound_dir = os.path.join(MAPS_ROOT_DIR, map_name, "soundfx")
        files = [f for f in os.listdir(sound_dir) if f.endswith((".mp3", ".wav"))]
        return files
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Verzeichnis nicht gefunden")


@app.get("/api/v1/sounds/{map_name}/{file_name}")
async def get_sound_file(map_name: str, file_name: str):
    """Lädt eine Sound-Datei anhand ihres Namens"""
    file_location = os.path.join(MAPS_ROOT_DIR, map_name, "soundfx", file_name)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    # Return the file as a response with the appropriate MIME type for MP3
    return FileResponse(file_location, media_type="audio/mpeg", filename=file_name)


# Static files für /editor - liefert Dateien aus dem src/static Verzeichnis
#app.mount("/editor", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Server direkt im Python-File starten
if __name__ == "__main__":
    # Starte den FastAPI-Server auf dem Standard-Port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
