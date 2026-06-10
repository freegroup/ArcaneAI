"""
Abstract base class for all game runners.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class BaseRunner(ABC):
    """
    Base class for all game runners.
    A runner sets up the I/O infrastructure and drives the game loop.
    """

    @abstractmethod
    def run(self) -> None:
        """Start and run the game until completion."""
        pass
