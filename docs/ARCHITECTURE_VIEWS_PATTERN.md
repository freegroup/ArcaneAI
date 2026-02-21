# View-Patterns für JSON-Datenmodelle

## Das Problem

```
┌─────────────────────────────────────────────────────────────────┐
│  ANFORDERUNG                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Kanonisches Modell              Views                          │
│  ┌───────────────────┐          ┌──────────────────┐           │
│  │ State "Tavern"    │          │ World View       │           │
│  │ - id: "abc"       │──────────│ - Position (100,100)         │
│  │ - name: "Tavern"  │          │ - Routing: [...]  │           │
│  │ - triggers: [...] │          └──────────────────┘           │
│  │                   │          ┌──────────────────┐           │
│  │                   │──────────│ Encounter View   │           │
│  │                   │          │ - Position (200,150)         │
│  │                   │          │ - Routing: [...]  │           │
│  └───────────────────┘          └──────────────────┘           │
│                                                                 │
│  ✓ State-Daten sind IDENTISCH (name, triggers, etc.)           │
│  ✓ Layout-Daten sind VIEW-SPEZIFISCH (position, routing)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lösung 1: **Overlay Pattern** (Empfohlen)

### Konzept
Das kanonische Modell bleibt "rein" (ohne Layout). Jede View hat ein separates "Overlay" mit Layout-Informationen.

### Datenstruktur

```javascript
// ============================================
// CANONICAL MODEL (Single Source of Truth)
// ============================================
// Datei: maps/{game}/model.json
{
  "states": {
    "abc123": {
      "id": "abc123",
      "type": "StateShape",
      "name": "Tavern",
      "triggers": [
        { "id": "t1", "name": "enter", "actions": [...] }
      ]
    },
    "def456": {
      "id": "def456",
      "type": "StateShape", 
      "name": "Forest",
      "triggers": [...]
    }
  },
  "connections": {
    "conn1": {
      "id": "conn1",
      "type": "TriggerConnection",
      "source": { "node": "abc123", "port": "output0" },
      "target": { "node": "def456", "port": "input0" },
      "userData": { "condition": "hasKey" }
    }
  }
}

// ============================================
// VIEW OVERLAYS (View-spezifische Layouts)
// ============================================
// Datei: maps/{game}/views/world.json
{
  "viewId": "world",
  "visibleStates": ["abc123", "def456"],  // Welche States sichtbar
  "visibleConnections": ["conn1"],         // Welche Connections sichtbar
  "layout": {
    "abc123": { "x": 100, "y": 100 },
    "def456": { "x": 400, "y": 200 }
  },
  "routing": {
    "conn1": { 
      "vertices": [{ "x": 250, "y": 150 }]
    }
  }
}

// Datei: maps/{game}/views/encounter_tavern.json
{
  "viewId": "encounter_tavern",
  "visibleStates": ["abc123"],             // Nur Tavern sichtbar!
  "visibleConnections": [],                 // Keine Connections
  "layout": {
    "abc123": { "x": 200, "y": 150 }       // Andere Position!
  },
  "routing": {}
}
```

### Implementierung: View-Composer

```javascript
// viewComposer.js
class ViewComposer {
  /**
   * Komponiert ein vollständiges Diagramm aus Model + Overlay
   * @param {Object} model - Kanonisches Modell (states, connections)
   * @param {Object} overlay - View-spezifisches Layout
   * @returns {Array} - draw2d-kompatibles Diagram-Array
   */
  static compose(model, overlay) {
    const diagram = [];

    // 1. States mit Layout mergen
    for (const stateId of overlay.visibleStates) {
      const state = model.states[stateId];
      if (!state) continue;

      const layout = overlay.layout[stateId] || { x: 0, y: 0 };
      
      diagram.push({
        ...state,
        x: layout.x,
        y: layout.y
      });
    }

    // 2. Connections mit Routing mergen
    for (const connId of overlay.visibleConnections) {
      const connection = model.connections[connId];
      if (!connection) continue;

      const routing = overlay.routing[connId] || {};
      
      diagram.push({
        ...connection,
        vertex: routing.vertices || [],
        routingMetaData: routing.metaData || {}
      });
    }

    return diagram;
  }

