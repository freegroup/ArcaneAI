#!/usr/bin/env python3
"""
Wrapper script to run the web server.
Actual implementation is in src/server.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run
if __name__ == "__main__":
    import uvicorn
    from src.server import app, PORT
    
    print(f"Starting server on http://0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)