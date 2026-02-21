# Implementierungsplan: Overlay Pattern

## Übersicht

### Neue Dateistruktur
```
maps/{game_name}/
├── model.json              ← NEU: Kanonisches Modell (states, connections)
├── config.json             ← NEU: Game-Config (prompts, inventory)
├── views/
│   ├── world.json          ← NEU: World Layout
│   └── encounter_{name}.json ← NEU: Encounter Layouts
├── index.json              ← DEPRECATED: Legacy (für Rückwärtskompatibilität)
├── encounters/             ← DEPRECATED: Legacy
│   └── *.json
└── soundfx/                ← Unverändert
```

### Neue JSON-Strukturen

**model.json** (Kanonisches Modell - KEIN Layout!)
```json
{
  "states": {
    "abc123": {
      "id": "abc123",
      "type": "StateShape",
      "name": "Tavern",
      "cssClass": "StateShape",
      "width": 100,
      "height": 100,
      "userData": {...},
      "labels": [
        { "id": "label1", "text": "enter", "userData": {...} }
      ]
    }
  },
  "connections": {
    "conn1": {
      "id": "conn1",
      "type": "TriggerConnection",
      "name": "path1",
      "source": { "node": "abc123", "port": "output0" },
      "target": { "node": "def456", "port": "input0" },
      "userData": { "condition": "hasKey" }
    }
  }
}
```

**config.json** (Game-Konfiguration)
```json
{
  "system_prompt": "...",
  "final_prompt": "...",
  "inventory": [...]
}
```

**views/world.json** (World View Layout)
```json
{
  "viewId": "world",
  "viewType": "world",
  "stateLayouts": {
    "abc123": { "x": 100, "y": 200 },
    "def456": { "x": 400, "y": 300 }
  },
  "connectionRoutes": {
    "conn1": {
      "vertex": [{ "x": 250, "y": 250 }]
    }
  }
}
```

**views/encounter_tavern.json** (Encounter View Layout)
```json
{
  "viewId": "encounter_tavern",
  "viewType": "encounter",
  "encounterConfig": {
    "encounter_prompt": "..."
  },
  "stateLayouts": {
    "abc123": { "x": 150, "y": 100 }
  },
  "connectionRoutes": {}
}
```

---

## Änderungen im Detail

### 1. Backend (Python/FastAPI)

#### Neue Routes: `views_routes.py`
- `GET /api/v1/game/{game}/model` - Lädt model.json
- `PUT /api/v1/game/{game}/model` - Speichert model.json
- `GET /api/v1/game/{game}/config` - Lädt config.json
- `PUT /api/v1/game/{game}/config` - Speichert config.json
- `GET /api/v1/game/{game}/views` - Listet alle Views
- `GET /api/v1/game/{game}/views/{view}` - Lädt eine View
- `PUT /api/v1/game/{game}/views/{view}` - Speichert eine View
- `DELETE /api/v1/game/{game}/views/{view}` - Löscht eine View

#### Migration Script
- Konvertiert bestehende `index.json` + `encounters/*.json` → neue Struktur
- Läuft beim ersten Laden eines Games

### 2. Frontend (Vue/Vuex)

#### Neue Stores

**store/model.js** - Kanonisches Modell
```javascript
state: {
  states: {},       // id → stateData
  connections: {}   // id → connectionData
}
mutations: UPDATE_STATE, REMOVE_STATE, UPDATE_CONNECTION, REMOVE_CONNECTION
actions: loadModel, saveModel
getters: allStates, allConnections, getState, getConnection
```

**store/views.js** - View Overlays
```javascript
state: {
  views: {},          // viewId → viewData
  currentViewId: null
}
mutations: SET_VIEW, UPDATE_STATE_LAYOUT, UPDATE_CONNECTION_ROUTE
actions: loadViews, saveView, loadView
getters: currentView, allViews, viewById
```

**store/config.js** - Game Config (ersetzt teilweise game.js)
```javascript
state: {
  systemPrompt: '',
  finalPrompt: '',
  inventory: []
}
```

