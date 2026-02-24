#!/usr/bin/env python3
"""
Zork I ZIL to ArcaneAI model.json Converter

This script converts the Zork I dungeon definition file (1dungeon.zil)
from the ZIL (Zork Implementation Language) format to the ArcaneAI 
game engine model.json format.

Source: https://github.com/historicalsource/zork1/blob/master/1dungeon.zil

Usage:
    python zork_converter.py [--output maps/Zork/model.json]
"""

import re
import json
import uuid
import urllib.request
from typing import Dict, List, Any, Optional, Tuple

# ZIL source URL
ZIL_URL = "https://raw.githubusercontent.com/historicalsource/zork1/master/1dungeon.zil"

# Object flag meanings in ZIL
OBJECT_FLAGS = {
    'TAKEBIT': 'takeable',
    'WEAPONBIT': 'weapon',
    'FOODBIT': 'food',
    'DRINKBIT': 'drink',
    'CONTBIT': 'container',
    'OPENBIT': 'open',
    'LIGHTBIT': 'light',
    'READBIT': 'readable',
    'BURNBIT': 'burnable',
    'TURNBIT': 'turnable',
    'DOORBIT': 'door',
    'ACTORBIT': 'actor',
    'NDESCBIT': 'nodesc',
    'TRYTAKEBIT': 'notakeable',
    'TRANSBIT': 'transparent',
    'SURFACEBIT': 'surface',
    'SACREDBIT': 'sacred',
    'SEARCHBIT': 'searchable',
    'CLIMBBIT': 'climbable',
}

# Direction mappings from ZIL to display names
DIRECTIONS = {
    'NORTH': 'north',
    'SOUTH': 'south', 
    'EAST': 'east',
    'WEST': 'west',
    'NE': 'northeast',
    'NW': 'northwest',
    'SE': 'southeast',
    'SW': 'southwest',
    'UP': 'up',
    'DOWN': 'down',
    'IN': 'enter',
    'OUT': 'exit',
    'LAND': 'land'
}


def generate_uuid() -> str:
    """Generate a UUID in the format used by the editor."""
    return str(uuid.uuid4())


def fetch_zil_source() -> str:
    """Fetch the ZIL source file from GitHub."""
    print(f"Fetching ZIL source from: {ZIL_URL}")
    with urllib.request.urlopen(ZIL_URL) as response:
        content = response.read().decode('utf-8')
    print(f"Fetched {len(content)} bytes")
    return content


def parse_room_definition(room_text: str) -> Optional[Dict[str, Any]]:
    """Parse a single ROOM definition from ZIL format."""
    room = {}
    
    # Extract room name (ID)
    name_match = re.match(r'<ROOM\s+([A-Z0-9-]+)', room_text)
    if not name_match:
        return None
    
    room_id = name_match.group(1)
    room['zil_id'] = room_id
    room['id'] = generate_uuid()
    
    # Extract description
    desc_match = re.search(r'\(DESC\s+"([^"]+)"\)', room_text)
    if desc_match:
        room['name'] = desc_match.group(1)
    else:
        room['name'] = room_id.replace('-', ' ').title()
    
    # Extract directions and transitions
    room['exits'] = {}
    room['blocked_exits'] = {}
    room['conditional_exits'] = {}
    
    for zil_dir, display_dir in DIRECTIONS.items():
        # Pattern for simple transition: (DIRECTION TO ROOM-NAME)
        simple_pattern = rf'\({zil_dir}\s+TO\s+([A-Z0-9-]+)\)'
        simple_match = re.search(simple_pattern, room_text)
        
        # Pattern for conditional transition: (DIRECTION TO ROOM-NAME IF FLAG)
        cond_pattern = rf'\({zil_dir}\s+TO\s+([A-Z0-9-]+)\s+IF\s+([A-Z0-9-]+)\)'
        cond_match = re.search(cond_pattern, room_text)
        
        # Pattern for blocked direction: (DIRECTION "message")
        blocked_pattern = rf'\({zil_dir}\s+"([^"]+)"\)'
        blocked_match = re.search(blocked_pattern, room_text)
        
        if cond_match:
            room['conditional_exits'][display_dir] = {
                'target': cond_match.group(1),
                'condition': cond_match.group(2)
            }
        elif simple_match:
            room['exits'][display_dir] = simple_match.group(1)
        elif blocked_match:
            room['blocked_exits'][display_dir] = blocked_match.group(1)
    
    # Extract LDESC (long description) if present
    ldesc_match = re.search(r'\(LDESC\s+"([^"]+)"\)', room_text)
    if ldesc_match:
        room['long_description'] = ldesc_match.group(1)
    
    return room


