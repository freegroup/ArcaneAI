from typing import Callable

def process_chat(session, text, session_factory: Callable[[str], None]):
    log_entry = {
        "question": text,
        "statusBefore": session.state_engine.get_state()
    }
    response_text = "?"
    action_name = None
    try:
        if text.lower() == "debug":
            session.llm.dump()
            return
        if text.lower() == "reset":
            session.llm.reset(session)
            return
        
        if len(text)>0:
            response = session.llm.chat(session,text)
            action_name = response.get("action") 

            # trigger the action, if the LLM found an action to trigger
            #
            if action_name:
                action_id = session.state_engine.get_action_id(action_name)
                done = session.state_engine.trigger(session, action_id)

                if done:
                    text = " ".join("""
                    Die letze Aktion war erfolgreich. Wiederhole am besten die letze Chatbot (nicht system)  Antwort, ohne zu erwähnen, dass du diese wiederholst.
                    Beachte eventuell neue Erkenntnisse.
                    Komme nicht auf die Idee neue Aktionen oder vorausschauend zu handeln.
                    """.split())
                    response = session.llm.chat(session, text)
                else:
                    text = " ".join("""
                    Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                    eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                    Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                    Hier ist der Fehler den wir vom Sytem erhalten haben:
                    """.split())+" "+session.state_engine.last_transition_error
                    response = session.llm.chat(session, text)

            response_text = response["text"]
            session.status_manager.set(session, response["expressions"], session.state_engine.get_all_vars() )
           
            session.tts.speak(session, response_text)
    finally:
        log_entry["response"] = response_text
        log_entry["statusAfter"] = session.state_engine.get_state()
        log_entry["action"] = action_name
        session.history_manager.append(session, log_entry)

    return response_text