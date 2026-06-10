"""
Runners package — game entry point adapters.
Each runner sets up the I/O infrastructure for a specific environment.
"""
from .base import BaseRunner
from .console import ConsoleRunner
from .web import WebRunner
from .developer import DeveloperRunner


def _load_telegram():
    try:
        from .telegram import TelegramRunner
        return TelegramRunner
    except ImportError as e:
        raise ImportError(
            "Telegram runner requires 'python-telegram-bot'.\n"
            "Install it with: pip install -r game/requirements.txt"
        ) from e


RUNNERS = {
    "console": ConsoleRunner,
    "web": WebRunner,
    "developer": DeveloperRunner,
    "telegram": _load_telegram,  # loaded on demand
}

__all__ = ["BaseRunner", "ConsoleRunner", "WebRunner", "DeveloperRunner", "RUNNERS"]
