import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Load configuration using EditorConfig
BASE_DIR = Path(__file__).parent

# Import local config_loader
from config_loader import EditorConfig

# Import route modules
from routes import games_routes, game_routes, sounds_routes, text_improver_routes, encounters_routes

# Load config
editor_config = EditorConfig()

# Get directories from config (already validated and resolved)
MAPS_ROOT_DIR = str(editor_config.maps_directory)
SOUNDFX_ROOT_DIR = str(editor_config.soundfx_directory)

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

# Initialize route modules with configuration
games_routes.init_routes(MAPS_ROOT_DIR)
game_routes.init_routes(MAPS_ROOT_DIR)
sounds_routes.init_routes(MAPS_ROOT_DIR, SOUNDFX_ROOT_DIR)
encounters_routes.init_routes(MAPS_ROOT_DIR)

# Include routers
app.include_router(games_routes.router)
app.include_router(game_routes.router)
app.include_router(sounds_routes.router)
app.include_router(text_improver_routes.router)
app.include_router(encounters_routes.router)


# Static files für /editor - liefert Dateien aus dem src/static Verzeichnis
#app.mount("/editor", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Server direkt im Python-File starten
if __name__ == "__main__":
    # Starte den FastAPI-Server auf dem Standard-Port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
