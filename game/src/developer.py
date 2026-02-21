"""
Developer Server - REST API for Editor Integration.
Single-session, hot-reload capable server for development workflow.

Endpoints:
    POST /chat         - Send user input and receive response
    POST /setState     - Set current game state by name
    POST /setInventory - Set inventory item value
    POST /reload       - Hot-reload game definition (preserves state/inventory)
    POST /reset        - Full reset (reload + reset state/inventory)
    GET  /status       - Get current session status

Usage:
    cd game/src && python developer.py
    
Port: 9000 (same as server.py - they never run simultaneously)
"""
import json
import sys
import uvicorn
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from session import GameSession
from config_loader import GameConfig, load_config
from audio import PyAudioSink
from sound import LocalJukebox


# === Pydantic Models ===

class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response body for /chat endpoint."""
    response: str
    current_state: str
    inventory: Dict[str, Any]
    executed_action: Optional[str] = None


class SetStateRequest(BaseModel):
    """Request body for /setState endpoint.
    
    If model_json is provided, the game engine will be reinitialized with
    this in-memory data, allowing testing of unsaved changes from the editor.
    """
    model_config = {"protected_namespaces": ()}  # Allow "model_" prefix in field names
    
    state_name: str
    model_json: Optional[Dict[str, Any]] = None  # Optional: model data for hot-reload
    config_json: Optional[Dict[str, Any]] = None  # Optional: config data for hot-reload


class SetInventoryRequest(BaseModel):
    """Request body for /setInventory endpoint."""
    key: str
    value: Any


class StatusResponse(BaseModel):
    """Response body for /status endpoint."""
    current_state: str
    inventory: Dict[str, Any]
    available_states: list[str]
    available_actions: list[str]
    game_started: bool


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str


# === Global Session ===

# Single session for developer mode
_session: Optional[GameSession] = None


def get_session() -> GameSession:
    """Get the global session, raising error if not initialized."""
    if _session is None:
        raise HTTPException(status_code=500, detail="Session not initialized")
    return _session


def create_session(config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Create a new game session.
    
    Args:
        config: Optional config dict. If not provided, loads from disk.
                In developer mode, config usually comes with setState call.
    """
    global _session
    
    print("[DEV] Creating new game session...")
    
    # Use provided config or load from disk as fallback
    if config is None:
        config = load_config()
        print(f"[DEV] Config loaded from disk")
    else:
        print(f"[DEV] Using provided config")
    
    # Create session with audio/jukebox
    _session = GameSession(
        session_id="developer",
        config=config,
        audio_sink=PyAudioSink(sample_rate=24000),
        jukebox=LocalJukebox(config=config)
    )
    
    print(f"[DEV] Session created. Game: {config.get('game_name', 'unknown')}")
    return _session


def reload_game_definition() -> GameSession:
    """
    Hot-reload game definition while preserving state and inventory.
    
    Returns:
        New session with preserved state/inventory
    """
    global _session
    
    old_session = _session
    
    # Preserve state and inventory if session exists
    preserved_state = None
    preserved_inventory = {}
    
    if old_session is not None:
        preserved_state = old_session.game_engine.state_engine.get_current_state().name
        preserved_inventory = old_session.game_engine.inventory.to_dict()
        print(f"[DEV] Preserving state: {preserved_state}")
        print(f"[DEV] Preserving inventory: {preserved_inventory}")
    
    # Create new session (reloads game definition)
    new_session = create_session()
    
    # Restore state if valid
    if preserved_state:
        try:
            states = new_session.game_engine.state_engine.states
            if preserved_state in states:
                new_session.game_engine.state_engine.current_state = preserved_state
                print(f"[DEV] Restored state: {preserved_state}")
            else:
                print(f"[DEV] State '{preserved_state}' not found in new definition, using initial state")
        except Exception as e:
            print(f"[DEV] Could not restore state: {e}")
    
    # Restore inventory
    if preserved_inventory:
        for key, value in preserved_inventory.items():
            try:
                new_session.game_engine.inventory.set(key, value)
            except Exception as e:
                print(f"[DEV] Could not restore inventory item '{key}': {e}")
        print(f"[DEV] Restored {len(preserved_inventory)} inventory items")
    
    _session = new_session
    
    return new_session


# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - NO session created on startup.
    
    Session is created lazily when first setState is called with model/config.
    This avoids loading from disk since editor always sends model/config.
    """
    print("[DEV] Developer Server starting...")
    print("[DEV] Waiting for setState call from editor...")
    print("[DEV] Ready for connections on port 9000")
    yield
    print("[DEV] Developer Server shutting down...")


# === FastAPI App ===

app = FastAPI(
    title="Dungeon Developer Server",
    description="REST API for Editor Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Endpoints ===

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send user input to game engine and receive response.
    No start_game needed - just process the input directly.
    """
    session = get_session()
    
    # Process input directly - returns dict with response and executed_action
    result = session.game_engine.process_input(request.message)
    
    return ChatResponse(
        response=result['response'],
        current_state=session.game_engine.state_engine.get_current_state().name,
        inventory=session.game_engine.inventory.to_dict(),
        executed_action=result.get('executed_action')
    )


