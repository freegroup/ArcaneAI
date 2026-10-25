"""
FastAPI Web Server for the text adventure game.
Provides REST API and web interface.

Run with: python server.py
Or: uvicorn server:app --host 0.0.0.0 --port 9000
"""
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4
import asyncio
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
from session_store import SessionStore
from config_loader import load_config
from audio import WebSocketSink
from sound import WebJukebox
from messaging import WebSocketMessageQueue

# Base directory for game
GAME_DIR: Path = Path(__file__).parent.parent

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
templates = Jinja2Templates(directory=str(GAME_DIR / "templates"))
app.mount("/assets", StaticFiles(directory=str(GAME_DIR / "static")), name="static")
app.mount("/soundfx", StaticFiles(directory=str(GAME_DIR / "soundfx")), name="soundfx")

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
auth_tokens: set[str] = set()  # random tokens handed out at login (cookie "auth")

# Game progress survives a server restart: one JSON file per session id.
saved_games = SessionStore(GAME_DIR.parent / "sessions" / "web")


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


def valid_session_id(session_id: Optional[str]) -> bool:
    """Session ids are UUIDs we handed out — they name the save file, so check them."""
    try:
        return session_id is not None and str(UUID(session_id)) == session_id
    except ValueError:
        return False


def get_or_create_session(session_id: Optional[str]) -> tuple[GameSession, str]:
    """Get existing session (from memory or its save file) or create new one. Returns (session, session_id)."""
    if not valid_session_id(session_id):
        session_id = str(uuid4())
    if session_id in session_store:
        return session_store[session_id], session_id

    session = create_session(session_id)
    saved = saved_games.load(session_id)
    if saved:
        session.restore_from_dict(saved)
        print(f"[SESSION] Restored saved game {session_id}")
    session_store[session_id] = session
    return session, session_id


def save_game(session: GameSession) -> None:
    saved_games.save(session.session_id, session.to_dict())


def game_state(session: GameSession) -> dict:
    """What the client shows: room, inventory, possible functions, whether the game is over."""
    engine = session.game_engine
    state = engine.state_engine.get_current_state()
    decision = engine.controller.decision
    return {
        "state": state.name,
        "inventory": engine.inventory.to_dict(),
        "game_over": state.is_end,
        # For debugging: exactly the functions stage 1 is offered right now.
        "functions": [
            {"name": f.name, "builtin": decision.builtins.by_name(f.name) is not None}
            for f in decision.prompts.functions(engine)
        ],
    }


def is_authenticated(request: Request) -> bool:
    """True if the request carries an auth token handed out at login."""
    return request.cookies.get("auth") in auth_tokens


def require_auth(request: Request) -> None:
    """Check if user is authenticated, raise HTTPException if not."""
    if not is_authenticated(request):
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
    
    token = secrets.token_urlsafe(32)
    auth_tokens.add(token)
    response = RedirectResponse(url=request.url_for("ui"), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie("auth", token, httponly=True, samesite=SAME_SITE_VALUE)
    return response


@app.get("/ui", response_class=HTMLResponse, name="ui")
async def ui(request: Request):
    """Show game UI."""
    if not is_authenticated(request):
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


@app.get("/api/game", name="game")
async def game(request: Request):
    """The running game (if any): history, room, inventory and the intro text."""
    require_auth(request)

    session, session_id = get_or_create_session(request.cookies.get("session_id"))
    entries = session.game_engine.controller.history.entries
    response = JSONResponse({
        "running": len(entries) > 0,
        # The welcome's input is the instruction to the model, not something the player said.
        "history": [
            {"user": None if e.is_welcome else e.user_input, "assistant": e.llm_response}
            for e in entries
        ],
        "intro": session.game_engine.game_data.get("help_text", ""),
        **game_state(session),
    })
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    return response


@app.post("/api/restart", name="restart")
async def restart(request: Request):
    """Start the game from the beginning."""
    require_auth(request)

    session_id = request.cookies.get("session_id")
    old_session, session_id = get_or_create_session(session_id)
    # The old game must stop talking (blocks until its speech thread ends)
    await asyncio.to_thread(old_session.game_engine.controller.stop_speaking)
    # Fresh game, but keep the WebSocket connection
    session = create_session(session_id)
    session.ws_token = old_session.ws_token
    session.message_queue = old_session.message_queue
    session_store[session_id] = session

    # LLM calls block — run them in a worker thread so other players
    # and the WebSocket keep being served meanwhile.
    response_text = await asyncio.to_thread(session.game_engine.controller.start_game)
    save_game(session)

    response = JSONResponse({"response": response_text, **game_state(session)})
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    return response


@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage):
    """Process one player input."""
    require_auth(request)

    session, session_id = get_or_create_session(request.cookies.get("session_id"))
    session.update_activity()
    result = await asyncio.to_thread(session.game_engine.controller.process_input, data.text.strip())
    save_game(session)

    response = JSONResponse({"response": result["response"], **game_state(session)})
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    return response


@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time game updates."""
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
    loop = asyncio.get_running_loop()
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

        # Reconnect to a running game: the room's ambience plays again
        if session.game_engine.controller.history.entries:
            session.game_engine.controller.send_ambient()
        
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