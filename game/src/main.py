import os
import sys 
import signal
import json
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

statusManager = LocalStatus()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
MAP_DIR  = os.path.join(PROJECT_DIR, 'maps')

MAP_FILE =  os.getenv("MAP_FILE")

print(MAP_DIR)
#conversation_file = "fsm_fun.yaml"
#conversation_file = "fsm_techi.yaml"

stop_requested = False


def stop():
    global stop_requested
    print("\nStopping gracefully...")
    stop_requested = True
    statusManager.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, lambda sig, frame: stop())


def newSession():
    return Session(
        map_name =  os.path.splitext(MAP_FILE)[0],  # Remove the suffix from file
        map_dir = MAP_DIR,
        state_engine=StateEngine(f"{MAP_DIR}/{MAP_FILE}"),
        llm = LLMFactory.create(),
        tts = TTSEngineFactory.create(PyAudioSink()),
        stt = STTFactory.create(),
        jukebox = LocalJukebox()
    )

if __name__ == '__main__':

    def process_text(session, text):

        print("=====================================================================================================")
        if text.lower() == "debug":
            session.llm.dump()
            return
        if text.lower() == "reset":
            session.llm.reset(session)
            return
        
        if len(text)>0:
            response = session.llm.chat(session,text)
            print(json.dumps(response, indent=4))

            action = response.get("action") 
            session.tts.stop(session)
            tts_text = "?"
            if action:
                done = session.state_engine.trigger(session, action)
                if done:
                    tts_text = response["text"]
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
                    tts_text = response["text"]
            else:
                tts_text = response["text"]

            statusManager.set(session, response["expressions"], session.state_engine.get_inventory() )
            session.tts.speak(session, tts_text)


    session = newSession()

    # Start the game for this new session
    #
    session.state_engine.trigger(session, "start")
    process_text(session, "Erkläre mir in kurzen Worten worum es hier geht und wer du bist")
    
    # show the current status of the game
    #
    statusManager.set(session, [], session.state_engine.get_inventory())

    try:
        for text in session.stt.start_recording():
            if stop_requested:
                break
            process_text(session, text)
    except Exception as e:
        print(f"An error occurred: {e}")
        stop()