@app.post("/setState", response_model=SuccessResponse)
async def set_state(request: SetStateRequest) -> SuccessResponse:
    """
    Set the current game state by name.
    Used by Editor to jump to specific states during development.
    
    model_json and config_json are expected from editor - this initializes
    or reinitializes the game engine with the current editor state.
    
    Flow: Load model/config → Set state → Clear history → Wait for chat
    """
    global _session
    
    # Log the setState call
    print(f"[DEV] === setState called ===")
    print(f"[DEV]   state_name: {request.state_name}")
    print(f"[DEV]   model_json: {'provided' if request.model_json else 'not provided'}")
    print(f"[DEV]   config_json: {'provided' if request.config_json else 'not provided'}")
    
    # If no session yet, create one (lazy initialization)
    if _session is None:
        if request.config_json is not None:
            create_session(config=request.config_json)
        else:
            # Fallback: load from disk if no config provided
            create_session()
    
    session = get_session()
    
    # Reinitialize game engine with provided model/config
    if request.model_json is not None:
        print("[DEV] Hot-reloading from in-memory model data...")
        session.game_engine.reinitialize_from_memory(
            model_data=request.model_json,
            config_data=request.config_json
        )
        print("[DEV] Model and config loaded successfully")
    
    # Clear chat history to ensure fresh start when jumping to a state
    session.game_engine.controller.history.clear()
    print("[DEV] Chat history cleared")
    
    # Get available states
    states = session.game_engine.state_engine.states
    
    if request.state_name not in states:
        available = list(states.keys())
        raise HTTPException(
            status_code=400,
            detail=f"State '{request.state_name}' not found. Available: {available}"
        )
    
    # Set state
    session.game_engine.state_engine.current_state = request.state_name
    
    print(f"[DEV] State set to: {request.state_name} - ready for chat")
    
    return SuccessResponse(
        success=True,
        message=f"State set to '{request.state_name}'"
    )


@app.post("/setInventory", response_model=SuccessResponse)
async def set_inventory(request: SetInventoryRequest) -> SuccessResponse:
    """
    Set an inventory item value.
    Used by Editor to manipulate game state during development.
    """
    session = get_session()
    
    # Set inventory item directly
    session.game_engine.inventory.set(request.key, request.value)
    
    print(f"[DEV] Inventory set: {request.key} = {request.value}")
    
    return SuccessResponse(
        success=True,
        message=f"Inventory item '{request.key}' set to {request.value}"
    )


@app.post("/reload", response_model=StatusResponse)
async def reload() -> StatusResponse:
    """
    Hot-reload game definition from disk.
    Preserves current state and inventory if possible.
    """
    print("[DEV] Hot-reloading game definition...")
    
    session = reload_game_definition()
    
    # Get available info
    states = list(session.game_engine.state_engine.states.keys())
    actions = [a.name for a in session.game_engine.state_engine.get_available_actions()]
    
    return StatusResponse(
        current_state=session.game_engine.state_engine.get_current_state().name,
        inventory=session.game_engine.inventory.to_dict(),
        available_states=states,
        available_actions=actions,
        game_started=True  # Always ready in developer mode
    )


@app.post("/reset", response_model=StatusResponse)
async def reset() -> StatusResponse:
    """
    Full reset: reload game definition AND reset state/inventory to initial values.
    """
    global _session
    
    print("[DEV] Full reset...")
    
    # Create fresh session (no preservation)
    _session = None
    
    session = create_session()
    
    # Get available info
    states = list(session.game_engine.state_engine.states.keys())
    actions = [a.name for a in session.game_engine.state_engine.get_available_actions()]
    
    return StatusResponse(
        current_state=session.game_engine.state_engine.get_current_state().name,
        inventory=session.game_engine.inventory.to_dict(),
        available_states=states,
        available_actions=actions,
        game_started=True
    )


@app.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    """
    Get current session status.
    Returns state, inventory, and available states/actions.
    """
    session = get_session()
    
    # Get available info
    states = list(session.game_engine.state_engine.states.keys())
    actions = [a.name for a in session.game_engine.state_engine.get_available_actions()]
    
    return StatusResponse(
        current_state=session.game_engine.state_engine.get_current_state().name,
        inventory=session.game_engine.inventory.to_dict(),
        available_states=states,
        available_actions=actions,
        game_started=True  # Always ready in developer mode
    )


# === Main ===

if __name__ == "__main__":
    print("=" * 60)
    print("DUNGEON DEVELOPER SERVER")
    print("=" * 60)
    print()
    print("Starting on http://localhost:9000")
    print()
    print("Endpoints:")
    print("  POST /chat         - Send user input")
    print("  POST /setState     - Set current state")
    print("  POST /setInventory - Set inventory item")
    print("  POST /reload       - Hot-reload (preserve state)")
    print("  POST /reset        - Full reset")
    print("  GET  /status       - Get session status")
    print()
    
    uvicorn.run(
        "developer:app",
        host="0.0.0.0",
        port=9000,
        reload=False,  # We have our own reload logic
        log_level="info"
    )