#!/usr/bin/env python3
"""
Sound Effects Organizer v3
--------------------------
Organizes sound files into a semantic folder structure using Google Gemini LLM.
Features:
- Strict main categories (Game Development standard)
- Flexible but guided subcategories
- Smart filename shortening (removing redundancy)
- JSON output parsing for reliability
"""

import os
import zipfile
import shutil
import re
import json
import yaml
import requests
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_DIR = Path(__file__).parent
SOUNDFX_DIR = BASE_DIR / "soundfx"
SOUNDFX_ZIP_DIR = BASE_DIR / "soundfx_zip"
CONFIG_FILE = BASE_DIR.parent / "config.yaml"  # Project root

# File size limit in MB (skip files larger than this)
MAX_FILE_SIZE_MB = 80

# Maximum parallel LLM requests
MAX_PARALLEL_REQUESTS = 4

# Allowed Main Categories (Strict)
MAIN_CATEGORIES = [
    "ambient", "character", "creature", "combat", "ui", "item", 
    "vehicle", "nature", "magic", "scifi", "horror", "movement", 
    "material", "water", "music", "machine", "weapon", "door", 
    "foley", "weather"
]

# Suggested Subcategories (Inspiration)
SUB_CATEGORY_HINTS = {
    "ambient": ["room_tone", "urban", "forest", "swamp", "cave", "hallway", "market"],
    "character": ["footstep", "jump", "land", "grunt", "voice", "breathe", "clothes"],
    "creature": ["growl", "roar", "attack", "die", "footstep", "wing", "breath"],
    "combat": ["sword", "punch", "kick", "impact", "gore", "whoosh", "block"],
    "ui": ["click", "hover", "confirm", "error", "popup", "start", "switch"],
    "vehicle": ["engine", "tire", "door", "pass_by", "crash", "horn", "siren"],
    "nature": ["wind", "rain", "thunder", "bird", "insect", "fire", "rock"],
    "magic": ["cast", "impact", "buff", "heal", "fire", "ice", "dark"],
    "scifi": ["laser", "robot", "alarm", "door", "scanner", "teleport", "drone"],
    "weapon": ["gun", "reload", "shell", "knife", "bow", "arrow", "explosion"]
}

class Config:
    @staticmethod
    def load():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

class LLMClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate_json(self, prompt: str, max_retries: int = 3) -> Optional[Dict]:
        """Call LLM and expect JSON response with retry logic."""
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,  # Low temperature for deterministic results
                            "responseMimeType": "application/json" # Force JSON
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and result["candidates"]:
                        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(raw_text)
                    else:
                        print(f"  LLM returned empty response (attempt {attempt + 1}/{max_retries})")
                else:
                    print(f"  LLM Error {response.status_code} (attempt {attempt + 1}/{max_retries}): {response.text}")
                    
            except requests.Timeout:
                print(f"  LLM Timeout (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"  LLM Exception (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Retry logic
            if attempt < max_retries - 1:
                print(f"  Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
            
        print(f"  All {max_retries} attempts failed. Using fallback categorization.")
        return None

class SoundOrganizer:
    def __init__(self):
        config = Config.load()
        api_key = config.get('llm', {}).get('api_key')
        model = config.get('llm', {}).get('model', 'gemini-3-pro-preview')
        
        if not api_key:
            raise ValueError("No API key found in config.yaml")
            
        print(f"Initializing with model: {model}")
        self.llm = LLMClient(api_key, model)
        
        # Cache for existing categories found on disk
        self.existing_subcats = {main: set() for main in MAIN_CATEGORIES}
        self.refresh_existing_categories()

    def refresh_existing_categories(self):
        """Scan SOUNDFX_DIR to know what categories we already have."""
        if not SOUNDFX_DIR.exists():
            return
            
        for main_dir in SOUNDFX_DIR.iterdir():
            if main_dir.is_dir() and main_dir.name in MAIN_CATEGORIES:
                for sub_dir in main_dir.iterdir():
                    if sub_dir.is_dir():
                        self.existing_subcats[main_dir.name].add(sub_dir.name)

    def get_existing_context_str(self) -> str:
        """Create a string summary of existing categories for the prompt."""
        lines = []
        categories_with_subs = []
        
        # Collect categories that have subcategories
        for main in sorted(MAIN_CATEGORIES):
            subs = sorted(list(self.existing_subcats[main]))
            if subs:
                categories_with_subs.append((main, subs))
        
        # Limit total categories shown to avoid context explosion
        MAX_CATEGORIES_SHOWN = 10
        MAX_SUBS_PER_CATEGORY = 3
        
        for main, subs in categories_with_subs[:MAX_CATEGORIES_SHOWN]:
            example_subs = ", ".join(subs[:MAX_SUBS_PER_CATEGORY])
            if len(subs) > MAX_SUBS_PER_CATEGORY:
                example_subs += f"... (+{len(subs) - MAX_SUBS_PER_CATEGORY} more)"
            lines.append(f"- {main}: {example_subs}")
        
        if len(categories_with_subs) > MAX_CATEGORIES_SHOWN:
            lines.append(f"... and {len(categories_with_subs) - MAX_CATEGORIES_SHOWN} more categories")
        
        return "\n".join(lines) if lines else "(No existing subcategories yet)"

    def process_file(self, folder_name: str, filename: str) -> Tuple[str, str, str]:
        """Decide category and new filename for a sound file."""
        
        context_str = self.get_existing_context_str()
        
        prompt = f"""You are an expert Audio Director for a video game.
Your task is to organize sound files into a strict folder structure and rename them cleanly.

INPUT FILE:
Path: "{folder_name}/{filename}"

STRICT GUIDELINES:
1. MAIN CATEGORY: Must be one of: {', '.join(MAIN_CATEGORIES)}
2. SUB CATEGORY: 
   - Use an existing one if it fits perfectly (see context below).
   - Or create a new one (one word, lowercase, singular/plural concept).
   - Example: 'footsteps', 'swords', 'explosions'. NOT 'sounds' or 'misc'.
3. FILENAME:
   - Max 30 chars.
   - Lowercase, underscores.
   - REMOVE redundant words that are already in Main/Sub categories.
   - Example: If category is 'creature/dog', filename 'dog_bark_loud' -> 'bark_loud'.
   - NO numbers if they are just generic counters (01, 002).
   - KEEP numbers if they describe specific variations (level_01, hit_02).

EXISTING STRUCTURE (Prefer reusing these!):
{context_str}

OUTPUT FORMAT (JSON):
{{
  "main_category": "string (one of the allowed list)",
  "sub_category": "string (short, descriptive, valid dirname)",
  "filename": "string (clean filename without extension)"
}}
"""
        data = self.llm.generate_json(prompt)
        
        if data and isinstance(data, dict):
            main = data.get("main_category", "").lower().strip()
            sub = data.get("sub_category", "").lower().strip()
            fname = data.get("filename", "").lower().strip()
            
            # Fallback validation
            if main not in MAIN_CATEGORIES:
                # Try to map unknown main category to 'foley' or 'ui' or fallback
                main = "foley" 
            
            # Clean strings
            sub = re.sub(r'[^a-z0-9_]', '', sub)
            fname = re.sub(r'[^a-z0-9_]', '', fname)
            
            # Enforce length limits roughly
            if len(sub) > 15: sub = sub[:15]
            if len(fname) > 40: fname = fname[:40]
            
            # Update cache immediately
            if main in self.existing_subcats:
                self.existing_subcats[main].add(sub)
                
            return main, sub, fname
            
        return "uncategorized", "files", filename.lower().replace(" ", "_")

def get_unique_path(base_dir: Path, filename: str, ext: str) -> Path:
    """Ensure unique filename by appending counter."""
    counter = 0
    clean_name = filename
    while True:
        suffix = f"_{counter:02d}" if counter > 0 else ""
        path = base_dir / f"{clean_name}{suffix}{ext}"
        if not path.exists():
            return path
        counter += 1

def process_single_file(args):
    """Process a single file (for parallel execution)."""
    organizer, info, zf_path, tmp_dir, file_index, total_files = args
    
    original_path = Path(info.filename)
    folder_context = str(original_path.parent)
    original_name = original_path.stem
    ext = original_path.suffix.lower()
    
    # Skip files larger than MAX_FILE_SIZE_MB
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if info.file_size > max_size_bytes:
        file_size_mb = info.file_size / (1024 * 1024)
        return {
            "status": "skipped",
            "index": file_index,
            "name": original_name,
            "reason": f"file {file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB"
        }
    
    try:
        # LLM Magic
        main_cat, sub_cat, new_name = organizer.process_file(folder_context, original_name)
        
        # Target Directory
        target_dir = SOUNDFX_DIR / main_cat / sub_cat
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Unique Filename
        final_path = get_unique_path(target_dir, new_name, ext)
        
        # Extract from ZIP
        with zipfile.ZipFile(zf_path, 'r') as zf:
            zf.extract(info, tmp_dir)
        
        source_extracted = tmp_dir / info.filename
        shutil.move(str(source_extracted), str(final_path))
        
        return {
            "status": "success",
            "index": file_index,
            "name": original_name,
            "original": info.filename,
            "new_path": f"{main_cat}/{sub_cat}/{final_path.name}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "index": file_index,
            "name": original_name,
            "error": str(e)
        }

def main():
    print("="*60)
    print(f"SoundFX Organizer v3 (Parallel Mode: {MAX_PARALLEL_REQUESTS} workers)")
    print("="*60)

    try:
        organizer = SoundOrganizer()
    except Exception as e:
        print(f"Startup Error: {e}")
        return

    # Process ZIP files
    zip_files = sorted(SOUNDFX_ZIP_DIR.glob("*.zip"))
    
    if not zip_files:
        print(f"No ZIP files found in {SOUNDFX_ZIP_DIR}")
        return
        
    for zip_path in zip_files:
        print(f"\nProcessing: {zip_path.name}")
        tmp_dir = SOUNDFX_ZIP_DIR / "tmp_extract"
        if tmp_dir.exists(): shutil.rmtree(tmp_dir)
        tmp_dir.mkdir()
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = [f for f in zf.infolist() if not f.is_dir() and 
                           Path(f.filename).suffix.lower() in ['.wav', '.mp3', '.ogg']]
                
                print(f"Found {len(file_list)} audio files.")
                
                # Prepare arguments for parallel processing
                tasks = [
                    (organizer, info, zip_path, tmp_dir, i+1, len(file_list))
                    for i, info in enumerate(file_list)
                ]
                
                # Process files in parallel
                with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as executor:
                    futures = {executor.submit(process_single_file, task): task for task in tasks}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        
                        if result["status"] == "skipped":
                            print(f"[{result['index']}/{len(file_list)}] {result['name']} - SKIPPED ({result['reason']})")
                        elif result["status"] == "success":
                            print(f"[{result['index']}/{len(file_list)}] {result['name']}")
                            print(f"   Original: {result['original']}")
                            print(f"   New:      {result['new_path']}")
                        elif result["status"] == "error":
                            print(f"[{result['index']}/{len(file_list)}] {result['name']} - ERROR: {result['error']}")
                    
        finally:
            if tmp_dir.exists(): shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()
