import pyttsx3
from tts.base import BaseTTS
from logger_setup import logger

# Definition of JanTTS class inheriting from BaseTTS
class PyTTS(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__(audio_sink)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Setting speech rate
        self.engine.setProperty('volume', 1.0)  # Setting volume level (0.0 to 1.0)


    def speak(self, session, text):
        logger.debug("PyTTS: "+text)
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self, session):
        logger.debug("PyTTS: stop")
        self.engine.stop()
        pass