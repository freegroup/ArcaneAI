import time
from RealtimeTTS import TextToAudioStream, CoquiEngine
from logger_setup import logger

from tts.base import BaseTTS


class CoquiTTS(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__(audio_sink)
        self.engine = CoquiEngine(
            language="de",
            full_sentences=True)
        
        self.stream = TextToAudioStream(
            self.engine, 
            language="de", 
            tokenizer="stanza")


    def speak(self, session, text):
        logger.debug("CoquiTTS: "+text)
        self.stream.feed(text)
        time.sleep(1.0)
        self.stream.play_async()
        while self.stream.is_playing():
            time.sleep(0.1)


    def stop(self, session):
        logger.debug("CoquiTTS: stop")
        self.stream.stop()
  