  /**
   * Extrahiert Layout-Änderungen aus einem Diagramm
   * @param {Array} diagram - Aktuelles draw2d Diagramm
   * @param {Object} overlay - Bisheriges Overlay
   * @returns {Object} - Aktualisiertes Overlay
   */
  static extractOverlay(diagram, overlay) {
    const newOverlay = { ...overlay };
    newOverlay.layout = { ...overlay.layout };
    newOverlay.routing = { ...overlay.routing };

    for (const item of diagram) {
      if (item.type === 'StateShape') {
        newOverlay.layout[item.id] = { x: item.x, y: item.y };
      } else if (item.type === 'TriggerConnection') {
        newOverlay.routing[item.id] = {
          vertices: item.vertex || [],
          metaData: item.routingMetaData || {}
        };
      }
    }

    return newOverlay;
  }

  /**
   * Extrahiert Model-Änderungen aus einem Diagramm
   * @param {Array} diagram - Aktuelles draw2d Diagramm
   * @param {Object} model - Bisheriges Model
   * @returns {Object} - Aktualisiertes Model
   */
  static extractModel(diagram, model) {
    const newModel = {
      states: { ...model.states },
      connections: { ...model.connections }
    };

    for (const item of diagram) {
      if (item.type === 'StateShape') {
        // Extrahiere NUR Model-Daten, NICHT Layout
        const { x, y, ...modelData } = item;
        newModel.states[item.id] = modelData;
      } else if (item.type === 'TriggerConnection') {
        // Extrahiere NUR Model-Daten, NICHT Routing
        const { vertex, routingMetaData, ...modelData } = item;
        newModel.connections[item.id] = modelData;
      }
    }

    return newModel;
  }
}

export default ViewComposer;
```

### Vuex Store Integration

```javascript
// store/model.js - Kanonisches Modell
export default {
  namespaced: true,
  state: {
    states: {},
    connections: {}
  },
  mutations: {
    UPDATE_STATE(state, stateData) {
      state.states[stateData.id] = stateData;
    },
    UPDATE_CONNECTION(state, connData) {
      state.connections[connData.id] = connData;
    },
    REMOVE_STATE(state, stateId) {
      delete state.states[stateId];
    },
    REMOVE_CONNECTION(state, connId) {
      delete state.connections[connId];
    }
  },
  getters: {
    getState: (state) => (id) => state.states[id],
    getConnection: (state) => (id) => state.connections[id],
    allStates: (state) => Object.values(state.states),
    allConnections: (state) => Object.values(state.connections)
  }
};

// store/views.js - View Overlays
export default {
  namespaced: true,
  state: {
    views: {
      // 'world': { viewId, visibleStates, layout, routing },
      // 'encounter_1': { ... }
    },
    currentViewId: null
  },
  mutations: {
    SET_VIEW(state, { viewId, overlay }) {
      state.views[viewId] = overlay;
    },
    SET_CURRENT_VIEW(state, viewId) {
      state.currentViewId = viewId;
    },
    UPDATE_LAYOUT(state, { viewId, stateId, position }) {
      if (state.views[viewId]) {
        state.views[viewId].layout[stateId] = position;
      }
    },
    UPDATE_ROUTING(state, { viewId, connId, routing }) {
      if (state.views[viewId]) {
        state.views[viewId].routing[connId] = routing;
      }
    }
  },
  getters: {
    currentView: (state) => state.views[state.currentViewId],
    
    // COMPUTED VIEW: Kombiniert Model + Overlay
    currentDiagram: (state, getters, rootState) => {
      const overlay = getters.currentView;
      if (!overlay) return [];
      
      const model = {
        states: rootState.model.states,
        connections: rootState.model.connections
      };
      
      return ViewComposer.compose(model, overlay);
    }
  }
};
```

### Vorteile des Overlay Patterns

| Aspekt | Bewertung | Begründung |
|--------|-----------|------------|
| **Single Source of Truth** | ⭐⭐⭐⭐⭐ | Model-Daten nur einmal gespeichert |
| **Flexibilität** | ⭐⭐⭐⭐⭐ | Beliebige Views möglich |
| **Performance** | ⭐⭐⭐⭐ | Computed Views sind reaktiv |
| **Erweiterbarkeit** | ⭐⭐⭐⭐⭐ | Neue View-Properties einfach hinzufügbar |
| **Testbarkeit** | ⭐⭐⭐⭐⭐ | ViewComposer ist pure function |

---

## Lösung 2: **Projection Pattern** (CQRS-inspiriert)

### Konzept
Änderungen werden als Commands auf das Model angewendet. Views werden als Read-Only Projections berechnet.

```javascript
// ============================================
// COMMAND HANDLERS
// ============================================
const commandHandlers = {
  // Model Commands (ändern das kanonische Model)
  'RENAME_STATE': (model, { stateId, newName }) => {
    model.states[stateId].name = newName;
  },
  'ADD_TRIGGER': (model, { stateId, trigger }) => {
    model.states[stateId].triggers.push(trigger);
  },
  
  // View Commands (ändern NUR das View-Overlay)
  'MOVE_STATE': (views, { viewId, stateId, x, y }) => {
    views[viewId].layout[stateId] = { x, y };
  },
  'ROUTE_CONNECTION': (views, { viewId, connId, vertices }) => {
    views[viewId].routing[connId] = { vertices };
  }
};

