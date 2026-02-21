"""
Developer Routes - Proxy endpoints to Developer Server (game/src/developer.py).
These routes forward requests from Editor UI to the Developer Server on port 9000.

This proxy pattern avoids CSRF issues since all requests come from the same origin.

Editor UI (8080) → Editor Backend (8000) → Developer Server (9000)
"""
import httpx
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/developer", tags=["developer"])

# Developer Server URL (configurable)
DEVELOPER_SERVER_URL = "http://localhost:9000"

# HTTP client timeout
TIMEOUT = 30.0


# === Pydantic Models (mirror developer.py) ===

class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response body for /chat endpoint."""
    response: str
    current_state: str
    inventory: Dict[str, Any]


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


# === Helper Functions ===

async def proxy_get(endpoint: str) -> Dict[str, Any]:
    """
    Proxy GET request to Developer Server.
    
    Args:
        endpoint: Endpoint path (e.g., "/status")
        
    Returns:
        JSON response from Developer Server
        
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{DEVELOPER_SERVER_URL}{endpoint}")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Developer Server not running. Start with: cd game/src && python developer.py"
        )
    except httpx.HTTPStatusError as e:
        # Forward error from Developer Server
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")


async def proxy_post(endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Proxy POST request to Developer Server.
    
    Args:
        endpoint: Endpoint path (e.g., "/chat")
        data: JSON body to send
        
    Returns:
        JSON response from Developer Server
        
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{DEVELOPER_SERVER_URL}{endpoint}",
                json=data or {}
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Developer Server not running. Start with: cd game/src && python developer.py"
        )
    except httpx.HTTPStatusError as e:
        # Forward error from Developer Server
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")


# === Proxy Endpoints ===

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Proxy /chat to Developer Server.
    Send user input to game engine and receive response.
    """
    result = await proxy_post("/chat", {"message": request.message})
    return ChatResponse(**result)


@router.post("/setState", response_model=SuccessResponse)
async def set_state(request: SetStateRequest) -> SuccessResponse:
    """
    Proxy /setState to Developer Server.
    Set the current game state by name.
    
    If model_json is provided, the game engine will be reinitialized with
    this in-memory data first, allowing testing of unsaved changes.
    """
    # Build request data, only including optional fields if provided
    data = {"state_name": request.state_name}
    if request.model_json is not None:
        data["model_json"] = request.model_json
    if request.config_json is not None:
        data["config_json"] = request.config_json
    
    result = await proxy_post("/setState", data)
    return SuccessResponse(**result)


@router.post("/setInventory", response_model=SuccessResponse)
async def set_inventory(request: SetInventoryRequest) -> SuccessResponse:
    """
    Proxy /setInventory to Developer Server.
    Set an inventory item value.
    """
    result = await proxy_post("/setInventory", {"key": request.key, "value": request.value})
    return SuccessResponse(**result)


@router.post("/reload", response_model=StatusResponse)
async def reload() -> StatusResponse:
    """
    Proxy /reload to Developer Server.
    Hot-reload game definition from disk (preserves state/inventory).
    """
    result = await proxy_post("/reload")
    return StatusResponse(**result)


@router.post("/reset", response_model=StatusResponse)
async def reset() -> StatusResponse:
    """
    Proxy /reset to Developer Server.
    Full reset: reload game definition AND reset state/inventory.
    """
    result = await proxy_post("/reset")
    return StatusResponse(**result)


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    """
    Proxy /status to Developer Server.
    Get current session status.
    """
    result = await proxy_get("/status")
    return StatusResponse(**result)


@router.get("/health")
async def health():
    """
    Check if Developer Server is running.
    Returns connection status without throwing errors.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DEVELOPER_SERVER_URL}/status")
            return {
                "developer_server": "running",
                "url": DEVELOPER_SERVER_URL,
                "status_code": response.status_code
            }
    except httpx.ConnectError:
        return {
            "developer_server": "not_running",
            "url": DEVELOPER_SERVER_URL,
            "hint": "Start with: cd game/src && python developer.py"
        }
    except Exception as e:
        return {
            "developer_server": "error",
            "url": DEVELOPER_SERVER_URL,
            "error": str(e)
        }