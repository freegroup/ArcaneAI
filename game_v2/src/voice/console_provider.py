"""
Console TTS Provider - just prints text without generating audio.
Useful for testing and debugging.
"""
from .base_provider import BaseTTSProvider


class ConsoleTTSProvider(BaseTTSProvider):
    """
    Console provider that just prints text instead of generating audio.
    Useful for testing without audio dependencies.
    """

    def speak(self, session, text: str) -> None:
        """
        Console provider - does nothing since text is already printed by game controller.

        Args:
            session: Game session
            text: Text (ignored, already printed by game controller)
        """
        # Text output is handled by game controller, not here
        pass

    def stop(self, session) -> None:
        """
        Stop is a no-op for console provider.

        Args:
            session: Game session
        """
        pass
