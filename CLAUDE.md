# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArcaneAI is an AI-powered text adventure game platform. Players interact through natural language; an LLM generates responses guided by a state machine. Games are authored via a visual state diagram editor (Vue.js) and played in browser or terminal.

Primary content language is **German** (UI strings, game prompts, personality text).

## Running the Project

```bash
# Full development environment (editor UI + editor API + developer game server)
./start-development.sh
# → Editor UI:      http://localhost:8080
# → Editor API:     http://localhost:8000
# → Developer API:  http://localhost:9000

# Web game only
./start-web.sh
# → Web Game: http://localhost:9000/ui

# Console game only
./start-console.sh
```

### Setup (first time)

```bash
# Game backend
cd game && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Editor backend
cd editor/server && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Editor frontend
cd editor/ui && npm install
```


## Architecture

### Three Services

| Service | Tech | Port | Entry Point |
|---------|------|------|-------------|
| **Game Engine** | Python/FastAPI | 9000 | `game/src/server.py` (web), `game/src/developer.py` (dev), `game/src/main.py` (console) |
| **Editor API** | Python/FastAPI | 8000 | `editor/server/src/main.py` |
| **Editor UI** | Vue 3 / Vuetify 3 | 8080 | `editor/ui/src/main.js` |

### Game Engine Core (`game/src/`)

The game loop flows: **User input → GameController → LLM (with function-calling schema built from available actions) → StateEngine executes chosen action → Inventory updates → Response + audio sent back**.

- **GameSession** (`session.py`) — Container for one player session; holds all components
- **GameEngine** (`game_engine.py`) — Coordinates StateEngine, Inventory, and GameController; loads game definition from `maps/`
- **GameController** (`game_controller.py`) — Builds LLM prompts, sends requests, parses function-call responses, manages conversation history and TTS
- **StateEngine** (`state_engine/engine.py`) — State machine executor: tracks current state, evaluates Lua-based conditions, executes transitions
- **Inventory** (`inventory.py`) — Key-value store (int/bool/string) with Lua scripting for game variable logic
- **GameHistory** (`game_history.py`) — Structured conversation history with configurable max length

### Provider/Factory Pattern

Swappable backends configured in `config.yaml`:

- **LLM**: `llm/llm_factory.py` → OpenAI, Gemini, DeepSeek, Ollama, LiteLLM providers
- **TTS**: `voice/voice_factory.py` → Google Cloud TTS, OpenAI TTS, Console (no-op)
- **Audio**: `audio/` → PyAudio (console), WebSocket (browser), Null
- **Messaging**: `messaging/` → Console, WebSocket
- **Sound/Jukebox**: `sound/` → LocalJukebox (pygame), WebJukebox (browser)

### Editor Architecture (`editor/`)

- **API routes** in `editor/server/src/routes/`: games, encounters, views, sounds, developer, text_improver
- **Vue stores** (Vuex) in `editor/ui/src/store/`: game, games, encounters, sounds, model, views
- **Overlay Pattern**: Model store is the single source of truth for semantic data (states, connections). Views store holds only layout coordinates. `ViewComposer` merges them for canvas rendering — avoids data duplication.

### Game Definition Format (`maps/<game_name>/`)

Each game is a directory containing:
- `config.json` — Personality prompt (German text) + inventory definitions (key/value/type)
- `model.json` — States, triggers, actions, connections (the state machine graph)
- `views/` — Layout/position data for the visual editor (x/y coordinates, routing)

## Key Configuration

`config.yaml` (project root) controls:
- `maps_directory` / `game_name` — Which game to load
- `llm` — Provider, model, API key/URL, temperature, max_tokens, max_history_length
- `voice` — TTS provider and settings
- `sound` — Sound effects directory
- `debug.llm` — Toggle verbose LLM request/response logging

## Testing

No formal test suite. Editor server has ad-hoc test files:
- `editor/server/test_text_improvement.py`
- `editor/server/test_text_improver_direct.py`
