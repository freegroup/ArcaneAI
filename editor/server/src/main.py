import os
import yaml
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import uvicorn

# Aktueller Dateipfad (__file__) und das src-Verzeichnis ermitteln
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Verzeichnis für YAML-Dateien und statische Dateien definieren
CONVERSATIONS_FILE_DIR = os.path.join(BASE_DIR, 'conversations')
STATIC_FILES_DIR = os.path.join(BASE_DIR, 'static')


# Stelle sicher, dass das conversations-Verzeichnis existiert
os.makedirs(CONVERSATIONS_FILE_DIR, exist_ok=True)

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



# /api/v1/conversations route Gruppe
@app.post("/api/v1/conversations/")
async def save_yaml_file(file: UploadFile = File(...)):
    """Speichert eine hochgeladene YAML-Datei im angegebenen Verzeichnis"""
    file_location = os.path.join(CONVERSATIONS_FILE_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"message": f"Datei {file.filename} gespeichert"}

@app.get("/api/v1/conversations/")
async def list_yaml_files() -> List[str]:
    """Listet alle YAML-Dateien im definierten Verzeichnis auf"""
    try:
        files = [f for f in os.listdir(CONVERSATIONS_FILE_DIR) if f.endswith(".json")]
        return files
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Verzeichnis nicht gefunden")

@app.get("/api/v1/conversations/{file_name}")
async def get_yaml_file(file_name: str):
    """Lädt eine YAML-Datei anhand ihres Namens"""
    file_location = os.path.join(CONVERSATIONS_FILE_DIR, file_name)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    return FileResponse(file_location)

@app.get("/api/v1/sounds/")
async def list_sound_files() -> List[str]:
    """Listet alle Sound-Dateien im definierten Verzeichnis auf"""
    try:
        files = [f for f in os.listdir(CONVERSATIONS_FILE_DIR) if f.endswith((".mp3", ".wav"))]
        return files
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Verzeichnis nicht gefunden")


@app.get("/api/v1/sounds/{file_name}")
async def get_mp3_file(file_name: str):
    """Lädt eine MP3-Datei anhand ihres Namens"""
    file_location = os.path.join(CONVERSATIONS_FILE_DIR, file_name)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    
    # Return the file as a response with the appropriate MIME type for MP3
    return FileResponse(file_location, media_type="audio/mpeg", filename=file_name)


# Static files für /editor - liefert Dateien aus dem src/static Verzeichnis
app.mount("/editor", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Server direkt im Python-File starten
if __name__ == "__main__":
    # Starte den FastAPI-Server auf dem Standard-Port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
