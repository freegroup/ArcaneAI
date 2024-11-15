import os
import sys 
import signal
import json
import traceback
from dotenv import load_dotenv
load_dotenv() 

from status.local import LocalStatus

from state_engine import StateEngine
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session
from sound.local_jukebox import LocalJukebox
from audio.pyaudio import PyAudioSink
from history import HistoryLog
from chat import process_chat

status_manager  = LocalStatus()
history_manager = HistoryLog()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
MAP_DIR  = os.path.join(PROJECT_DIR, 'maps')

MAP_FILE =  os.getenv("MAP_FILE")

print(MAP_DIR)

stop_requested = False


def stop():
    global stop_requested
    print("\nStopping gracefully...")
    stop_requested = True
    status_manager.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, lambda sig, frame: stop())


def session_factory():
    return Session(
        ws_token = "local",
        map_name =  os.path.splitext(MAP_FILE)[0],  # Remove the suffix from file
        map_dir = MAP_DIR,
        state_engine=StateEngine(f"{MAP_DIR}/{MAP_FILE}"),
        llm = LLMFactory.create(),
        tts = TTSEngineFactory.create(PyAudioSink()),
        stt = STTFactory.create(),
        jukebox = LocalJukebox(),
        status_manager = status_manager,
        history_manager = history_manager
    )

if __name__ == '__main__':

    session = session_factory()

    # Start the game for this new session
    #
    session.state_engine.trigger(session, session.state_engine.get_action_id("start"))
    process_chat(session, "Erkläre mir in kurzen Worten worum es hier geht und wer du bist", session_factory)
    
    try:
        for text in session.stt.start_recording():
            if stop_requested:
                break
            session.tts.stop(session)
            process_chat(session, text, session_factory)
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        stop()