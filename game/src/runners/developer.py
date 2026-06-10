"""
Developer runner — REST API server for editor integration.
"""
from __future__ import annotations

from .base import BaseRunner


class DeveloperRunner(BaseRunner):
    """Runs the game as a developer REST API server."""

    def run(self) -> None:
        import uvicorn
        from developer import app
        print("Starting developer server on http://localhost:9000")
        uvicorn.run(app, host="0.0.0.0", port=9000, reload=False, log_level="info")
