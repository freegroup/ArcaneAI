"""
FastAPI Web Server for the text adventure game.
Provides REST API and web interface.

Run with: python server.py
Or: uvicorn server:app --host 0.0.0.0 --port 9000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
import secrets
import os
import asyncio

from dotenv import load_dotenv
load_dotenv()

from session import GameSession


# Configuration
BASE_URI = os.getenv("BASE_URI", "")  # Empty for local, "/game" for production
PORT = int(os.getenv("PORT", "9000"))
SAME_SITE_VALUE = os.getenv("SAME_SITE", "Lax")  # "Lax" for local, "None" for cross-origin

VALID_USERNAME = os.getenv("USERNAME", "user")
VALID_PASSWORD = os.getenv("PASSWORD", "pass")

# Initialize FastAPI
app = FastAPI(title="Text Adventure Game", version="2.0.0", root_path=BASE_URI)

# Templates and static files
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store
session_store: Dict[str, GameSession] = {}


# Pydantic models
class ChatMessage(BaseModel):
    text: str


class LoginData(BaseModel):
    username: str
    password: str


def create_session(session_id: str) -> GameSession:
    """Create a new game session."""
    definition_path = BASE_DIR / "game_definition_tipsy_full.json"
    
    # Session creates everything now!
    # Note: message_queue will be set when WebSocket connects
    from messaging import MockMessageQueue
    return GameSession(
        session_id=session_id,
        definition_path=str(definition_path),
        message_queue=MockMessageQueue()  # Placeholder until WebSocket connects
    )


def get_or_create_session(request: Request, response: Response) -> GameSession:
    """Get existing session or create new one."""
    session_id = request.cookies.get("session_id")
    
    print(f"[SESSION DEBUG] Cookie session_id: {session_id}")
    print(f"[SESSION DEBUG] Sessions in store: {list(session_store.keys())}")
    
    if session_id and session_id in session_store:
        print(f"[SESSION DEBUG] Found existing session: {session_id}")
        return session_store[session_id]
    
    # Create new session
    if not session_id:
        session_id = str(uuid4())
    
    print(f"[SESSION DEBUG] Creating NEW session: {session_id}")
    session = create_session(session_id)
    session_store[session_id] = session
    response.set_cookie("session_id", session_id, httponly=True, samesite=SAME_SITE_VALUE)
    
    return session


# Routes
@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    """Show login page."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "BASE_URI": BASE_URI
    })


@app.post("/login_post", name="login")
async def login(request: Request, data: LoginData, response: Response):
    """Handle login."""
    if not (secrets.compare_digest(data.username, VALID_USERNAME) and 
            secrets.compare_digest(data.password, VALID_PASSWORD)):
        return JSONResponse({"error": "Invalid username or password"}, status_code=400)
    
    # Set authentication cookie
    response = RedirectResponse(
        url=request.url_for("ui"),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
    response.set_cookie("authenticated", "yes", httponly=True, samesite=SAME_SITE_VALUE)
    return response


@app.get("/ui", response_class=HTMLResponse, name="ui")
async def ui(request: Request, response: Response):
    """Show game UI."""
    # Check authentication
    if request.cookies.get("authenticated") != "yes":
        return RedirectResponse(url=request.url_for("login_page"))
    
    return templates.TemplateResponse("index_simple.html", {
        "request": request,
        "BASE_URI": BASE_URI
    })


@app.get("/websocket/connect", name="websocket_connect")
async def websocket_connect(request: Request):
    """
    Create WebSocket token for client.
    Client calls this before connecting to WebSocket.
    """
    # Check authentication
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Get or create session
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
    
    # Generate WebSocket token
    ws_token = secrets.token_urlsafe(32)
    
    # Create or get session
    if session_id not in session_store:
        session = create_session(session_id)
        session_store[session_id] = session
    else:
        session = session_store[session_id]
    
    # Store token in session
    session.ws_token = ws_token
    
    # Return token and set cookie
    response = JSONResponse({"token": ws_token})
    response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    
    return response


@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage):
    """Process chat message."""
    # Check authentication
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Get or create session
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in session_store:
        session = session_store[session_id]
    else:
        # Create new session
        if not session_id:
            session_id = str(uuid4())
        session = create_session(session_id)
        session_store[session_id] = session
    
    # Handle special commands
    text = data.text.strip()
    
    if text.lower() == "start":
        # Restart game
        session_store[session_id] = create_session(session_id)
        session = session_store[session_id]
        response_text = session.game_engine.controller.start_game()
    else:
        # Process normal input
        session.update_activity()
        response_text = session.game_engine.controller.process_input(text)
    
    # Flush WebSocket messages if using WebSocket queue
    if hasattr(session.message_queue, 'flush'):
        await session.message_queue.flush()
    
    # Get buffered messages from message queue (for REST fallback)
    messages = []
    if hasattr(session.message_queue, 'get_messages'):
        messages = session.message_queue.get_messages()
    
    # Create response with cookie and session_id in body
    json_response = JSONResponse({
        "response": response_text,
        "state": session.game_engine.state_engine.get_current_state().name,
        "inventory": session.inventory.to_dict(),
        "messages": messages,  # All queued messages (inventory_update, etc.)
        "session_id": session_id  # Include session_id in response for WebSocket
    })
    # Set cookie without httponly so JavaScript can read it
    json_response.set_cookie("session_id", session_id, httponly=False, samesite=SAME_SITE_VALUE)
    
    return json_response


@app.get("/api/state", name="get_state")
async def get_state(request: Request, response: Response):
    """Get current game state."""
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    session = get_or_create_session(request, response)
    
    return JSONResponse({
        "state": session.game_engine.state_engine.get_current_state().name,
        "inventory": session.inventory.to_dict()
    })


@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time game updates.
    Client connects with token from /websocket/connect.
    """
    await websocket.accept()
    
    try:
        # Find session by token
        session = None
        session_id = None
        for sid, sess in session_store.items():
            if sess.ws_token == token:
                session = sess
                session_id = sid
                break
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Invalid token"}
            })
            await websocket.close()
            return
        
        from messaging import WebSocketMessageQueue
        import asyncio
        
        old_queue = session.message_queue
        loop = asyncio.get_event_loop()
        session.message_queue = WebSocketMessageQueue(websocket, loop=loop)
        
        print(f"[WEBSOCKET] Client connected for session {session_id}")
        
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "data": {
                "state": session.game_engine.state_engine.get_current_state().name,
                "inventory": session.inventory.to_dict()
            }
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong)
                message = await websocket.receive_json()
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                print(f"[WEBSOCKET] Client disconnected for session {session_id}")
                # Restore old message queue
                session.message_queue = old_queue
                break
                
    except Exception as e:
        print(f"[WEBSOCKET ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on http://0.0.0.0:{PORT}{BASE_URI}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)