"""
Google Cloud Text-to-Speech provider.
"""
import numpy as np
import threading
import re
from typing import Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

try:
    import google.cloud.texttospeech as tts
    from google.api_core import client_options as client_options_lib
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

from .base_provider import BaseTTSProvider


class GoogleTTSProvider(BaseTTSProvider):
    """
    Google Cloud TTS provider.
    Requires google-cloud-texttospeech package and authentication.
    Supports both API key and Application Default Credentials (ADC).
    """

    def __init__(self, audio_sink, language_code: str = "de-DE", voice_name: str = "de-DE-Journey-D",
                 sample_rate: int = 24000, api_key: Optional[str] = None,
                 model_name: Optional[str] = None, voice_prompt: Optional[str] = None,
                 pitch: float = 0.0, speaking_rate: float = 1.0):
        """
        Initialize Google TTS provider.

        Args:
            audio_sink: Audio sink for output
            language_code: Language code (default: de-DE)
            voice_name: Voice name (default: de-DE-Journey-D, or prompt-based like "Enceladus")
            sample_rate: Sample rate in Hz (default: 24000)
            api_key: Optional API key (if not provided, uses Application Default Credentials)
            model_name: Model name for Gemini TTS (e.g., "gemini-2.5-flash-tts")
            voice_prompt: Character description for prompt-based voices
            pitch: Voice pitch adjustment (-20.0 to 20.0, default: 0.0)
            speaking_rate: Speaking rate (0.25 to 4.0, default: 1.0)
        """
        if not GOOGLE_TTS_AVAILABLE:
            raise ImportError("google-cloud-texttospeech package not installed")

        super().__init__(audio_sink)
        self.language_code = language_code
        self.voice_name = voice_name
        self.sample_rate = sample_rate
        self.model_name = model_name
        self.voice_prompt = voice_prompt
        self.pitch = pitch
        self.speaking_rate = speaking_rate
        self.stop_event = threading.Event()
        self.audio_thread = None

        # Initialize client with API key or ADC
        if api_key:
            client_options = client_options_lib.ClientOptions(api_key=api_key)
            self.client = tts.TextToSpeechClient(client_options=client_options)
        else:
            # Use Application Default Credentials
            self.client = tts.TextToSpeechClient()

    def speak(self, session, text: str) -> None:
        """
        Convert text to speech using Google Cloud TTS.
        Splits text for faster initial response.

        Args:
            session: Game session
            text: Text to speak
        """
        if not text:
            return

        # Clean text
        text = text.replace("\n", " ")
        self.stop_event.clear()

        # Split text into first sentence and rest for faster initial response
        first_part, second_part = self._split_text(text)

        # Synthesize in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_first = executor.submit(self._synthesize_text, first_part)
            future_second = executor.submit(self._synthesize_text, second_part) if second_part else None

            wait([future_first, future_second] if future_second else [future_first], return_when=FIRST_COMPLETED)
            audio_data_first = self._apply_fade_in(future_first.result())

            def play_audio():
                try:
                    # Play first part
                    self._stream_audio(session, audio_data_first)

                    # Play second part if available
                    if future_second and not self.stop_event.is_set():
                        audio_data_second = self._apply_fade_in(future_second.result())
                        self._stream_audio(session, audio_data_second)
                except Exception as e:
                    print(f"[ERROR] Google TTS playback error: {e}")
                finally:
                    self.stop(session)

            # Text output is handled by game controller, not here
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()

    def stop(self, session) -> None:
        """
        Stop current speech.

        Args:
            session: Game session
        """
        self.stop_event.set()

        try:
            if (self.audio_thread is not None and self.audio_thread.is_alive() and threading.current_thread() != self.audio_thread):
                self.audio_thread.join()
            self.audio_thread = None
        except Exception as e:
            print(f"[ERROR] Google TTS stop error: {e}")

    def _synthesize_text(self, text: str) -> np.ndarray:
        """
        Synthesize text to audio using Google Cloud TTS.
        Supports both classic voices and new Gemini 2.5 Flash TTS with prompts.

        Args:
            text: Text to synthesize

        Returns:
            Audio data as numpy array
        """
        if not text or len(text) == 0:
            return np.array([], dtype=np.int16)

        # Build synthesis input
        if self.voice_prompt:
            # Gemini TTS with prompt-based voice
            synthesis_input = tts.SynthesisInput(
                text=text,
                prompt=self.voice_prompt
            )
        else:
            # Classic TTS without prompt
            synthesis_input = tts.SynthesisInput(text=text)

        # Build voice selection
        voice_params = tts.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name
        )
        if self.model_name:
            voice_params.model_name = self.model_name

        # Build audio config with pitch and speaking rate
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,
            pitch=self.pitch,
            speaking_rate=self.speaking_rate
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        # Convert to int16 format
        audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
        return audio_data

    def _stream_audio(self, session, audio_data: np.ndarray, chunk_size: int = 1024) -> None:
        """
        Stream audio data in chunks to audio sink.

        Args:
            session: Game session
            audio_data: Audio data to stream
            chunk_size: Chunk size in samples
        """
        for i in range(0, len(audio_data), chunk_size):
            if self.stop_event.is_set():
                break
            chunk = audio_data[i:i + chunk_size].tobytes()
            self.audio_sink.write(session, chunk)

    def _apply_fade_in(self, audio_data: np.ndarray, duration_ms: int = 10) -> np.ndarray:
        """
        Apply fade-in effect to audio data.

        Args:
            audio_data: Audio data
            duration_ms: Fade duration in milliseconds

        Returns:
            Audio data with fade-in applied
        """
        audio_data = np.copy(audio_data)
        num_samples = int(self.sample_rate * duration_ms / 1000)

        if len(audio_data) < num_samples:
            return audio_data

        fade = np.linspace(0, 1, num=num_samples)
        audio_data[:num_samples] = (audio_data[:num_samples].astype(float) * fade).astype(np.int16)
        return audio_data

    def _split_text(self, text: str, min_chars: int = 50) -> Tuple[str, str]:
        """
        Split text into first part (min 50 chars) and rest for faster initial response.
        Takes first sentence, but continues to next sentences until min_chars is reached.

        Args:
            text: Text to split
            min_chars: Minimum characters for first part (default: 50)

        Returns:
            Tuple of (first_part, rest)
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if not sentences:
            return text, ""

        # Build first part until we reach min_chars
        first_part = sentences[0]
        remaining_sentences = sentences[1:]

        # Keep adding sentences until we reach min_chars
        while remaining_sentences and len(first_part) < min_chars:
            first_part += " " + remaining_sentences[0]
            remaining_sentences = remaining_sentences[1:]

        # Rest is remaining sentences
        second_part = " ".join(remaining_sentences) if remaining_sentences else ""

        return first_part, second_part
