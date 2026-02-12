"""
Lua scripting sandbox for safe script execution.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Set

from lupa import LuaRuntime
from .base import BaseSandbox


class LuaSandbox(BaseSandbox):
    """Lua scripting sandbox for executing game scripts safely."""
    
    def __init__(self) -> None:
        self.lua: LuaRuntime = LuaRuntime(unpack_returned_tuples=True)
        self.env: Any = self.lua.globals()
        
        # Capture the initial state of Lua globals (before setting user variables)
        self.initial_globals: Set[str] = set(self.env.keys())

    def set_var(self, name: str, value: Any) -> None:
        """
        Set a variable in the Lua environment.
        
        Args:
            name: Variable name
            value: Value to set
        """
        try:
            if isinstance(value, bool):
                # Lua uses `true` and `false` for booleans
                lua_value: str = 'true' if value else 'false'
                self.lua.execute(f"{name} = {lua_value}")
            else:
                self.lua.execute(f"{name} = {value}")
        except Exception as e:
            print(f"ERROR: unable to set Lua value with '{name} = {value}': {e}")
            raise

    def get_var(self, name: str) -> Any:
        """
        Get a variable from the Lua environment.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
        """
        return self.lua.globals()[name]

    def get_all_vars(self) -> Dict[str, Any]:
        """
        Get all user-defined variables from Lua environment.
        
        Returns:
            Dictionary of all user-defined variables
        """
        # Get all current globals and filter out the initial (default) Lua globals
        current_globals: Set[str] = set(self.env.keys())
        user_defined_globals: Set[str] = current_globals - self.initial_globals
        # Create a dictionary of only user-defined variables
        return {key: self.env[key] for key in user_defined_globals}

    def eval(self, code: str) -> Any:
        """
        Evaluate Lua code.
        
        Args:
            code: Lua code to evaluate
            
        Returns:
            Result of evaluation, or False on error
        """
        try:
            # empty condition == True
            if not code or len(code) == 0:
                return True
            
            return self.lua.execute(code)
        except Exception as e:
            print(f"Unable to evaluate: '{code}': {e}")
            return False