def extract_rooms(zil_content: str) -> List[Dict[str, Any]]:
    """Extract all ROOM definitions from ZIL content."""
    rooms = []
    room_pattern = r'<ROOM\s+[A-Z0-9-]+[^>]+>'
    
    for match in re.finditer(room_pattern, zil_content, re.DOTALL):
        room_text = match.group(0)
        room = parse_room_definition(room_text)
        if room:
            rooms.append(room)
    
    print(f"Extracted {len(rooms)} rooms")
    return rooms


def parse_object_definition(obj_text: str) -> Optional[Dict[str, Any]]:
    """Parse a single OBJECT definition from ZIL format."""
    obj = {}
    
    name_match = re.match(r'<OBJECT\s+([A-Z0-9-]+)', obj_text)
    if not name_match:
        return None
    
    obj_id = name_match.group(1)
    obj['id'] = obj_id
    
    desc_match = re.search(r'\(DESC\s+"([^"]+)"\)', obj_text)
    if desc_match:
        obj['name'] = desc_match.group(1)
    else:
        obj['name'] = obj_id.replace('-', ' ').title()
    
    in_match = re.search(r'\(IN\s+([A-Z0-9-]+)\)', obj_text)
    if in_match:
        obj['location'] = in_match.group(1)
    
    flags_match = re.search(r'\(FLAGS\s+([^)]+)\)', obj_text)
    obj['properties'] = []
    obj['flags'] = []
    if flags_match:
        flags = flags_match.group(1).split()
        obj['flags'] = flags
        for flag in flags:
            if flag in OBJECT_FLAGS:
                obj['properties'].append(OBJECT_FLAGS[flag])
    
    ldesc_match = re.search(r'\(LDESC\s+"([^"]+)"\)', obj_text)
    if ldesc_match:
        obj['description'] = ldesc_match.group(1)
    
    value_match = re.search(r'\(VALUE\s+(\d+)\)', obj_text)
    if value_match:
        obj['value'] = int(value_match.group(1))
    
    syn_match = re.search(r'\(SYNONYM\s+([^)]+)\)', obj_text)
    if syn_match:
        obj['synonyms'] = syn_match.group(1).split()
    
    return obj


def extract_objects(zil_content: str) -> List[Dict[str, Any]]:
    """Extract all OBJECT definitions from ZIL content."""
    objects = []
    obj_pattern = r'<OBJECT\s+[A-Z0-9-]+[^>]+>'
    
    for match in re.finditer(obj_pattern, zil_content, re.DOTALL):
        obj_text = match.group(0)
        obj = parse_object_definition(obj_text)
        if obj:
            objects.append(obj)
    
    print(f"Extracted {len(objects)} objects")
    return objects


def calculate_layout(rooms: List[Dict[str, Any]], id_map: Dict[str, str]) -> Dict[str, Tuple[int, int]]:
    """Calculate visual layout positions for rooms based on their connections."""
    positions = {}
    placed = set()
    
    dir_vectors = {
        'north': (0, -150),
        'south': (0, 150),
        'east': (200, 0),
        'west': (-200, 0),
        'northeast': (150, -100),
        'northwest': (-150, -100),
        'southeast': (150, 100),
        'southwest': (-150, 100),
        'up': (50, -150),
        'down': (50, 150),
        'enter': (100, 0),
        'exit': (-100, 0),
        'land': (0, 100)
    }
    
    # Build adjacency map using ZIL IDs
    adjacency = {}
    for room in rooms:
        zil_id = room['zil_id']
        adjacency[zil_id] = {}
        for direction, target in room.get('exits', {}).items():
            adjacency[zil_id][direction] = target
        for direction, info in room.get('conditional_exits', {}).items():
            if info.get('target'):
                adjacency[zil_id][direction] = info['target']
    
    # Start with WEST-OF-HOUSE as origin
    start_room = 'WEST-OF-HOUSE'
    if start_room not in [r['zil_id'] for r in rooms]:
        start_room = rooms[0]['zil_id'] if rooms else None
    
    if not start_room:
        return positions
    
    # BFS to place rooms
    positions[start_room] = (500, 300)
    placed.add(start_room)
    queue = [start_room]
    
    while queue:
        current = queue.pop(0)
        current_pos = positions[current]
        
        if current not in adjacency:
            continue
            
        for direction, target in adjacency[current].items():
            if target not in placed and target in [r['zil_id'] for r in rooms]:
                if direction in dir_vectors:
                    dx, dy = dir_vectors[direction]
                    new_x = current_pos[0] + dx
                    new_y = current_pos[1] + dy
                    
                    while (new_x, new_y) in positions.values():
                        new_x += 50
                        new_y += 30
                    
                    positions[target] = (new_x, new_y)
                    placed.add(target)
                    queue.append(target)
    
    # Place remaining rooms in a grid
    remaining = [r['zil_id'] for r in rooms if r['zil_id'] not in placed]
    grid_x, grid_y = 100, 2000
    for zil_id in remaining:
        positions[zil_id] = (grid_x, grid_y)
        grid_x += 200
        if grid_x > 2000:
            grid_x = 100
            grid_y += 150
    
    return positions


