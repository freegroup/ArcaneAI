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

from motorcontroller.mock import MotorControlerMock
from state_engine import StateEngine
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session as ChatSession
from sound.web_jukebox import WebJukebox
from websocketmanager import WebSocketManager
from audio.websocket import WebSocketSink


BASE_URI = "/game"
PORT = 9000
#SAME_SITE_VALUE = "None" # cross origin and https
SAME_SITE_VALUE = "Lax" # local http


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
MAP_DIR  = os.path.join(PROJECT_DIR, 'maps')

MAP_FILE =  os.getenv("MAP_FILE")


debug_ui = MotorControlerMock()
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


def newChatSession():
    print("CREATE NEW SESSION OBJECT")
    return ChatSession(
            map_name =  os.path.splitext(MAP_FILE)[0],  # Remove the suffix from file
            map_dir = MAP_DIR,
            state_engine = StateEngine(f"{MAP_DIR}/{MAP_FILE}"),
            llm = LLMFactory.create(),
            tts = TTSEngineFactory.create(WebSocketSink()),
            stt = STTFactory.create(),
            jukebox= WebJukebox()
        )

def create_proxy_aware_redirect(request: Request, target_route: str) -> RedirectResponse:
    print("Request Headers in /ui route:")
    for header, value in request.headers.items():
        print(f"{header}: {value}")

    # Get forwarded headers or defaults
    forwarded_proto = request.headers.get("x-dungeon-proto", "http")
    forwarded_host = request.headers.get("x-dungeon-host", "localhost")
    forwarded_port = request.headers.get("x-dungeon-port", f"{PORT}")
    print(f"dungeon_proto {forwarded_proto}")
    print(f"dungeon_host {forwarded_host}")
    print(f"dungeon_port {forwarded_port}")
    # Construct the base URL manually
    base_url = f"{forwarded_proto}://{forwarded_host}"
    if forwarded_port and forwarded_port not in ["80", "443"]:
        base_url += f":{forwarded_port}"

    # Manually create the target URL, ensuring both parts are strings
    target_path = request.app.url_path_for(target_route)  # Provides just the path
    target_url = f"{base_url}{BASE_URI}{target_path}"  # Combine the base URL and target path
    print(f"Target URL for Redirect: {target_url}")

    return target_url


# Middleware to retrieve or create a session
def get_session(request: Request, response: Response) -> Dict:
    session_id = request.cookies.get("session_id")
    print(f"Current session_id (get_session): {session_id}")
    print(session_store)
    print(session_id)
    if session_id and session_id in session_store:
        return session_store[session_id], session_id
    
    if session_id is None:
        session_id = str(uuid4())
    
    session_store[session_id] = newChatSession()
    print("SET COOKIE SESSION_ID")
    response.set_cookie("session_id", session_id, httponly=True, samesite=SAME_SITE_VALUE)
    print(f"New session_id set: {session_id}")
    return session_store[session_id], session_id


# Mount the static directory to serve CSS, JavaScript, and images
app.mount("/assets", StaticFiles(directory="static"), name="static")

# GET route for the login page
@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html",  {"request": request, "BASE_URI": BASE_URI})


@app.post("/login_post", name="login")
async def login(request: Request, data: LoginData, response: Response):
    print("LOGIN IN THE REQUEST FLOW")
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
    
    print(f"Using session with session_id: {session_id} for /ui request")
    return template_response


# Chat endpoint with cookie-based authentication
@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage, response: Response):
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session, session_id = get_session(request, response)
    print(f"Using session with session_id: {session_id} for /chat request")

    text = data.text
    
    if text.lower() == "debug":
        session.llm.dump()
        return
     
    if text.lower() == "reset":
        session.llm.reset(session)
        return
    
    if text.lower() == "start":
        old_ws_token = session.ws_token
        session_store[session_id] = newChatSession()
        session, session_id = get_session(request, response)
        session.ws_token = old_ws_token
        session.state_engine.trigger(session, "start")
        text = "Erkläre dem Spieler in kurzen Worten worum es hier geht und wer du bist, sei bitte auch so ehrlich und erwähne, dass du manchmal voreilig in deinen Aussagen bist da du nicht sofort alles überblickst. Du bist ja nur der Gehilfe und nicht das Gehirn. Einfach mal nachhacken hilft falls Du eine Behauptung aufstellst."

    response_text = ""
    if len(text) > 0:
        response = session.llm.chat(session, text)
        action = response.get("action")
        session.tts.stop(session)
        if action:
            done = session.state_engine.trigger(session, action)
            if done:
                debug_ui.set(response["expressions"], session.state_engine.get_inventory())
                response_text = response["text"]
                session.llm.system(session.state_engine.get_action_system_prompt(action))
            else:
                # generate a negative answer to the last tried transition
                text = """
                Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                Hier ist der Fehler den wir vom Sytem erhalten haben:
                """+session.state_engine.last_transition_error
                response = session.llm.chat(session, text)
                debug_ui.set(response["expressions"], session.state_engine.get_inventory() )

                response_text= response["text"]
        else:
            debug_ui.set(response["expressions"], session.state_engine.get_inventory())
            response_text = response["text"]

    token = session.ws_token
    if token:
        WebSocketManager.send_message(token, json.dumps({"function":"chat_response", "text":response_text}))

    WebSocketManager.send_message(token, json.dumps({"function":"speak.stop"}))
    session.tts.speak(session, response_text)
    debug_ui.set([], session.state_engine.get_inventory())

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
    print(f"Using session with session_id: {session_id} for /ws/connect request")

    if not session.ws_token:
        session.ws_token = str(uuid4())

    print(f"Retrieved or created ws_token: {session.ws_token}")
    return {"token": session.ws_token}


# WebSocket handling
@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    print("WZ_TOKEN", token)
    await WebSocketManager.connect(websocket, token)
    try:
        while True:
            await WebSocketManager.process_queue(token)
            await asyncio.sleep(0.1)  # Small delay to prevent a tight loop, adjust as needed
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        await WebSocketManager.remove(token)
        

if __name__ == "__main__":
    import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=PORT,  log_level="trace")
    uvicorn.run(app, host="0.0.0.0", port=PORT)


