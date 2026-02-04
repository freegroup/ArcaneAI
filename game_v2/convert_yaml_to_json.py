"""
Convert TheTipsyQuest YAML to our JSON format.
"""
import yaml
import json
from pathlib import Path

def convert_yaml_to_json(yaml_path: str, output_path: str):
    """Convert YAML game definition to JSON format."""
    
    # Load YAML
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Extract initial state
    initial_state = data.get('initial', 'Start')
    
    # Find the transition from Start to get the actual initial state
    actual_initial_state = None
    for transition in data.get('transitions', []):
        if transition['source'] == initial_state:
            actual_initial_state = transition['dest']
            break
    
    if not actual_initial_state:
        actual_initial_state = list(data.get('states', [{}]))[0].get('name', 'WestOfHouse')
    
    # Extract identity and behaviour from metadata
    identity = data.get('metadata', {}).get('normal_prompt', '')
    behaviour = "WICHTIG: Du darfst NUR die explizit definierten Aktionen verwenden. Erfinde NIEMALS eigene Aktionen. Wenn der Spieler etwas tun möchte, das nicht in der Liste der verfügbaren Aktionen steht, antworte im Piraten-Slang ablehnend und verwende [AKTION: keine_aktion]."
    
    # Extract inventory (can be at top level or in metadata)
    inventory = data.get('inventory') or data.get('metadata', {}).get('inventory', {})
    
    # Extract states
    states = {}
    for state in data.get('states', []):
        state_name = state['name']
        system_prompt = state.get('metadata', {}).get('system_prompt', '')
        
        # Skip Start state
        if state.get('metadata', {}).get('state_type') == 'start':
            continue
            
        states[state_name] = {
            "description": system_prompt
        }
    
    # Extract actions (transitions)
    actions = []
    for transition in data.get('transitions', []):
        source = transition['source']
        dest = transition['dest']
        metadata = transition.get('metadata', {})
        name = metadata.get('name', '')
        description = metadata.get('description', metadata.get('system_prompt', ''))
        
        # Skip if no name
        if not name:
            continue
        
        # Skip Start transitions
        if source == 'Start':
            continue
        
        # Get system_prompt for after_fire context
        system_prompt = metadata.get('system_prompt', '')
        
        # Get scripts (called 'actions' in YAML triggers)
        scripts = metadata.get('actions', [])
        
        # Get conditions (from YAML triggers)
        conditions = metadata.get('conditions', [])
        
        # Build prompts object
        prompts = {
            "description": description[:100] if description else name,
            "after_fire": system_prompt[:200] if system_prompt else ""
        }
        
        action = {
            "state_before": source,
            "state_after": dest,
            "name": name,
            "prompts": prompts
        }
        
        # Add conditions if present
        if conditions:
            action["conditions"] = conditions
        
        # Add scripts if present
        if scripts:
            action["scripts"] = scripts
        
        actions.append(action)
    
    # Build output
    output = {
        "initial_state": actual_initial_state,
        "identity": identity,
        "behaviour": behaviour,
        "states": states,
        "actions": actions
    }
    
    # Add inventory if present
    if inventory:
        output["inventory"] = inventory
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(states)} states and {len(actions)} actions")
    print(f"📝 Output: {output_path}")

if __name__ == "__main__":
    yaml_path = Path(__file__).parent.parent / "maps" / "TheTipsyQuest" / "index.yaml"
    output_path = Path(__file__).parent / "game_definition_tipsy_full.json"
    
    convert_yaml_to_json(str(yaml_path), str(output_path))