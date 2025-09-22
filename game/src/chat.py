# chat.py
from typing import Callable
from session import Session

def process_chat(session: Session, text: str, session_factory: Callable[[], None] = None):
    if not text:
        return
    
    # 1. Rufe die gekapselte chat-Methode auf.
    #    Die ganze Komplexität (History, Prompts) ist jetzt im LLM-Client verborgen.
    response_dict = session.llm.chat(session, text)
    
    action_name = response_dict.get("action")
    response_text = response_dict.get("text")

    # 2. Wenn eine Aktion zurückkam, triggere die State Engine.
    if action_name:
        action_id = session.state_engine.get_action_id(action_name)
        if action_id:
            session.state_engine.trigger(session, action_id)
            # Hinweis: Der Feedback-Text kommt jetzt direkt vom ersten LLM-Aufruf.
            # Kein zweiter Aufruf mehr nötig.
    
    # 3. Sprich den finalen Text.
    if response_text:
        session.tts.speak(session, response_text)

    # Dein alter HistoryLog kann weiterhin die finalen Ergebnisse aufzeichnen.
    session.history_manager.append(session, {
        "question": text,
        "response": response_text,
        "action": action_name,
        "statusAfter": session.state_engine.get_state()
    })