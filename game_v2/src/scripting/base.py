"""
Abstract base class for scripting sandboxes.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSandbox(ABC):
    """Abstract base class for script execution sandboxes."""
    
    @abstractmethod
    def set_var(self, name: str, value: Any) -> None:
        """
        Set a variable in the sandbox.
        
        Args:
            name: Variable name
            value: Value to set
        """
        pass

    @abstractmethod
    def get_var(self, name: str) -> Any:
        """
        Get a variable from the sandbox.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
        """
        pass

    @abstractmethod
    def get_all_vars(self) -> Dict[str, Any]:
        """
        Get all user-defined variables.
        
        Returns:
            Dictionary of all variables
        """
        pass

    @abstractmethod
    def eval(self, code: str) -> Any:
        """
        Evaluate code in the sandbox.
        
        Args:
            code: Code to evaluate
            
        Returns:
            Result of evaluation
        """
        pass