def convert_to_model_json(rooms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert parsed rooms to ArcaneAI model.json format.
    
    model.json structure:
    {
        "states": {
            "uuid": {
                "type": "StateShape",
                "id": "uuid",
                "userData": { "system_prompt": "...", ... },
                "name": "RoomName",
                "stateType": "NORMAL" or "START",
                "trigger": []
            }
        },
        "connections": {
            "uuid": {
                "type": "TriggerConnection",
                "id": "uuid",
                "userData": { "description": "...", ... },
                "source": { "node": "source-uuid", "port": "output0", "name": "SourceName" },
                "target": { "node": "target-uuid", "port": "input0", "name": "TargetName", "decoration": "..." },
                "name": "connection_name"
            }
        }
    }
    """
    model = {
        "states": {},
        "connections": {}
    }
    
    # Create ID mapping: ZIL room name -> UUID
    id_map = {}
    for room in rooms:
        id_map[room['zil_id']] = room['id']
    
    # Calculate positions for world.json later
    positions = calculate_layout(rooms, id_map)
    
    # Convert each room to a state
    for room in rooms:
        state_id = room['id']
        zil_id = room['zil_id']
        
        # Determine if this is the start state
        is_start = zil_id == 'WEST-OF-HOUSE'
        
        state = {
            "type": "StateShape",
            "id": state_id,
            "userData": {
                "system_prompt": room.get('long_description', f"You are in {room['name']}."),
                "ambient_sound_volume": 100
            },
            "name": room['name'].replace(' ', '').replace('-', ''),
            "stateType": "START" if is_start else "NORMAL",
            "trigger": []
        }
        
        model['states'][state_id] = state
        
        # Store position for later use
        room['position'] = positions.get(zil_id, (100, 100))
    
    # Create connections for exits
    for room in rooms:
        source_id = room['id']
        source_name = room['name'].replace(' ', '').replace('-', '')
        
        # Process simple exits
        for direction, target_zil_id in room.get('exits', {}).items():
            if target_zil_id in id_map:
                target_id = id_map[target_zil_id]
                target_room = next((r for r in rooms if r['zil_id'] == target_zil_id), None)
                target_name = target_room['name'].replace(' ', '').replace('-', '') if target_room else target_zil_id
                
                conn_id = generate_uuid()
                connection = {
                    "type": "TriggerConnection",
                    "id": conn_id,
                    "userData": {
                        "description": f"Go {direction}.",
                        "system_prompt": f"You go {direction} to {target_room['name'] if target_room else target_zil_id}.",
                        "sound_effect_volume": 100,
                        "sound_effect_duration": 2
                    },
                    "source": {
                        "node": source_id,
                        "port": "output0",
                        "name": source_name
                    },
                    "target": {
                        "node": target_id,
                        "port": "input0",
                        "decoration": "draw2d.decoration.connection.ArrowDecorator",
                        "name": target_name
                    },
                    "name": f"go_{direction}"
                }
                model['connections'][conn_id] = connection
        
        # Process conditional exits
        for direction, info in room.get('conditional_exits', {}).items():
            target_zil_id = info.get('target')
            condition = info.get('condition', '')
            
            if target_zil_id and target_zil_id in id_map:
                target_id = id_map[target_zil_id]
                target_room = next((r for r in rooms if r['zil_id'] == target_zil_id), None)
                target_name = target_room['name'].replace(' ', '').replace('-', '') if target_room else target_zil_id
                
                conn_id = generate_uuid()
                connection = {
                    "type": "TriggerConnection",
                    "id": conn_id,
                    "userData": {
                        "description": f"Go {direction}.",
                        "system_prompt": f"You go {direction} to {target_room['name'] if target_room else target_zil_id}.",
                        "conditions": [f"{condition.lower()} == true"] if condition else [],
                        "sound_effect_volume": 100,
                        "sound_effect_duration": 2
                    },
                    "dasharray": "- ",  # Dashed line for conditional connections
                    "source": {
                        "node": source_id,
                        "port": "output0",
                        "name": source_name
                    },
                    "target": {
                        "node": target_id,
                        "port": "input0",
                        "decoration": "draw2d.decoration.connection.ArrowDecorator",
                        "name": target_name
                    },
                    "name": f"go_{direction}"
                }
                model['connections'][conn_id] = connection
    
    return model, rooms


def create_world_view(rooms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create the world.json view file with state layouts."""
    world_view = {
        "viewId": "world",
        "viewType": "world",
        "stateLayouts": {}
    }
    
    for room in rooms:
        state_id = room['id']
        pos = room.get('position', (100, 100))
        world_view['stateLayouts'][state_id] = {
            "x": pos[0],
            "y": pos[1]
        }
    
    return world_view


def create_config_json() -> Dict[str, Any]:
    """Create a basic config.json for the Zork map."""
    return {
        "name": "Zork I: The Great Underground Empire",
        "description": "A port of the classic 1980 Infocom text adventure game Zork I",
        "author": "Converted from original Infocom ZIL source",
        "version": "1.0.0",
        "settings": {
            "enableInventory": True,
            "enableScore": True,
            "maxScore": 350
        }
    }


def main():
    """Main conversion routine."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Convert Zork I ZIL to ArcaneAI model.json')
    parser.add_argument('--output', '-o', default='maps/Zork/model.json',
                        help='Output path for model.json')
    args = parser.parse_args()
    
    # Fetch and parse ZIL source
    zil_content = fetch_zil_source()
    rooms = extract_rooms(zil_content)
    objects = extract_objects(zil_content)
    
    if not rooms:
        print("ERROR: No rooms found!")
        return 1
    
    # Convert to model.json format
    model, rooms_with_positions = convert_to_model_json(rooms)
    
    # Create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write model.json
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    print(f"Wrote model.json to: {args.output}")
    
    # Write inventory.json with all takeable objects
    inventory_items = []
    for obj in objects:
        if 'TAKEBIT' in obj.get('flags', []):
            item = {
                "id": f"item-{obj['id'].lower()}",
                "name": obj['name'],
                "location": obj.get('location', 'unknown'),
            }
            if obj.get('description'):
                item['description'] = obj['description']
            if obj.get('value'):
                item['value'] = obj['value']
            if obj.get('synonyms'):
                item['synonyms'] = [s.lower() for s in obj['synonyms']]
            props = []
            if 'WEAPONBIT' in obj.get('flags', []):
                props.append('weapon')
            if 'FOODBIT' in obj.get('flags', []):
                props.append('food')
            if 'LIGHTBIT' in obj.get('flags', []):
                props.append('light')
            if 'CONTBIT' in obj.get('flags', []):
                props.append('container')
            if 'SACREDBIT' in obj.get('flags', []):
                props.append('treasure')
            if props:
                item['properties'] = props
            inventory_items.append(item)
    
    inventory_path = os.path.join(output_dir, 'inventory.json')
    with open(inventory_path, 'w', encoding='utf-8') as f:
        json.dump({"items": inventory_items}, f, indent=2, ensure_ascii=False)
    print(f"Wrote inventory.json to: {inventory_path}")
    
    # Write config.json
    config_path = os.path.join(output_dir, 'config.json')
    config = create_config_json()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"Wrote config.json to: {config_path}")
    
    # Create views directory and write world.json
    views_dir = os.path.join(output_dir, 'views')
    os.makedirs(views_dir, exist_ok=True)
    
    world_view = create_world_view(rooms_with_positions)
    world_path = os.path.join(views_dir, 'world.json')
    with open(world_path, 'w', encoding='utf-8') as f:
        json.dump(world_view, f, indent=2, ensure_ascii=False)
    print(f"Wrote world.json to: {world_path}")
    
    # Print statistics
    print(f"\n=== Conversion Complete ===")
    print(f"States: {len(model['states'])}")
    print(f"Connections: {len(model['connections'])}")
    print(f"Inventory items: {len(inventory_items)}")
    
    return 0


if __name__ == '__main__':
    exit(main())