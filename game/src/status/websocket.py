import json
import threading
from status.base import Base
from websocketmanager import WebSocketManager

class WebSocketStatus(Base):
    def __init__(self):
        pass

    def stop(self):
        pass

    def set(self, session, expressions, inventory):
        WebSocketManager.send_message(session, json.dumps({
            "function": "state.inventory",
            "data"  : inventory
        }))
        
