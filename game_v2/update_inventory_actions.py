"""
Script to update game_definition_tipsy_full.json with inventory_actions from YAML.
"""
import json
import yaml
from pathlib import Path

# Paths
yaml_path = Path("../maps/TheTipsyQuest/index.yaml")
json_path = Path("game_definition_tipsy_full.json")

# Load YAML
print(f"Loading YAML from {yaml_path}...")
with open(yaml_path, 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

# Load JSON
print(f"Loading JSON from {json_path}...")
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Create mapping: transition name -> inventory actions
print("Creating action mapping...")
action_map = {}
for transition in yaml_data.get('transitions', []):
    name = transition['metadata']['name']
    actions = transition['metadata'].get('actions', [])
    if actions:
        action_map[name] = actions
        print(f"  {name}: {actions}")

# Update JSON actions
print("\nUpdating JSON actions...")
updated_count = 0
for action in json_data['actions']:
    action_name = action['name']
    if action_name in action_map:
        action['inventory_actions'] = action_map[action_name]
        updated_count += 1
        print(f"  ✓ Updated {action_name}")

# Add inventory initial state from YAML metadata
print("\nAdding inventory initial state...")
if 'metadata' in yaml_data and 'inventory' in yaml_data['metadata']:
    json_data['inventory'] = yaml_data['metadata']['inventory']
    print(f"  ✓ Added inventory with {len(json_data['inventory'])} items")
else:
    print("  ⚠ No inventory found in YAML metadata")

# Save updated JSON
print(f"\nSaving updated JSON to {json_path}...")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! Updated {updated_count} actions with inventory_actions")
