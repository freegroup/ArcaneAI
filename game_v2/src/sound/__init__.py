"""
Sound package - Jukebox implementations for sound effects and ambient sounds.
"""
from .base import BaseJukebox
from .web_jukebox import WebJukebox
from .local_jukebox import LocalJukebox

__all__ = ['BaseJukebox', 'WebJukebox', 'LocalJukebox']
