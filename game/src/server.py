from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response, status, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
import mimetypes
import secrets
import os
import json
import asyncio

from dotenv import load_dotenv
load_dotenv() 

from status.websocket import WebSocketStatus as Status
from state_engine import StateEngine
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session as ChatSession
from sound.web_jukebox import WebJukebox
from websocketmanager import WebSocketManager
from audio.websocket import WebSocketSink
from history import HistoryLog
from chat import process_chat
from logger_setup import logger

BASE_URI = "/game"
PORT = 9000
#SAME_SITE_VALUE = "None" # cross origin and https
SAME_SITE_VALUE = "Lax" # local http


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
MAPS_ROOT_DIR  = os.path.join(PROJECT_DIR, 'maps')

MAP_FILE =  os.getenv("MAP_FILE")


status_manager = Status()
history_manager = HistoryLog()

app = FastAPI(title="Chat Application", version="1.0.0", root_path=BASE_URI)
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:9000"],  # Adjust if using a different port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_USERNAME = os.getenv("USERNAME", "user")
VALID_PASSWORD = os.getenv("PASSWORD", "pass")

session_store: Dict[str, Dict] = {}


from fastapi.middleware.cors import CORSMiddleware


class ChatMessage(BaseModel):
    text: str

class LoginData(BaseModel):
    username: str
    password: str


def session_factory():
    return ChatSession(
            map_name =  MAP_FILE,
            map_dir = MAPS_ROOT_DIR,
            state_engine = StateEngine(f"{MAPS_ROOT_DIR}/{MAP_FILE}/index.yaml"),
            llm = LLMFactory.create(),
            tts = TTSEngineFactory.create(WebSocketSink()),
            stt = STTFactory.create(),
            jukebox= WebJukebox(),
            status_manager = status_manager,
            history_manager = history_manager
        )

def create_proxy_aware_redirect(request: Request, target_route: str) -> RedirectResponse:
    logger.debug("Request Headers in /ui route:")
    for header, value in request.headers.items():
        logger.debug(f"{header}: {value}")

    # Get forwarded headers or defaults
    forwarded_proto = request.headers.get("x-dungeon-proto", "http")
    forwarded_host = request.headers.get("x-dungeon-host", "localhost")
    forwarded_port = request.headers.get("x-dungeon-port", f"{PORT}")
    logger.debug(f"dungeon_proto {forwarded_proto}")
    logger.debug(f"dungeon_host {forwarded_host}")
    logger.debug(f"dungeon_port {forwarded_port}")
    # Construct the base URL manually
    base_url = f"{forwarded_proto}://{forwarded_host}"
    if forwarded_port and forwarded_port not in ["80", "443"]:
        base_url += f":{forwarded_port}"

    # Manually create the target URL, ensuring both parts are strings
    target_path = request.app.url_path_for(target_route)  # Provides just the path
    target_url = f"{base_url}{BASE_URI}{target_path}"  # Combine the base URL and target path
    logger.debug(f"Target URL for Redirect: {target_url}")

    return target_url


# Middleware to retrieve or create a session
def get_session(request: Request, response: Response) -> Dict:
    session_id = request.cookies.get("session_id")
    logger.debug(f"Current session_id (get_session): {session_id}")

    if session_id and session_id in session_store:
        return session_store[session_id], session_id

    if session_id is None:
        session_id = str(uuid4())
    
    session_store[session_id] = session_factory()
    response.set_cookie("session_id", session_id, httponly=True, samesite=SAME_SITE_VALUE)
    return session_store[session_id], session_id


# Mount the static directory to serve CSS, JavaScript, and images
app.mount("/assets", StaticFiles(directory="static"), name="static")

# GET route for the login page
@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html",  {"request": request, "BASE_URI": BASE_URI})


@app.post("/login_post", name="login")
async def login(request: Request, data: LoginData, response: Response):
    # Manually validate username and password
    if not (secrets.compare_digest(data.username, VALID_USERNAME) and secrets.compare_digest(data.password, VALID_PASSWORD)):
        return JSONResponse({"error": "Invalid username or password"}, status_code=400)

    # Set the session cookie and redirect to the main UI
    response = RedirectResponse(url=create_proxy_aware_redirect(request, "ui"), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie("authenticated", "yes", httponly=True, samesite=SAME_SITE_VALUE)
    return response


# Updated /ui route to require authentication
@app.get("/ui", response_class=HTMLResponse, name="ui")
async def ui(request: Request, response: Response):
    # Check if user is authenticated by looking for the "authenticated" cookie
    if request.cookies.get("authenticated") != "yes":
        return RedirectResponse(url=create_proxy_aware_redirect(request, "login_page")) 

    # Proceed to load the UI if authenticated
    session, session_id = get_session(request, response)

    template_response = templates.TemplateResponse("index.html", {"request": request, "session": session, "BASE_URI": BASE_URI})
    template_response.set_cookie("session_id", session_id, httponly=True, samesite=SAME_SITE_VALUE)
    
    logger.debug(f"Using session with session_id: {session_id} for /ui request")
    return template_response


# Chat endpoint with cookie-based authentication
@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage, response: Response):
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session, session_id = get_session(request, response)
    logger.debug(f"Using session with session_id: {session_id} for /chat request")

    # new user input. Stop curent TTS output
    #
    session.tts.stop(session)
    WebSocketManager.send_message(session, json.dumps({"function":"speak.stop"}))

    text = data.text
    response_text = ""

    if text.lower() == "start":
        old_ws_token = session.ws_token
        session_store[session_id] = session_factory()
        session, session_id = get_session(request, response)
        session.ws_token = old_ws_token
        text = session.state_engine.get_action_system_prompt(session.state_engine.get_action_id("start"))
        session.state_engine.trigger(session, session.state_engine.get_action_id("start"))

    response_text = process_chat(session, text, session_factory)
    return JSONResponse({"response": response_text})



# REST endpoint to serve audio files
@app.get("/api/audio/{filename}", name="audio_get")
async def get_audio(filename: str, request: Request, response: Response):
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session, session_id = get_session(request, response)

    file_path = f"{session.map_dir}/{session.map_name}/soundfx/{filename}"
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename, media_type=mime_type)
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/websocket/connect", name="ws_connect")
async def ws_connect(request: Request, response: Response):
    session, session_id = get_session(request, response)
    logger.debug(f"Using session with session_id: {session_id} for /ws/connect request")

    if not session.ws_token:
        session.ws_token = str(uuid4())

    logger.debug(f"Retrieved or created ws_token: {session.ws_token}")
    return {"token": session.ws_token}


# WebSocket handling
@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    logger.debug("WZ_TOKEN", token)
    await WebSocketManager.connect(websocket, token)
    try:
        while True:
            await WebSocketManager.process_queue(token)
            await asyncio.sleep(0.1)  # Small delay to prevent a tight loop, adjust as needed
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        await WebSocketManager.remove(token)
        

if __name__ == "__main__":
    import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=PORT,  log_level="trace")
    uvicorn.run(app, host="0.0.0.0", port=PORT)


