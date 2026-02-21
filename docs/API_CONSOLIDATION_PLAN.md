# API Konsolidierung: Store & ViewComposer

## Executive Summary

Die Analyse zeigt signifikante Redundanzen und Inkonsistenzen in der Store-API und dem ViewComposer. Dieser Plan beschreibt die notwendigen Konsolidierungen für eine homogene, sprechende API.

---

## 1. Kritische Redundanzen (Sofort beheben)

### 1.1 `gameName` ist 3x definiert ❌

| Store | Property | Problem |
|-------|----------|---------|
| `game.js` | `state.gameName` | ✅ Primäre Quelle |
| `model.js` | `state.gameName` | ❌ Redundant - ENTFERNEN |
| `views.js` | `state.gameName` | ❌ Redundant - ENTFERNEN |

**Lösung:** `gameName` nur in `game.js` behalten. Andere Module greifen via Getter zu:
```javascript
// In model.js und views.js:
rootGetters['game/gameName']
```

### 1.2 `gameConfig` ist 2x definiert ❌

| Store | Property | Problem |
|-------|----------|---------|
| `game.js` | `state.gameConfig` | ❌ Legacy |
| `config.js` | `state.config` | ✅ Neue kanonische Quelle |

**Lösung:** `gameConfig` aus `game.js` entfernen, nur `config.js` nutzen.

---

## 2. Getter-Namenskonventionen

### 2.1 model.js Getter umbenennen

| Aktuell | Problem | Vorschlag |
|---------|---------|-----------|
| `getState(id)` | "get" Präfix redundant | `stateById(id)` |
| `getConnection(id)` | "get" Präfix redundant | `connectionById(id)` |
| `allStates` | "all" Präfix unnötig | `states` |
| `allConnections` | "all" Präfix unnötig | `connections` |

### 2.2 views.js Getter umbenennen

| Aktuell | Problem | Vorschlag |
|---------|---------|-----------|
| `viewById(id)` | ✅ Konsistent | Beibehalten |
| `currentView` | ✅ Klar | Beibehalten |
| `currentStateLayouts` | Unklar | `stateLayoutsInCurrentView` |
| `currentConnectionRoutes` | Unklar | `connectionRoutesInCurrentView` |

---

## 3. Action-Namenskonventionen

### 3.1 Konsistentes Naming-Schema etablieren

**Pattern:** `<verb><Entity>[Modifier]`

| Kategorie | Verben | Beispiele |
|-----------|--------|-----------|
| CRUD | `load`, `save`, `create`, `delete` | `loadModel`, `saveView` |
| Mutation | `update`, `set`, `remove` | `updateState`, `removeConnection` |
| Bulk | `add`, `merge`, `clear` | `addStateToView`, `clearAllViews` |

### 3.2 Inkonsistente Actions in views.js

| Aktuell | Problem | Vorschlag |
|---------|---------|-----------|
| `addStateToView` | ✅ Gut | Beibehalten |
| `removeStateFromView` | ✅ Gut | Beibehalten |
| `updateCurrentViewLayout` | Unklar was "Layout" ist | `updateStateLayoutInCurrentView` |
| `setStateLayoutInCurrentView` | Fast identisch zu oben | **MERGE** mit `updateStateLayoutInCurrentView` |

---

## 4. ViewComposer Konsolidierung

### 4.1 Methoden-Übersicht

| Methode | Verantwortlichkeit | Verbleib |
|---------|-------------------|----------|
| `compose(model, view)` | Kernfunktion | ✅ ViewComposer |
| `extractModel(diagram)` | Kernfunktion | ✅ ViewComposer |
| `extractLayout(diagram)` | Kernfunktion | ✅ ViewComposer |
| `diffModels(old, new)` | Vergleichslogik | ✅ ViewComposer |
| `isEmpty(diagram)` | Utility | ⚠️ Verschieben zu Store-Getter |
| `count(diagram)` | Utility | ⚠️ Verschieben zu Store-Getter |
| `findById(diagram, id)` | Utility | ⚠️ Redundant mit Store-Getter |
| `copyLayoutToView` | View-Manipulation | ⚠️ Verschieben zu views.js Action |

### 4.2 Empfohlene Änderungen

**1. `isEmpty` und `count` → Store-Getter:**
```javascript
// model.js
getters: {
  isEmpty: state => Object.keys(state.states).length === 0,
  stateCount: state => Object.keys(state.states).length,
  connectionCount: state => Object.keys(state.connections).length
}
```

**2. `findById` entfernen** - redundant mit `stateById`/`connectionById`

**3. `copyLayoutToView` → views.js Action:**
```javascript
// views.js
actions: {
  copyLayoutBetweenViews({ commit, state }, { sourceViewId, targetViewId, stateIds })
}
```

---

## 5. Store-Modul Verantwortlichkeiten

### 5.1 Klare Trennung

| Modul | Verantwortlichkeit | Daten |
|-------|-------------------|-------|
| `game.js` | Spiel-Session, Name, Legacy | `gameName`, `gameDiagram` |
| `model.js` | Kanonische Daten (States, Connections) | `states`, `connections` |
| `views.js` | View-spezifische Layouts | `views`, `currentViewId` |
| `config.js` | Spiel-Konfiguration | `config` (NPC, Inventory, etc.) |

### 5.2 Cross-Modul Dependencies

```
game.js (Orchestrator)
    ├── model.js (Daten)
    ├── views.js (Layout)
    └── config.js (Konfiguration)
```

---

## 6. Implementierungsplan