// ============================================
// PROJECTION BUILDER
// ============================================
class ProjectionBuilder {
  static buildDiagram(model, viewOverlay) {
    return viewOverlay.visibleStates
      .map(id => ({
        ...model.states[id],
        ...viewOverlay.layout[id]
      }))
      .concat(
        viewOverlay.visibleConnections.map(id => ({
          ...model.connections[id],
          vertex: viewOverlay.routing[id]?.vertices || []
        }))
      );
  }
}
```

---

## Lösung 3: **Reactive Computed Views** (Vue-native)

### Konzept
Nutze Vue's Reaktivitätssystem für automatische View-Updates.

```javascript
// composables/useComputedDiagram.js
import { computed } from 'vue';
import { useStore } from 'vuex';

export function useComputedDiagram(viewId) {
  const store = useStore();
  
  // Reaktive Referenzen
  const model = computed(() => store.state.model);
  const overlay = computed(() => store.state.views.views[viewId]);
  
  // Computed Diagram - aktualisiert sich automatisch!
  const diagram = computed(() => {
    if (!overlay.value) return [];
    
    const states = overlay.value.visibleStates.map(id => ({
      ...model.value.states[id],
      x: overlay.value.layout[id]?.x || 0,
      y: overlay.value.layout[id]?.y || 0
    }));
    
    const connections = overlay.value.visibleConnections.map(id => ({
      ...model.value.connections[id],
      vertex: overlay.value.routing[id]?.vertices || []
    }));
    
    return [...states, ...connections];
  });
  
  // Handler für Canvas-Updates
  function handleCanvasUpdate(newDiagram) {
    // Trennen: Model-Daten vs Layout-Daten
    for (const item of newDiagram) {
      if (item.type === 'StateShape') {
        // Layout → View Store
        store.commit('views/UPDATE_LAYOUT', {
          viewId,
          stateId: item.id,
          position: { x: item.x, y: item.y }
        });
        
        // Model-Daten → Model Store (ohne x, y)
        const { x, y, ...modelData } = item;
        store.commit('model/UPDATE_STATE', modelData);
      }
    }
  }
  
  return {
    diagram,
    handleCanvasUpdate
  };
}
```

### Verwendung in der Komponente

```vue
<!-- CanvasGame.vue -->
<template>
  <div>
    <canvas-iframe 
      :diagram="diagram"
      @update="handleCanvasUpdate"
    />
  </div>
</template>

<script setup>
import { useComputedDiagram } from '@/composables/useComputedDiagram';

