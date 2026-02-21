# Developer Server Konzept

## Übersicht

Ein neuer `developer.py` Server für die Game Engine, der speziell für die Entwicklung und das Testen von Spielen aus dem Editor heraus konzipiert ist.

## Architektur

### Drei Startmöglichkeiten (mutual exclusive)

```
game/src/
├── main.py       # CLI-Version (lokale Konsole)
├── server.py     # Web-Version (Production, Multi-Session)
└── developer.py  # Web-Version (Editor, Single-Session, Hot-Reload)
```

**Alle drei Server nutzen Port 9000** - da nie zwei gleichzeitig laufen.

### Development Setup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT SETUP                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────────┐     ┌─────────────────────────────────┐
│  Editor UI  │────▶│  Editor Backend  │────▶│  Developer Server               │
│  (Vue.js)   │     │  (FastAPI)       │     │  (developer.py)                 │
│  Port 8080  │     │  Port 8000       │     │  Port 9000                      │
└─────────────┘     └──────────────────┘     └─────────────────────────────────┘
                            │                        │
                    ┌───────┴───────┐               │
                    │ Proxy Routes: │               │
                    │ /dev/chat     │───────────────┤
                    │ /dev/setState │               │
                    │ /dev/setInv   │               │
                    │ /dev/reload   │               │
                    │ /dev/reset    │               │
                    │ /dev/status   │               │
                    └───────────────┘               │
                                                   │
                                           ┌───────┴───────┐
                                           │  GameEngine   │
                                           │  + StateEngine│
                                           │  + Inventory  │
                                           │  + Audio      │
                                           └───────────────┘
```

## Game Engine Server Vergleich

| Feature                | main.py (CLI) | server.py (Web) | developer.py (Editor) |
|------------------------|---------------|-----------------|----------------------|
| Port                   | -             | 9000            | 9000                 |
| Session Management     | Single        | Multi (UUID)    | Single               |
| Audio/Sounds           | ✅ Local      | ✅ WebSocket    | ✅ Local             |
| Input                  | CLI stdin     | REST /api/chat  | REST /chat           |
| State Navigation       | Via Game      | Via Game        | REST /setState       |
| Inventory Control      | Via Game      | Via Game        | REST /setInventory   |
| Hot Reload             | ❌            | ❌              | ✅ REST /reload      |
| Full Reset             | Restart       | New Session     | REST /reset          |
| Auth                   | ❌            | Cookie-based    | ❌ (localhost only)  |
| UI served              | ❌            | ✅ /ui          | ❌ (via Editor)      |

## Developer Server Endpoints

### `POST /chat`
Chat-Befehl an die Game Engine senden.

```json
Request:
{
  "text": "look around"
}

Response:
{
  "response": "You see a dark corridor...",
  "state": "corridor_1",
  "inventory": {"torch": 1, "key": 0}
}
```

### `POST /setState`
State Engine direkt in einen bestimmten State versetzen (für Testing).

```json
Request:
{
  "state": "treasure_room"
}

Response:
{
  "success": true,
  "state": "treasure_room",
  "inventory": {"torch": 1, "key": 0}
}
```

### `POST /setInventory`
Inventory direkt setzen (für Testing von Bedingungen).

```json
Request:
{
  "inventory": {"torch": 1, "key": 3, "gold": 100}
}

Response:
{
  "success": true,
  "inventory": {"torch": 1, "key": 3, "gold": 100}
}
```

### `POST /reload`
Model neu laden (nach Änderungen im Editor), dabei State und Inventory beibehalten.

```json
Request: (empty or optional)
{
  "preserveState": true,    // default: true
  "preserveInventory": true // default: true
}

Response:
{
  "success": true,
  "previousState": "corridor_1",
  "currentState": "corridor_1",  // or "start" if previous state was deleted
  "inventory": {"torch": 1, "key": 0},
  "message": "Model reloaded, state preserved"
}
```

**Reload Logik:**
1. Aktuellen State-Namen und Inventory merken
2. `model.json` neu laden
3. Versuchen, zum vorherigen State zurückzukehren
4. Falls State nicht mehr existiert → zum Start-State gehen
5. Inventory wiederherstellen (falls `preserveInventory: true`)

### `POST /reset`
Kompletter Reset - lädt alles neu und setzt Inventory auf Anfangswerte.

```json
Request: (empty)

Response:
{
  "success": true,
  "state": "start",
  "inventory": {"torch": 0, "key": 0},
  "message": "Game fully reset"
}
```

### `GET /status`
Aktuellen Zustand abfragen.

```json
Response:
{
  "state": "corridor_1",
  "inventory": {"torch": 1, "key": 0},
  "availableStates": ["start", "corridor_1", "treasure_room", ...],
  "modelLoaded": true,
  "lastReload": "2024-02-21T14:30:00Z"
}
```

## Editor Backend Proxy Routes

Das Editor Backend (Port 8000) proxyt die Anfragen zum Developer Server:

```python
# editor/server/src/routes/developer_routes.py

DEVELOPER_SERVER_URL = "http://localhost:9000"

@router.post("/dev/chat")
async def dev_chat(data: ChatMessage):
    response = httpx.post(f"{DEVELOPER_SERVER_URL}/chat", json=data.dict())
    return response.json()

@router.post("/dev/setState")
async def dev_set_state(data: SetStateRequest):
    response = httpx.post(f"{DEVELOPER_SERVER_URL}/setState", json=data.dict())
    return response.json()

