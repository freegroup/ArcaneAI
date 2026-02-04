#!/usr/bin/env python3
"""
Wrapper script to run the console game.
Actual implementation is in src/main.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run
from src.main import main

if __name__ == "__main__":
    main()