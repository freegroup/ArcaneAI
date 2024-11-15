from audio.base_sink import BaseAudioSink
from websocketmanager import WebSocketManager

class WebSocketSink(BaseAudioSink):

    def __init__(self):
        super().__init__()
        self.close = False


    def write(self, session, chunk, speed):
        if not self.close:
            WebSocketManager.send_bytes(session, chunk)


    def close(self, session):
        self.close = True