# ... weitere Proxy-Routes
```

## Editor UI Integration

### Kontextmenü Integration (StateShape.js)

Das bestehende Kontextmenü in `editor/ui/public/shared/StateShape.js` wird erweitert:

```javascript
// Bestehendes Kontextmenü
items: {
    "add": {name: "Add Trigger"},
    "sep1": "---------",
    "start": {name: "Start Node"},
    "normal": {name: "Normal Node"},
    "end": {name: "End Node"},
    "sep2": "---------",
    "setActiveState": {name: "🎮 Set as Active State"},  // NEU
    "sep3": "---------",                                  // NEU
    "delete": {name: "Delete"},
}

// Im callback:
case "setActiveState":
    // C2V = Canvas to Vue (bestehende Konvention)
    window.parent.postMessage({
        type: "C2V_SET_ACTIVE_STATE",
        stateName: this.getName()
    }, "*");
    break;
```

### Event Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StateShape.js (iframe)                                                       │
│   └── Kontextmenü "Set as Active State"                                     │
│        └── window.parent.postMessage({type: "C2V_SET_ACTIVE_STATE", ...})   │
└───────────────────────────────────────────────────────────────────────────────
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CanvasGame.vue (parent)                                                      │
│   └── window.addEventListener("message", handler)                            │
│        └── if (event.data.type === "C2V_SET_ACTIVE_STATE")                  │
│             └── this.$store.dispatch('developer/setActiveState', stateName) │
└───────────────────────────────────────────────────────────────────────────────
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ developer.js (Vuex Store)                                                    │
│   └── action: setActiveState(stateName)                                      │
│        └── axios.post('/dev/setState', {state: stateName})                  │
└───────────────────────────────────────────────────────────────────────────────
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Editor Backend (developer_routes.py)                                         │
│   └── POST /dev/setState                                                     │
│        └── httpx.post('http://localhost:9000/setState', ...)                │
└───────────────────────────────────────────────────────────────────────────────
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Developer Server (developer.py)                                              │
│   └── POST /setState                                                         │
│        └── game_engine.state_engine.set_state(stateName)                    │
└───────────────────────────────────────────────────────────────────────────────
```

### Aktionen im Editor

1. **State auswählen** (Rechtsklick → "Set as Active State") → `/dev/setState`
2. **Chat testen** → `/dev/chat`
3. **Inventory manipulieren** → `/dev/setInventory`
4. **Nach Änderungen** → `/dev/reload` (automatisch nach Save?)
5. **Neustart** → `/dev/reset`

## Workflow im Editor

```
┌────────────────────────────────────────────────────────────────────┐
│                    EDITOR UI (CanvasGame.vue)                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│  │   State Diagram     │    │   Developer Panel                │  │
│  │   ┌───┐    ┌───┐   │    │                                  │  │
│  │   │ A │───▶│ B │   │    │  Current State: [corridor_1  ▼]  │  │
│  │   └───┘    └───┘   │    │                                  │  │
│  │     │        │     │    │  Inventory:                      │  │
│  │     ▼        ▼     │    │  torch: [1 ] key: [0 ] gold: [5] │  │
│  │   ┌───┐    ┌───┐   │    │                                  │  │
│  │   │ C │    │ D │◀──┼────┼── [Set as Active State]          │  │
│  │   └───┘    └───┘   │    │                                  │  │
│  │                    │    │  ┌─────────────────────────────┐ │  │
│  │  [Save] [Reload]   │    │  │ Chat:                       │ │  │
│  └─────────────────────┘    │  │ > look around              │ │  │
│                             │  │ You see a dark corridor... │ │  │
│                             │  │ > _                        │ │  │
│                             │  └─────────────────────────────┘ │  │
│                             │                                  │  │
│                             │  [Reload Model] [Full Reset]     │  │
│                             └──────────────────────────────────┘  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## Implementierungsplan

### Phase 1: Developer Server (game/src/developer.py)
- [ ] Basis-Server mit FastAPI (Port 9000)
- [ ] Single-Session GameEngine (wie main.py)
- [ ] Audio lokal abspielen (wie main.py)
- [ ] `/chat` Endpoint
- [ ] `/setState` Endpoint
- [ ] `/setInventory` Endpoint
- [ ] `/reload` Endpoint mit State-Preservation
- [ ] `/reset` Endpoint
- [ ] `/status` Endpoint

### Phase 2: Editor Backend Proxy (editor/server/src/routes/developer_routes.py)
- [ ] Proxy-Routes zu Developer Server (localhost:9000)
- [ ] Error Handling wenn Developer Server nicht läuft

### Phase 3: Editor UI Integration
- [ ] Developer Panel Component
- [ ] State-Selector mit "Set Active" Button
- [ ] Inventory Editor
- [ ] Chat Panel
- [ ] Auto-Reload nach Save (optional)

## Nutzung

```bash
# Option 1: CLI spielen
cd game/src && python main.py

# Option 2: Web-UI spielen (Production)
cd game/src && python server.py
# dann http://localhost:9000/ui

# Option 3: Editor Development
cd game/src && python developer.py
# Editor verbindet sich automatisch
```

## Sicherheitshinweise

- Developer Server sollte nur auf `localhost` lauschen
- Kein Auth notwendig (nur für lokale Entwicklung)
- Nicht für Production geeignet