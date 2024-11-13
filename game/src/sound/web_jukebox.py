from websocketmanager import WebSocketManager

import json
from sound.base import BaseJukebox

class WebJukebox(BaseJukebox):
    def __init__(self):
        pass

    def play_sound(self, session, file_name, volume=100, loop=True, duration=2):
        """
        Play a sound from the given file path.
        :param file_path: Absolute path to the sound file (wav or mp3).
        :param loop: If True, play sound in an infinite loop; otherwise, play once.
        :return: PlayingSound object for controlling this sound.
        """
        if not file_name or len(file_name)==0:
            return #silently
        message = json.dumps({ "function": "sound.play_sound", "loop": loop, "file_name": file_name, "volume": volume, "duration":duration}, indent=4)
        WebSocketManager.send_message(session, message)


    def stop_all(self, session):
        """Stop all currently playing sounds."""
        message = json.dumps({ "function": "sound.stop_all"}, indent=4)
        WebSocketManager.send_message(session, message)


    def stop_ambient(self, session):
        """Stop all ambient playing sounds."""
        message = json.dumps({ "function": "sound.stop_ambient"}, indent=4)
        WebSocketManager.send_message(session, message)