### Phase 1: Redundanzen entfernen (Kritisch)
1. [ ] `gameName` aus model.js und views.js entfernen
2. [ ] `gameConfig` aus game.js entfernen (nur config.js nutzen)

### Phase 2: Getter umbenennen
3. [ ] `getState` → `stateById`
4. [ ] `getConnection` → `connectionById`
5. [ ] `allStates` → `states`
6. [ ] `allConnections` → `connections`

### Phase 3: Actions konsolidieren
7. [ ] `updateCurrentViewLayout` und `setStateLayoutInCurrentView` mergen
8. [ ] `copyLayoutToView` von ViewComposer → views.js verschieben

### Phase 4: ViewComposer aufräumen
9. [ ] `isEmpty`, `count`, `findById` entfernen (Store-Getter nutzen)

### Phase 5: Komponenten anpassen
10. [ ] Alle Stellen mit direktem `this.$store.state` auf mapGetters umstellen
11. [ ] Import-Pfade aktualisieren

---

## 7. Finale API-Übersicht (Zielzustand)

### model.js
```javascript
// State
state: { states: {}, connections: {}, loading: false, error: null }

// Getters
states           // alle States
connections      // alle Connections
stateById(id)    // einzelner State
connectionById(id) // einzelne Connection
stateCount       // Anzahl States
connectionCount  // Anzahl Connections

// Actions
loadModel({ gameName })
saveModel()
updateState({ id, data })
removeState(id)
updateConnection({ id, data })
removeConnection(id)
```

### views.js
```javascript
// State
state: { views: {}, currentViewId: null, loading: false, error: null }

// Getters
views                          // alle Views
currentView                    // aktive View
viewById(id)                   // einzelne View
stateLayoutsInCurrentView      // Layouts in aktueller View
connectionRoutesInCurrentView  // Routes in aktueller View

// Actions
loadAllViews({ gameName })
saveAllViews()
setCurrentView(viewId)
addStateToView({ stateId, layout })
removeStateFromView({ stateId })
updateStateLayoutInCurrentView({ stateId, layout })
copyLayoutBetweenViews({ sourceViewId, targetViewId, stateIds })
```

### ViewComposer (Utils)
```javascript
// Kern-Methoden (bleiben)
compose(model, view)      // Model + View → Diagram
extractModel(diagram)     // Diagram → Model
extractLayout(diagram)    // Diagram → Layout
diffModels(oldModel, newModel)  // Model-Diff
```

---

## 8. Server-API Analyse

### 8.1 Endpunkt-Übersicht

| Route-Datei | HTTP | Pfad | Store-Action |
|-------------|------|------|--------------|
| `games_routes.py` | GET | `/api/v1/games/` | `games/loadGames` |
| | POST | `/api/v1/games/{game_name}` | `games/createGame` |
| | DELETE | `/api/v1/games/{game_name}` | `games/deleteGame` |
| `game_routes.py` | GET | `/api/v1/game/{game_name}` | `game/loadGame` |
| | PUT | `/api/v1/game/{game_name}` | `game/saveGame` |
| `views_routes.py` | GET | `/api/v1/game/{name}/model` | `model/loadModel` |
| | PUT | `/api/v1/game/{name}/model` | `model/saveModel` |
| | GET | `/api/v1/game/{name}/views` | `views/loadAllViews` |
| | GET | `/api/v1/game/{name}/views/{id}` | `views/loadView` |
| | PUT | `/api/v1/game/{name}/views/{id}` | `views/saveView` |
| | GET | `/api/v1/game/{name}/config` | `config/loadConfig` |
| | PUT | `/api/v1/game/{name}/config` | `config/saveConfig` |

### 8.2 Server-API Probleme

#### ⚠️ Problem 1: Model-Routen in `views_routes.py`

Model-Endpunkte (`/model`) sind in `views_routes.py` definiert, obwohl sie semantisch zu `model_routes.py` gehören würden.

**Status:** Akzeptabel - da Model, Views und Config zusammen das Overlay Pattern bilden.

#### ⚠️ Problem 2: Inkonsistente Funktionsnamen

| Server-Funktion | Konvention | Problem |
|-----------------|------------|---------|
| `list_games` | ✅ | Korrekt |
| `load_game` | ⚠️ | Sollte `get_game` sein |
| `save_game` | ⚠️ | Sollte `update_game` sein (REST) |
| `load_model` | ⚠️ | Sollte `get_model` sein |
| `save_model` | ⚠️ | Sollte `update_model` sein |

**Empfehlung:** Entweder durchgängig REST (`get`/`update`) ODER durchgängig semantisch (`load`/`save`). Aktuell ist `load`/`save` die Konvention - beibehalten.

### 8.3 Server ist OK ✅

Die Server-API ist insgesamt sauber strukturiert:
- Konsistentes Prefix: `/api/v1/`
- Logische Gruppierung der Routes
- REST-konforme HTTP-Methoden
- Naming-Konvention (`load`/`save`/`list`/`create`/`delete`) ist durchgängig

**Keine kritischen Änderungen erforderlich.**

---

## 9. Gesamt-Bewertung

| Komponente | Status | Handlungsbedarf |
|------------|--------|-----------------|
| **Server API** | ✅ Gut | Keine kritischen Änderungen |
| **model.js** | ⚠️ Mittel | Getter umbenennen, gameName entfernen |
| **views.js** | ⚠️ Mittel | Actions konsolidieren |
| **ViewComposer** | ⚠️ Mittel | Utility-Methoden entfernen |
| **game.js** | ❌ Kritisch | gameConfig entfernen (redundant) |
| **config.js** | ✅ Gut | Ist die kanonische Quelle für Config |
