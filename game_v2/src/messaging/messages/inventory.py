"""
Inventory Update Message.
"""
from dataclasses import dataclass
from typing import Dict, Any
from .base import Message


@dataclass
class InventoryMessage(Message):
    """Message sent when inventory changes."""
    inventory: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.inventory
        }
    
    @property
    def type(self) -> str:
        return "inventory_update"