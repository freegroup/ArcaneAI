#!/usr/bin/env python3
"""Builds game packs for the ArcaneAI Flutter app.

For each game it copies the definition (model.json, config.json) and the
sounds it references into the app's asset tree, converting WAV to AAC (.m4a)
with macOS `afconvert`, and writes a `pack.json` manifest (every file with
size + sha256, and whether it ships in the bundle). It also writes a top-level
`catalog.json` listing the games.

Sound paths are resolved like the Python LocalJukebox:
  map/<f>     -> maps/<game>/soundfx/<f>
  global/<f>  -> game/soundfx/<f>
  <f>         -> game/soundfx/<f>
and flattened ('/' -> '__') into one folder per game.

Usage:
  tool/build_game_pack.py [GameName ...]   # default: TheTipsyQuest DramaLlama
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(APP)
ASSETS = os.path.join(APP, 'assets', 'games')

DEFAULT_GAMES = ['TheTipsyQuest', 'DramaLlama']


def referenced_sounds(model):
    refs = set()
    for state in model.get('states', {}).values():
        refs.add(state.get('userData', {}).get('ambient_sound'))
        for trigger in state.get('trigger', []):
            refs.add(trigger.get('sound_effect'))
    for conn in model.get('connections', {}).values():
        refs.add(conn.get('userData', {}).get('sound_effect'))
    return sorted(r for r in refs if r)


def source_path(game, ref):
    if ref.startswith('map/'):
        return os.path.join(ROOT, 'maps', game, 'soundfx', ref[4:])
    if ref.startswith('global/'):
        ref = ref[7:]
    return os.path.join(ROOT, 'game', 'soundfx', ref)


def asset_name(ref):
    """Flattened asset file name; must match soundAssetName() in the app."""
    base, ext = os.path.splitext(ref.replace('/', '__'))
    return base + ('.m4a' if ext.lower() == '.wav' else ext)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 16), b''):
            digest.update(block)
    return digest.hexdigest()


def file_entry(path, rel):
    return {'path': rel, 'size': os.path.getsize(path), 'sha256': sha256(path), 'bundled': True}


def build_game(game):
    with open(os.path.join(ROOT, 'maps', game, 'model.json'), encoding='utf-8') as handle:
        model = json.load(handle)
    with open(os.path.join(ROOT, 'maps', game, 'config.json'), encoding='utf-8') as handle:
        config = json.load(handle)

    out = os.path.join(ASSETS, game)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, 'sounds'))

    shutil.copyfile(os.path.join(ROOT, 'maps', game, 'model.json'), os.path.join(out, 'model.json'))
    shutil.copyfile(os.path.join(ROOT, 'maps', game, 'config.json'), os.path.join(out, 'config.json'))

    sounds, missing = {}, []
    for ref in referenced_sounds(model):
        src = source_path(game, ref)
        if not os.path.exists(src):
            missing.append(ref)
            continue
        name = asset_name(ref)
        dst = os.path.join(out, 'sounds', name)
        if dst.endswith('.m4a'):
            subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '128000', src, dst], check=True)
        else:
            shutil.copyfile(src, dst)
        sounds[ref] = file_entry(dst, f'sounds/{name}')

    manifest = {
        'id': game,
        'title': _title(config, game),
        'version': 1,
        'model': file_entry(os.path.join(out, 'model.json'), 'model.json'),
        'config': file_entry(os.path.join(out, 'config.json'), 'config.json'),
        'sounds': sounds,
    }
    with open(os.path.join(out, 'pack.json'), 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    size = sum(e['size'] for e in [manifest['model'], manifest['config'], *sounds.values()])
    print(f'  {game}: {len(sounds)} sounds, {size / 1e6:.1f} MB'
          + (f', MISSING {missing}' if missing else ''))
    return {'id': game, 'title': manifest['title']}


def _title(config, game):
    # The games carry no explicit title; derive a readable one from the id.
    return config.get('title') or re.sub(r'(?<!^)(?=[A-Z])', ' ', game)


def update_pubspec_assets(games):
    """Flutter bundles only files directly in a listed folder, not nested
    ones, so each game and its sounds/ subfolder must be listed explicitly."""
    pubspec = os.path.join(APP, 'pubspec.yaml')
    lines = ['    - assets/games/']
    for game in games:
        lines.append(f'    - assets/games/{game}/')
        lines.append(f'    - assets/games/{game}/sounds/')
    block = '\n'.join(lines)
    with open(pubspec, encoding='utf-8') as handle:
        text = handle.read()
    text = re.sub(r'(  assets:\n)(?:    - .*\n)*', f'\\1{block}\n', text, count=1)
    with open(pubspec, 'w', encoding='utf-8') as handle:
        handle.write(text)


def main():
    games = sys.argv[1:] or DEFAULT_GAMES
    os.makedirs(ASSETS, exist_ok=True)
    entries = [build_game(game) for game in games]
    with open(os.path.join(ASSETS, 'catalog.json'), 'w', encoding='utf-8') as handle:
        json.dump({'games': entries}, handle, ensure_ascii=False, indent=2)
    update_pubspec_assets(games)
    print(f'catalog.json: {len(entries)} games')


if __name__ == '__main__':
    main()
