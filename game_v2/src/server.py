"""
FastAPI Web Server for the text adventure game.
Provides REST API and web interface.

Run with: python server.py
Or: uvicorn server:app --host 0.0.0.0 --port 9000
"""
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4
import secrets
import os

from fastapi import FastAPI, HTTPException, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from session import GameSession
from config_loader import load_config
from audio import WebSocketSink
from sound import WebJukebox
from messaging import WebSocketMessageQueue

# Base directory for game_v2
GAME_V2_DIR: Path = Path(__file__).parent.parent

# Load config once at startup
CONFIG = load_config()

# Configuration from environment
BASE_URI = os.getenv("BASE_URI", "")
PORT = int(os.getenv("PORT", "9000"))
SAME_SITE_VALUE = os.getenv("SAME_SITE", "Lax")
VALID_USERNAME = os.getenv("USERNAME", "user")
VALID_PASSWORD = os.getenv("PASSWORD", "pass")

# Initialize FastAPI
app = FastAPI(title="Text Adventure Game", version="2.0.0", root_path=BASE_URI)

# Templates and static files
templates = Jinja2Templates(directory=str(GAME_V2_DIR / "templates"))
app.mount("/assets", StaticFiles(directory=str(GAME_V2_DIR / "static")), name="static")
app.mount("/soundfx", StaticFiles(directory=str(GAME_V2_DIR / "soundfx")), name="soundfx")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store and token mapping
session_store: Dict[str, GameSession] = {}
token_to_session: Dict[str, str] = {}  # ws_token -> session_id


# Pydantic models
class ChatMessage(BaseModel):
    text: str


class LoginData(BaseModel):
    username: str
    password: str


# ============ Session Management ============

def create_session(session_id: str) -> GameSession:
    """Create a new game session.
    Game definition is loaded from config.yaml (maps_directory + game_name).
    """
    return GameSession(
        session_id=session_id,
        config=CONFIG,
        audio_sink=WebSocketSink(),
        jukebox=WebJukebox()
    )


def get_session(session_id: Optional[str]) -> Optional[GameSession]:
    """Get session by ID if it exists."""
    if session_id and session_id in session_store:
        return session_store[session_id]
    return None


def get_or_create_session(session_id: Optional[str]) -> tuple[GameSession, str]:
    """Get existing session or create new one. Returns (session, session_id)."""
    if session_id and session_id in session_store:
        return session_store[session_id], session_id
    
    # Create new session
    if not session_id:
        session_id = str(uuid4())
    
    session = create_session(session_id)
    session_store[session_id] = session
    return session, session_id


def require_auth(request: Request) -> None:
    """Check if user is authenticated, raise HTTPException if not."""
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


# ============ Routes ============

@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    """Show login page."""
    return templates.TemplateResponse("login.html", {"request": request, "BASE_URI": BASE_URI})


@app.post("/login_post", name="login")
async def login(request: Request, data: LoginData):
    """Handle login."""
    if not (secrets.compare_digest(data.username, VALID_USERNAME) and 
            secrets.compare_digest(data.password, VALID_PASSWORD)):
        return JSONResponse({"error": "Invalid username or password"}, status_code=400)
    
    response = RedirectResponse(url=request.url_for("ui"), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie("authenticated", "yes", httponly=True, samesite=SAME_SITE_VALUE)
    return response


@app.get("/ui", response_class=HTMLResponse, name="ui")
async def ui(request: Request):
    """Show game UI."""
    if request.cookies.get("authenticated") != "yes":
        return RedirectResponse(url=request.url_for("login_page"))
    return templates.TemplateResponse("index.html", {"request": request, "BASE_URI": BASE_URI})


@app.get("/websocket/connect", name="websocket_connect")
async def websocket_connect(request: Request):
    """Create WebSocket token for client."""
    require_auth(request)
    
    session_id = request.cookies.get("session_id")
    session, session_id = get_or_create_session(session_id)
    
    # Generate and store WebSocket token
    ws_token = secrets.token_urlsafe(32)
    session.ws_token = ws_token
    token_to_session[ws_token] = session_id
    
    response = JSONResponse({"token": ws_token})
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    return response


@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage):
    """Process chat message."""
    require_auth(request)
    
    session_id = request.cookies.get("session_id")
    session, session_id = get_or_create_session(session_id)
    
    text = data.text.strip()
    
    if text.lower() == "start":
        # Restart game - preserve WebSocket state
        old_ws_token = session.ws_token
        old_message_queue = session.message_queue
        session = create_session(session_id)
        session_store[session_id] = session
        session.ws_token = old_ws_token
        session.message_queue = old_message_queue
        response_text = session.game_engine.controller.start_game()
    else:
        session.update_activity()
        response_text = session.game_engine.controller.process_input(text)
    
    # Flush WebSocket messages if connected
    if hasattr(session.message_queue, 'flush'):
        await session.message_queue.flush()
    
    # Get buffered messages (for REST fallback)
    messages = []
    if hasattr(session.message_queue, 'get_messages'):
        messages = session.message_queue.get_messages()
    
    response = JSONResponse({
        "response": response_text,
        "state": session.game_engine.state_engine.get_current_state().name,
        "inventory": session.game_engine.inventory.to_dict(),
        "messages": messages,
        "session_id": session_id
    })
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    return response


@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time game updates."""
    import asyncio
    
    await websocket.accept()
    
    # Find session by token (O(1) lookup)
    session_id = token_to_session.get(token)
    session = session_store.get(session_id) if session_id else None
    
    if not session:
        await websocket.send_json({"type": "error", "data": {"message": "Invalid token"}})
        await websocket.close()
        return
    
    # Set up WebSocket message queue with event loop
    # This allows other threads (like audio playback) to send messages
    old_queue = session.message_queue
    loop = asyncio.get_event_loop()
    session.message_queue = WebSocketMessageQueue(websocket, loop=loop)
    
    print(f"[WEBSOCKET] Client connected for session {session_id}")
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "data": {
                "state": session.game_engine.state_engine.get_current_state().name,
                "inventory": session.game_engine.inventory.to_dict()
            }
        })
        
        # Keep connection alive
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print(f"[WEBSOCKET] Client disconnected for session {session_id}")
    except Exception as e:
        print(f"[WEBSOCKET ERROR] {e}")
    finally:
        # Restore old message queue
        session.message_queue = old_queue
        # Clean up token mapping
        if token in token_to_session:
            del token_to_session[token]


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on http://0.0.0.0:{PORT}{BASE_URI}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)