#### Neuer Utility: `ViewComposer.js`
```javascript
class ViewComposer {
  // Model + View → draw2d-kompatibles Array
  static compose(model, view) {...}
  
  // draw2d Array → Model-Änderungen extrahieren
  static extractModelChanges(diagram, oldModel) {...}
  
  // draw2d Array → Layout-Änderungen extrahieren
  static extractLayoutChanges(diagram, oldView) {...}
}
```

#### Angepasste Views

**CanvasGame.vue** → nutzt ViewComposer für "world" View
**CanvasEncounter.vue** → nutzt ViewComposer für "encounter_{name}" View

#### Zu Entfernen
- `ContentChangeManager.js` - nicht mehr benötigt
- Teile von `game.js` und `encounters.js` werden in neue Stores migriert

### 3. Delete-Logik

Wenn ein State gelöscht wird:
1. `model/REMOVE_STATE` → Entfernt aus model.states
2. `views/REMOVE_STATE_FROM_ALL_VIEWS` → Iteriert über alle Views und entfernt Layout
3. Connections die diesen State referenzieren werden ebenfalls entfernt

```javascript
// In model.js action
async removeState({ commit, dispatch }, stateId) {
  // 1. Finde alle Connections die diesen State nutzen
  const connectionsToRemove = findConnectionsForState(stateId);
  
  // 2. Entferne Connections
  for (const connId of connectionsToRemove) {
    commit('REMOVE_CONNECTION', connId);
    dispatch('views/removeConnectionFromAllViews', connId, { root: true });
  }
  
  // 3. Entferne State aus Model
  commit('REMOVE_STATE', stateId);
  
  // 4. Entferne State-Layout aus allen Views
  dispatch('views/removeStateFromAllViews', stateId, { root: true });
}
```

---

## Subagent-Aufgabenverteilung

### Subagent 1: Backend Views Routes
- Neue `views_routes.py` erstellen
- Model, Config und Views Endpunkte
- In main.py registrieren

### Subagent 2: Frontend Stores (model.js, views.js, config.js)
- Neue Store-Module erstellen
- store/index.js anpassen
- Migrations-Logik für alte Daten

### Subagent 3: ViewComposer + Integration
- ViewComposer.js implementieren
- Integration in CanvasGame.vue
- Integration in CanvasEncounter.vue

### Subagent 4: Cleanup + Delete-Logik
- ContentChangeManager.js entfernen
- game.js/encounters.js bereinigen
- Delete-Logik für States/Connections

### Subagent 5: Migration + Rückwärtskompatibilität
- Backend Migration Script
- Frontend Auto-Migration beim Laden
- Legacy-Support für alte Dateien

---

## Kritische Entscheidungen

### 1. Wann wird das Model/View gespeichert?
- **Option A**: Sofort bei jeder Änderung (Auto-Save)
- **Option B**: Explizit über Save-Button
- **Empfehlung**: Option B mit Debounce (wie bisher)

### 2. Wie werden neue States hinzugefügt?
- State wird in model.json erstellt (ohne Position)
- Initiale Position wird in der aktiven View gesetzt
- Andere Views: State erscheint bei (0,0) oder ist unsichtbar

### 3. Was passiert wenn ein State in einer View nicht sichtbar ist?
- View kann `visibleStates: ["id1", "id2"]` Array haben
- Oder alle States sind sichtbar, aber manche haben kein Layout → Default Position
- **Empfehlung**: Alle States immer sichtbar, Default Position wenn kein Layout

### 4. Können Views States "verstecken"?
- **Empfehlung**: Nein, für Einfachheit sind alle States in allen Views sichtbar
- Die Position ist view-spezifisch

---

## Reihenfolge der Implementierung

1. **Backend Routes** (unabhängig)
2. **Frontend Stores** (unabhängig)  
3. **ViewComposer** (braucht Store-Struktur)
4. **Canvas Integration** (braucht Stores + ViewComposer)
5. **Migration** (braucht alles)
6. **Cleanup CCM** (am Ende)