const { diagram, handleCanvasUpdate } = useComputedDiagram('world');
</script>
```

---

## Lösung 4: **GraphQL-Style Fragments** (Für komplexe Szenarien)

### Konzept
Definiere "Fragments" die beschreiben, welche Felder aus dem Model geholt und mit welchen View-Daten ergänzt werden.

```javascript
// fragments.js
const StateFragment = {
  modelFields: ['id', 'type', 'name', 'triggers'],
  viewFields: ['x', 'y']
};

const ConnectionFragment = {
  modelFields: ['id', 'type', 'source', 'target', 'userData'],
  viewFields: ['vertex', 'routingMetaData']
};

// Fragment Resolver
class FragmentResolver {
  static resolve(fragment, modelData, viewData) {
    const result = {};
    
    // Model-Felder kopieren
    for (const field of fragment.modelFields) {
      if (modelData[field] !== undefined) {
        result[field] = modelData[field];
      }
    }
    
    // View-Felder hinzufügen
    for (const field of fragment.viewFields) {
      if (viewData[field] !== undefined) {
        result[field] = viewData[field];
      }
    }
    
    return result;
  }
}
```

---

## Vergleich der Lösungen

| Lösung | Komplexität | Flexibilität | Refactoring-Aufwand | Empfehlung |
|--------|-------------|--------------|---------------------|------------|
| **Overlay Pattern** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Mittel | ✅ **Beste Wahl** |
| **Projection Pattern** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Hoch | Für Event Sourcing |
| **Reactive Computed** | ⭐⭐ | ⭐⭐⭐⭐ | Mittel | Vue 3 Composition API |
| **GraphQL Fragments** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Hoch | Für große Systeme |

---

## Empfehlung für Ihren Editor

### Migrationsplan: Overlay Pattern

**Phase 1: Neue Datenstrukturen**
```
maps/{game}/
├── model.json           ← NEU: Kanonisches Modell
├── views/
│   ├── world.json       ← NEU: World Layout
│   └── encounters/
│       ├── 001.json     ← NEU: Encounter 1 Layout
│       └── 002.json     ← NEU: Encounter 2 Layout
├── index.json           ← ALT: Für Rückwärtskompatibilität
└── encounters/          ← ALT: Für Rückwärtskompatibilität
```

**Phase 2: Store-Refactoring**
1. `store/model.js` - Kanonisches Modell
2. `store/views.js` - View Overlays mit Computed Getters
3. `ViewComposer.js` - Pure Functions für Merge/Split

**Phase 3: CCM entfernen**
Der ContentChangeManager wird obsolet, da:
- Model-Änderungen automatisch in alle Views propagieren (reaktiv)
- View-Änderungen nur das jeweilige Overlay betreffen

---

## Fazit

Das **Overlay Pattern** ist die beste Lösung für Ihr Problem:

1. **Klare Trennung**: Model (WAS) vs. View (WO)
2. **Kein Sync nötig**: Änderungen am Model sind automatisch in allen Views sichtbar
3. **Einfache Migration**: Bestehende JSON-Struktur kann schrittweise migriert werden
4. **draw2d-kompatibel**: ViewComposer erzeugt das gleiche Format wie bisher

```
┌─────────────────────────────────────────────────────────────────┐
│  VORHER: CCM synchronisiert Kopien                              │
│                                                                 │
│  State "A" ──copy──► State "A" ──copy──► State "A"             │
│  (World)            (Enc. 1)            (Enc. 2)               │
│      │                  │                   │                  │
│      └──────────────────┴───────────────────┘                  │
│                    CCM sync                                     │
├─────────────────────────────────────────────────────────────────┤
│  NACHHER: Views referenzieren ein Model                         │
│                                                                 │
│           ┌───────────────────┐                                │
│           │  State "A"        │ ◄── Single Source of Truth     │
│           │  (Model)          │                                │
│           └─────────┬─────────┘                                │
│                     │                                          │
│        ┌────────────┼────────────┐                             │
│        ▼            ▼            ▼                             │
│   World View   Enc. 1 View   Enc. 2 View                       │
│   (100,100)    (200,150)     (300,200)                         │
│                                                                 │
│  Keine Synchronisation nötig!                                   │
└─────────────────────────────────────────────────────────────────┘