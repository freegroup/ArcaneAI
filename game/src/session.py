

class Session():
    def __init__(self, map_name, map_dir, state_engine, llm, tts, stt, jukebox, ws_token = None):
        self.map_dir = map_dir
        self.map_name = map_name
        self.state_engine = state_engine
        self.llm = llm
        self.tts= tts
        self.stt = stt
        self.last_action = ""
        self.last_state = ""
        self.jukebox = jukebox
        self.ws_token = ws_token

