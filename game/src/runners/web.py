"""
Web runner — FastAPI server for browser-based play.
"""
from __future__ import annotations
import os
from pathlib import Path

from .base import BaseRunner


class WebRunner(BaseRunner):
    """Runs the game as a FastAPI web server."""

    def run(self) -> None:
        import uvicorn
        from server import app, PORT, BASE_URI
        print(f"Starting web server on http://0.0.0.0:{PORT}{BASE_URI}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)
