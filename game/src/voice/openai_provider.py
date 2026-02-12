"""
OpenAI Text-to-Speech provider.
"""
import threading
import time
from openai import OpenAI

from .base_provider import BaseTTSProvider


class OpenAITTSProvider(BaseTTSProvider):
    """
    OpenAI TTS provider with streaming support.
    """

    def __init__(self, audio_sink, api_key: str = None, voice: str = "onyx", speed: float = 1.2, model: str = "tts-1"):
        """
        Initialize OpenAI TTS provider.

        Args:
            audio_sink: Audio sink for output
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            model: Model to use (tts-1 or tts-1-hd)
        """
        super().__init__(audio_sink)
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.voice = voice
        self.speed = speed
        self.model = model
        self.stop_event = threading.Event()
        self.audio_thread = None
        self.max_retries = 3

    def speak(self, session, text: str) -> None:
        """
        Convert text to speech using OpenAI TTS with streaming.

        Args:
            session: Game session
            text: Text to speak
        """
        # Stop any ongoing playback
        self.stop(session)
        self.stop_event.clear()

        def play_audio():
            try:
                retries = 0
                while retries < self.max_retries:
                    try:
                        with self.client.audio.speech.with_streaming_response.create(
                            input=text,
                            speed=self.speed,
                            response_format="pcm",
                            voice=self.voice,
                            model=self.model
                        ) as response:
                            # Text output is handled by game controller, not here
                            for chunk in response.iter_bytes(chunk_size=8192):
                                if self.stop_event.is_set():
                                    break
                                self.audio_sink.write(session, chunk)
                        break  # Success
                    except (ConnectionError, TimeoutError) as e:
                        retries += 1
                        print(f"[WARNING] OpenAI TTS connection error ({retries}/{self.max_retries}): {e}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"[ERROR] OpenAI TTS error: {e}")
                        break
            except Exception as e:
                print(f"[ERROR] OpenAI TTS playback error: {e}")

        self.audio_thread = threading.Thread(target=play_audio, daemon=True)
        self.audio_thread.start()

    def stop(self, session) -> None:
        """
        Stop current speech.

        Args:
            session: Game session
        """
        try:
            self.stop_event.set()

            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_thread = None
        except Exception as e:
            print(f"[ERROR] OpenAI TTS stop error: {e}")
