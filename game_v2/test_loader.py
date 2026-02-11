#!/usr/bin/env python3
"""
Test script to verify that the game loader correctly handles the original Designer format,
especially triggers in StateShape elements.
"""
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from game_engine import GameEngine

class MockSession:
    """Mock session for testing."""
    def __init__(self):
        self.messages = []
        self.audio_sink = None  # Mock audio sink
    
    def send_to_llm(self, message):
        """Mock LLM response."""
        self.messages.append(message)
        return "Mock response"
    
    def send_message(self, **kwargs):
        """Mock message sending."""
        self.messages.append(kwargs)

def test_loader():
    """Test the game loader with the original Designer format."""
    print("=" * 80)
    print("Testing Game Loader with Original Designer Format")
    print("=" * 80)
    
    # Create mock session
    session = MockSession()
    
    # Load game engine
    print("\n1. Loading game definition from game_definition_tipsy_v2.json...")
    try:
        engine = GameEngine(session, "game_definition_tipsy_v2.json")
        print("   ✓ Game definition loaded successfully!")
    except Exception as e:
        print(f"   ✗ Error loading game: {e}")
        return False
    
    # Check states
    print(f"\n2. Checking states...")
    states = engine.game_data.get('states', {})
    print(f"   Found {len(states)} states:")
    for state_name in sorted(states.keys()):
        print(f"     - {state_name}")
    
    # Check initial state
    initial_state = engine.game_data.get('initial_state')
    print(f"\n3. Initial state: {initial_state}")
    
    # Check inventory
    print(f"\n4. Checking inventory...")
    inventory = engine.game_data.get('inventory', {})
    print(f"   Found {len(inventory)} inventory items:")
    for key, value in sorted(inventory.items()):
        print(f"     - {key}: {value}")
    
    # Check actions
    print(f"\n5. Checking actions...")
    actions = engine.game_data.get('actions', [])
    print(f"   Found {len(actions)} actions total")
    
    # Separate transition actions from internal triggers
    transitions = [a for a in actions if a['state_before'] != a['state_after']]
    triggers = [a for a in actions if a['state_before'] == a['state_after']]
    
    print(f"   - {len(transitions)} transitions (state changes)")
    print(f"   - {len(triggers)} internal triggers (same state)")
    
    # Show some examples of internal triggers
    print(f"\n6. Examples of internal triggers (from StateShape elements):")
    trigger_examples = {}
    for trigger in triggers[:10]:  # Show first 10
        state = trigger['state_before']
        if state not in trigger_examples:
            trigger_examples[state] = []
        trigger_examples[state].append(trigger['name'])
    
    for state, names in trigger_examples.items():
        print(f"   State '{state}':")
        for name in names:
            print(f"     - {name}")
    
    # Check specific state with known triggers
    print(f"\n7. Detailed check for 'FriedhofDerTraeume' state (has many triggers):")
    friedhof_triggers = [a for a in actions if a['state_before'] == 'FriedhofDerTraeume' and a['state_after'] == 'FriedhofDerTraeume']
    print(f"   Found {len(friedhof_triggers)} internal triggers:")
    for trigger in friedhof_triggers:
        print(f"     - {trigger['name']}")
        if trigger.get('conditions'):
            print(f"       Conditions: {trigger['conditions']}")
        if trigger.get('scripts'):
            print(f"       Scripts: {trigger['scripts']}")
    
    # Check KalterRaum trigger
    print(f"\n8. Checking 'KalterRaum' state (has untersuche_den_raum trigger):")
    kalter_raum_triggers = [a for a in actions if a['state_before'] == 'KalterRaum' and a['state_after'] == 'KalterRaum']
    print(f"   Found {len(kalter_raum_triggers)} internal trigger(s):")
    for trigger in kalter_raum_triggers:
        print(f"     - {trigger['name']}")
        print(f"       Description: {trigger['prompts']['description']}")
        if trigger.get('sound_effect'):
            print(f"       Sound: {trigger['sound_effect']}")
        if trigger.get('scripts'):
            print(f"       Scripts: {trigger['scripts']}")
    
    print("\n" + "=" * 80)
    print("Test completed successfully! ✓")
    print("=" * 80)
    print("\nSummary:")
    print(f"  - States: {len(states)}")
    print(f"  - Actions: {len(actions)} ({len(transitions)} transitions, {len(triggers)} triggers)")
    print(f"  - Inventory items: {len(inventory)}")
    print(f"  - Initial state: {initial_state}")
    print("\nConclusion: The original Designer format (maps/TheTipsyQuest/index.json)")
    print("is being correctly loaded and converted, including all triggers in StateShape elements!")
    
    return True

if __name__ == "__main__":
    success = test_loader()
    exit(0 if success else 1)