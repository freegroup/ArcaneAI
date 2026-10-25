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

The game loop flows in two LLM stages: **User input → Stage 1 (LLM picks one function: a game action or a built-in one) → FunctionExecutor (StateEngine fires the action, Lua scripts update the Inventory) → Stage 2 (LLM tells the player what happened, in the game's personality) → Response + audio sent back**. A background step adjusts the companion's mood.

- **GameSession** (`session.py`) — Container for one player session; holds all components; `to_dict`/`restore_from_dict` for saved games
- **GameEngine** (`game_engine.py`) — Coordinates StateEngine, Inventory, and GameController; loads game definition from `maps/`
- **GameController** (`game_controller.py`) — Orchestrates one turn: `DecisionStage` (`stage_1_decision.py`, prompt from `prompt_builder.py`) → `FunctionExecutor` (`function_executor.py`) → `NarrationStage` (`stage_2_narration.py`); manages history and TTS
- **Built-in functions** (`builtin_functions/action_<name>.py`, class `Action<Name>`) — `keine_aktion`, `helfe_dem_spieler`, `on_system_error`; registered in `BuiltinRegistry`
- **CompanionDirector** (`companion_director.py`) — Companion mood (enum inventory variable `companion_mood`) and goal reminder (Telegram)
- **StateEngine** (`state_engine/engine.py`) — State machine executor: tracks current state, evaluates Lua-based conditions, executes transitions
- **Inventory** (`inventory.py`) — Key-value store (int/bool/string/enum) with Lua scripting for game variable logic
- **GameHistory** (`game_history.py`) — One entry per turn (input, function called, narration); `recent(count, chars)` for context limits

### Prompts (`game/prompts/`)

No prompt text is hard-coded in the engine. All prompts are YAML files in `game/prompts/` (`prompt_rule_stage1.yaml`, `prompt_rule_stage2_with_function.yaml`, `prompt_rule_stage2_without_function.yaml`, `prompt_rule_mood.yaml`, `prompt_rule_goal.yaml`, `prompt_builtin_functions.yaml`). A provider can override any file with `game/prompts/<provider>/<file>.yaml` (e.g. `game/prompts/qwen/`). The engine (not the model) picks stage 2's "with function" variant when a game action fired, else "without function".

### Provider/Factory Pattern

Swappable backends configured in `config.yaml`:

- **LLM**: `llm/llm_factory.py` → providers share `BaseLLMProvider.chat(messages, functions, max_tokens, label)` (stateless; functions are native tools without arguments; history carries earlier function calls). `OpenAICompatibleProvider` base: OpenAI, Gemini, DeepSeek, LiteLLM, Hermes, Ollama (/v1). `OllamaNativeProvider` base (think=False, num_ctx): Gemma, Qwen
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

#### Writing action descriptions (`description` in model.json)

Stage 1 picks the function by its description; stage 2 gets it as "what the player does" and in the list of possible actions. Every description follows the same pattern (German):

1. The player's intent in a few words, then a colon — `Ins Haus hineinkommen:`
2. One sentence on what happens: "Du"-form, present tense, factual. Facts stage 2 should tell stay here ("Dabei fällt dir ein Türschild auf", "das gelingt niemals"); jokes and narration style go into `after_fire` (`system_prompt` of the connection/trigger).
3. `Passt, wenn der Spieler …` with 2–4 typical phrasings in quotes, including questions/requests to the companion (`"kommst du rein?"`, `"gehen wir zum Baum?"`).
4. Same action → same wording in every room. No game mechanics, no function names. With two similar targets in one room (two doors), say which one is meant.

Measured on TheTipsyQuest (gemma4:26b): question-form requests like "kommst du rein?" went from 0/10 to 10/10 correct with this pattern.

## Key Configuration

`config.yaml` (project root, gitignored) controls:
- `maps_directory` / `game_name` — Which game to load
- `llms` — Named model definitions (provider, model, base_url, api_key, temperature, max_tokens, context_length)
- `llm` — Which named model runs what: `default`, `stage1` (function choice), `stage2` (narration), `mood`; plus `max_history_length`
- `voice` — TTS provider and settings
- `sound` — Sound effects directory
- `debug.llm` — Print the exact prompt and answer of every LLM call

Web saved games live in `sessions/web/<session_id>.json` (gitignored).

## Testing

No formal test suite. Editor server has ad-hoc test files:
- `editor/server/test_text_improvement.py`
- `editor/server/test_text_improver_direct.py`
