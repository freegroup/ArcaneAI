"""
State class for game states.
"""
from dataclasses import dataclass
from jinja2 import Template


@dataclass
class State:
    """Represents a game state."""
    name: str
    description: str
    session: any
    
    def get_raw_description(self) -> str:
        """Get the raw description without template rendering."""
        return self.description
    
    def get_description(self) -> str:
        """
        Get the description with Jinja2 template rendering.
        Uses inventory variables from session for {% if %} conditions etc.
        """
        try:
            template = Template(self.description)
            # Access inventory via game_engine
            inventory_dict = self.session.game_engine.inventory.to_dict()
            return template.render(inventory_dict)
        except Exception as e:
            print(f"[WARNING] Failed to render state description: {e}")
            return self.description
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"State(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        desc_preview = self.description[:50] + "..." if len(self.description) > 50 else self.description
        return f"State(name='{self.name}', description='{desc_preview}')"
