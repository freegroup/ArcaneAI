"""
Inventory System for managing game items and flags.
Uses Lua scripting engine for powerful expression evaluation.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from scripting.lua import LuaSandbox

if TYPE_CHECKING:
    from session import GameSession
    from state_engine import Action


class Inventory:
    """
    Manages the game inventory - items, flags, and counters.
    Uses Lua scripting for flexible action execution.
    """
    
    def __init__(self, session: GameSession, items: Optional[Dict[str, Any]] = None, enum_constraints: Optional[Dict[str, List]] = None) -> None:
        self.session: GameSession = session
        self.lua: LuaSandbox = LuaSandbox()
        self.items: Dict[str, Any] = items or {}
        self._enum_constraints: Dict[str, List] = enum_constraints or {}

        if items:
            for key, value in items.items():
                self.lua.set_var(key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.lua.get_var(key)
            return value if value is not None else default
        except:
            return default
    
    def set(self, key: str, value: Any) -> None:
        if key in self._enum_constraints:
            allowed = self._enum_constraints[key]
            if value not in allowed:
                print(f"[WARNING] Invalid enum value '{value}' for '{key}'. Allowed: {allowed}. Ignoring.")
                return
        self.lua.set_var(key, value)
        self.items[key] = value
    
    def execute(self, actions: List[str]) -> None:
        """
        Execute a list of inventory actions using Lua.
        Inventory is master - any new variables created in Lua are synced back.
        
        Actions are Lua code strings like:
        - "coins = coins + 1"
        - "has_key = true"
        - "discovered_room = true"
        - "if coins > 10 then has_bonus = true end"
        
        Args:
            actions: List of Lua code strings to execute
        """
        for action in actions:
            if not action or not action.strip():
                continue
            
            try:
                self.lua.eval(action)
            except Exception as e:
                print(f"[WARNING] Failed to execute inventory action '{action}': {e}")
        
        # Sync: Pull all Lua variables back into inventory items
        self._sync_from_lua()
    
    def _sync_from_lua(self) -> None:
        all_vars: Dict[str, Any] = self.lua.get_all_vars()
        for key, value in all_vars.items():
            if key in self._enum_constraints:
                allowed = self._enum_constraints[key]
                if value not in allowed:
                    print(f"[WARNING] Lua set invalid enum value '{value}' for '{key}'. Allowed: {allowed}. Reverting.")
                    self.lua.set_var(key, self.items.get(key))
                    continue
            self.items[key] = value
    
    def eval(self, condition: str) -> bool:
        """
        Evaluate a condition using Lua.
        
        Args:
            condition: Lua condition string like "coins > 5"
            
        Returns:
            True if condition is met, False otherwise
        """
        if not condition or not condition.strip():
            return True
        
        try:
            # Wrap in return statement for Lua
            result = self.lua.eval(f"return ({condition})")
            return bool(result)
        except Exception as e:
            print(f"[WARNING] Failed to evaluate condition '{condition}': {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get all inventory items with their current values.
        Inventory is master - returns all items.
        Since items can be created dynamically by scripts, we return all Lua variables.

        Returns:
            Dictionary of all inventory items
        """
        # Inventory is master - return all variables
        # Items are created dynamically by scripts, so we need all Lua vars
        return self.items.copy()

    def get_enum_values(self, key: str) -> Optional[List]:
        """
        Get the allowed enum values for a key, if it has an enum constraint.

        Args:
            key: Inventory key

        Returns:
            List of allowed values, or None if the key is not an enum
        """
        return self._enum_constraints.get(key)
    
    def get_all_vars(self) -> Dict[str, Any]:
        """
        Get ALL Lua variables (for debugging).
        
        Returns:
            Dictionary of all Lua variables
        """
        return self.lua.get_all_vars()
    
    def on_action(self, action: Action) -> bool:
        """
        Callback method for StateEngine action hook.
        Executes inventory actions when an action is performed.
        
        Args:
            action: The action being executed
            
        Returns:
            True to allow action, False to veto
        """
        if action.scripts:
            print(f"[INVENTORY] Action '{action.name}' executing {len(action.scripts)} script(s)")
            for script in action.scripts:
                print(f"[INVENTORY]   → {script}")
            self.execute(action.scripts)
            
            # Send inventory update via message queue
            if self.session.message_queue:
                from messaging.messages.inventory import InventoryMessage
                message = InventoryMessage(inventory=self.to_dict())
                self.session.message_queue.send(message)
        
        return True
    
    def __repr__(self) -> str:
        return f"Inventory({self.to_dict()})"
