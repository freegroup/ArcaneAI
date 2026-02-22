# Architektur-Review: Game Editor State Diagram System

## Executive Summary

Der Game Editor verwendet ein **State-Diagram-basiertes System** zum Erstellen von interaktiven Spielen. Die Architektur zeigt einige gut durchdachte Patterns, aber das **Content Change Manager (CCM) Pattern** weist signifikante Schwächen auf, die zu Wartungsproblemen und Inkonsistenzen führen können.

---

## 1. Aktuelle Architektur-Übersicht

### 1.1 Systemkomponenten

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vue.js Application                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Vuex      │    │   Views/    │    │   ContentChange     │ │
│  │   Store     │◄───│   Components│◄───│   Manager (CCM)     │ │
│  │             │    │             │    │                     │ │
│  │ - game      │    │ - Canvas*   │    │ - handleStateChange │ │
│  │ - games     │    │ - Properties│    │ - handleConnection  │ │
│  │ - encounters│    │ - Dialogs   │    │   Change            │ │
│  │ - sounds    │    │             │    │ - etc.              │ │
│  └──────┬──────┘    └──────┬──────┘    └─────────────────────┘ │
│         │                  │                                    │
│         │         ┌────────▼────────┐                          │
│         │         │  postMessage    │                          │
│         │         │  Communication  │                          │
│         │         └────────┬────────┘                          │
│         │                  │                                    │
│  ┌──────▼──────────────────▼──────┐                            │
│  │         iframe                  │                            │
│  │  ┌─────────────────────────┐   │                            │
│  │  │  draw2d.js Canvas       │   │                            │
│  │  │  - StateShape           │   │                            │
│  │  │  - TriggerConnection    │   │                            │
│  │  │  - TriggerLabel         │   │                            │
│  │  └─────────────────────────┘   │                            │
│  └────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   FastAPI Backend Server      │
              │   - /api/v1/games            │
              │   - /api/v1/game/{name}      │
              │   - /api/v1/encounters       │
              │   - /api/v1/sounds           │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   File System                 │
              │   maps/{game_name}/           │
              │   ├── index.json (World)     │
              │   ├── encounters/            │
              │   │   ├── 001_start.json    │
              │   │   └── 002_tavern.json   │
              │   └── soundfx/               │
              └───────────────────────────────┘
```

### 1.2 Datenmodell

Das System hat ein **denormalisiertes Datenmodell**:

```
Game (index.json)
├── config: { personality, inventory[] }
└── diagram: [                    ◄─── World-Level States
      { type: "StateShape", id: "abc123", name: "Tavern", ... },
      { type: "TriggerConnection", id: "xyz789", source: {...}, target: {...} }
    ]

Encounter (encounters/001_start.json)
├── config: { encounter_prompt }
└── diagram: [                    ◄─── KOPIE der gleichen States!
      { type: "StateShape", id: "abc123", name: "Tavern", ... },  ◄─── DUPLIZIERT!
      { type: "TriggerConnection", id: "xyz789", ... }
    ]
```

---

## 2. Das CCM-Problem: Analyse

### 2.1 Was macht der ContentChangeManager?

Der CCM ist ein **Synchronisations-Manager**, der versucht, Änderungen an States/Connections über alle Diagrams hinweg konsistent zu halten:

```javascript
// ContentChangeManager.js - Das Pattern
static handleStateChange(emitter, data) {
  // 1. Update in World (gameDiagram)
  const gameDiagram = store.state.game.gameDiagram;
  _updateState(gameDiagram);

  // 2. Update in ALLEN Encounters
  const encounters = store.state.encounters.encounters;
  for (const [name, encounterData] of Object.entries(encounters)) {
    _updateState(encounterData.diagram);
  }
}
```

### 2.2 Kernprobleme des CCM-Ansatzes

#### Problem 1: **Data Duplication (Verletzung des DRY-Prinzips)**

```
┌─────────────────────────────────────────────────────────────────┐
│  AKTUELL: Daten werden KOPIERT                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  World Diagram        Encounter 1         Encounter 2           │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ State "A"   │     │ State "A"   │     │ State "A"   │       │
│  │ id: 123     │     │ id: 123     │     │ id: 123     │       │
│  │ name: "Foo" │     │ name: "Foo" │     │ name: "Foo" │       │
│  │ x: 100      │     │ x: 200      │     │ x: 300      │       │
│  │ y: 100      │     │ y: 150      │     │ y: 200      │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    CCM muss ALLE                                │
│                    synchronisieren!                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Konsequenzen:**
- Jede State-Änderung muss N+1 mal geschrieben werden (World + N Encounters)
- Race Conditions möglich wenn mehrere Updates gleichzeitig
- Inkonsistenzen wenn ein Update fehlschlägt

#### Problem 2: **Unvollständige Handler-Implementierung**

```javascript
// Diese Handler sind NUR STUBS!
static handleStateTriggerChange(emitter, data) {
  console.log(`StateTrigger changed:`, data.id);
  // KEINE IMPLEMENTIERUNG!
}

static handleStateAdded(emitter, data) {
  console.log(`State added:`, data.id);
  // KEINE IMPLEMENTIERUNG!
}

static handleStateRemoved(emitter, data) {
  console.log(`State removed:`, data.id);
  // KEINE IMPLEMENTIERUNG!
}
```

**Konsequenz:** Wenn ein State in einem Encounter hinzugefügt oder entfernt wird, wird dies NICHT in anderen Diagrams synchronisiert!

#### Problem 3: **Tightly Coupled Architecture**

Der CCM greift direkt auf den Vuex Store zu:
```javascript
import store from '@/store';

// Direkter Zugriff - keine Abstraktion
const gameDiagram = store.state.game.gameDiagram;
const encounters = store.state.encounters.encounters;
```

Dies verletzt das **Dependency Inversion Principle** und macht Testing schwierig.

#### Problem 4: **Inkonsistente Positions-Behandlung**

```javascript
// Position wird bei States entfernt...
const stateData = { ...data };
delete stateData.x;
delete stateData.y;

// ...aber bei Connections werden vertex entfernt
const connectionData = { ...data };
delete connectionData.vertex;
delete connectionData.routingMetaData;
```

Das implizite Wissen, welche Properties "lokal" vs "global" sind, ist nicht dokumentiert und schwer wartbar.

#### Problem 5: **Fehlende Transaktionen**

```javascript
// Mehrere Updates ohne Transaktionsgarantie
_updateState(gameDiagram);           // Step 1
for (const [name, data] of ...) {
  _updateState(data.diagram);        // Step 2, 3, 4, ...
}
// Was passiert wenn Step 3 fehlschlägt?
```

---

## 3. Architektur-Bewertung

### 3.1 Stärken

| Aspekt | Bewertung | Begründung |
|--------|-----------|------------|
| **Modularisierung** | ⭐⭐⭐⭐ | Gute Trennung in Vuex-Module |
| **Canvas-Isolation** | ⭐⭐⭐⭐ | iframe-Ansatz isoliert draw2d.js gut |
| **API-Design** | ⭐⭐⭐⭐ | RESTful, gut strukturierte Endpunkte |
| **Message-Pattern** | ⭐⭐⭐ | postMessage ermöglicht lose Kopplung |

### 3.2 Schwächen

| Aspekt | Bewertung | Begründung |
|--------|-----------|------------|
| **Datenmodell** | ⭐ | Starke Denormalisierung, Duplikation |
| **CCM-Pattern** | ⭐⭐ | Unvollständig, fehleranfällig |
| **Konsistenz** | ⭐⭐ | Keine Transaktionen, Race Conditions |
| **Testbarkeit** | ⭐⭐ | Tight Coupling zu Store |
| **Skalierbarkeit** | ⭐⭐ | O(n) Updates bei jeder Änderung |

### 3.3 Gesamtbewertung: **2.5 / 5 Sterne**

Das System funktioniert für kleine Spiele, aber die Architektur wird bei wachsender Komplexität problematisch.

---

## 4. Empfohlene Lösungsansätze

### Option A: **Normalisiertes Datenmodell** (Empfohlen)

```
┌─────────────────────────────────────────────────────────────────┐
│  BESSER: Single Source of Truth + Referenzen                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  States Registry (Global)       Encounters                      │
│  ┌─────────────────────┐       ┌─────────────────────┐         │
│  │ states: {           │       │ encounter_1: {      │         │
│  │   "123": {          │◄──────│   stateRefs: [      │         │
│  │     name: "Foo",    │       │     { id: "123",    │         │
│  │     triggers: [...] │       │       x: 200,       │         │
│  │   },                │       │       y: 150 }      │         │
│  │   "456": {...}      │       │   ]                 │         │
│  │ }                   │       │ }                   │         │
│  └─────────────────────┘       └─────────────────────┘         │
│                                                                 │
│  ✓ State-Daten nur EINMAL gespeichert                          │
│  ✓ Position ist encounter-spezifisch (wo es hingehört!)        │
│  ✓ Änderung an State = 1 Update                                │
│  ✓ Keine Synchronisation nötig                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Neues Datenmodell:**

```javascript
// states.js - NEUE Registry
{
  states: {
    "abc123": {
      id: "abc123",
      type: "StateShape",
      name: "Tavern",
      triggers: [...]
      // KEINE Position - die ist View-spezifisch!
    }
  },
  connections: {
    "xyz789": {
      id: "xyz789",
      type: "TriggerConnection",
      sourceState: "abc123",
      targetState: "def456",
      userData: {...}
      // KEINE vertices - die sind View-spezifisch!
    }
  }
}

// game.js - World View
{
  layout: {
    "abc123": { x: 100, y: 100 },  // Position in World
    "def456": { x: 300, y: 200 }
  },
  connectionRoutes: {
    "xyz789": { vertices: [...] }  // Routing in World
  }
}

// encounter.js - Encounter View
{
  layout: {
    "abc123": { x: 200, y: 150 },  // Andere Position!
  }
}
```

### Option B: **Event Sourcing Pattern**

```javascript
// Alle Änderungen als Events
const events = [
  { type: 'STATE_CREATED', payload: { id: '123', name: 'Foo' }, timestamp: ... },
  { type: 'STATE_RENAMED', payload: { id: '123', name: 'Bar' }, timestamp: ... },
  { type: 'STATE_MOVED', payload: { id: '123', view: 'world', x: 100, y: 100 }, timestamp: ... },
];

// Jedes Diagram wird aus Events rekonstruiert
function buildDiagram(events, viewFilter) {
  return events
    .filter(e => e.view === viewFilter || e.view === undefined)
    .reduce(applyEvent, initialState);
}
```

**Vorteile:**
- Volle Audit-Historie
- Undo/Redo trivial
- Keine Synchronisationsprobleme

### Option C: **Verbesserter CCM** (Minimal-Invasiv)

Falls eine große Refaktorierung nicht möglich ist:

```javascript
class ContentChangeManager {
  // Dependency Injection statt direktem Store-Zugriff
  constructor(store) {
    this.store = store;
  }

  // Transaktions-Wrapper
  async handleStateChange(emitter, data) {
    const transaction = new Transaction();
    try {
      transaction.begin();
      
      // Alle Updates sammeln
      const updates = this.collectStateUpdates(data);
      
      // Batch-Update mit Rollback bei Fehler
      await transaction.commit(updates);
    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }

  // Alle Handler VOLLSTÄNDIG implementieren
  handleStateAdded(emitter, data) {
    // Hier: State zu ALLEN Diagrams hinzufügen
  }

  handleStateRemoved(emitter, data) {
    // Hier: State aus ALLEN Diagrams entfernen
  }
}
```

---

## 5. Konkrete Handlungsempfehlungen

### Kurzfristig (Quick Wins)

1. **Fehlende CCM-Handler implementieren**
   - `handleStateAdded` - States in alle Diagrams einfügen
   - `handleStateRemoved` - States aus allen Diagrams entfernen
   - `handleStateTriggerChange` - Trigger synchronisieren

2. **Logging und Monitoring hinzufügen**
   ```javascript
   static handleStateChange(emitter, data) {
     const startTime = performance.now();
     // ... existing logic ...
     console.log(`CCM sync completed in ${performance.now() - startTime}ms`);
   }
   ```

3. **Unit Tests für CCM schreiben**
   - Mock-Store erstellen
   - Alle Sync-Szenarien testen

### Mittelfristig (Refactoring)

1. **Normalisiertes Datenmodell einführen**
   - Neue `states.js` Registry erstellen
   - Migration der bestehenden Daten
   - Getter/Computer Properties für Views

2. **CCM durch reaktive Computed Properties ersetzen**
   ```javascript
   // Vuex Getter
   getWorldDiagram: (state, getters, rootState) => {
     const states = rootState.states.states;
     const layout = state.worldLayout;
     return Object.values(states).map(s => ({
       ...s,
       ...layout[s.id]
     }));
   }
   ```

### Langfristig (Architektur-Evolution)

1. **Event Sourcing evaluieren**
   - Für Undo/Redo-Funktionalität
   - Für kollaboratives Editing

2. **GraphQL/Apollo Client evaluieren**
   - Automatische Cache-Normalisierung
   - Optimistische Updates
   - Subscription für Real-Time Updates

---

## 6. Fazit

Das CCM-Pattern war ein verständlicher Versuch, mit dem Problem der Daten-Duplikation umzugehen. Allerdings behandelt es **Symptome statt Ursachen**. Die eigentliche Lösung ist ein **normalisiertes Datenmodell**, bei dem:

1. **State-Daten nur einmal existieren** (Single Source of Truth)
2. **View-spezifische Daten (Position)** separat gespeichert werden
3. **Keine manuelle Synchronisation** nötig ist

Die Implementierung von Option A würde den CCM überflüssig machen und gleichzeitig die Codebasis vereinfachen, die Performance verbessern und Bugs durch Inkonsistenzen eliminieren.

---

---

## 7. Refactoring-Status (Update 20.02.2026)

### Durchgeführte Verbesserungen

#### ✅ views.js - Mutations konsolidiert
- `SET_VIEW` und `UPDATE_VIEW` zu einer Mutation zusammengeführt
- Neue `PATCH_VIEW` Mutation für partielle Updates
- Granulare `SET_STATE_LAYOUT` und `SET_CONNECTION_ROUTE` Mutations
- Entfernte Redundanz: von 7 auf 5 Mutations reduziert

#### ✅ model.js - Bereinigt
- Entfernte ungenutzte `SET_STATES` und `SET_CONNECTIONS` Mutations
- Verbesserte Dokumentation aller Mutations
- Konsistente Namenskonvention

#### ✅ game.js - Aufgeräumt
- Entfernter dead code
- Bessere Kommentare und Action-Gruppierung
- Klarere Struktur

#### ✅ game.js - Refactored zu "Orchestration Only"
- `gameDiagram` State ENTFERNT - wird on-the-fly aus model+views generiert
- Neue Rolle: Nur noch Config + Orchestrierung von Load/Save
- Legacy `gameDiagram` Getter leitet an `views/getWorldDiagram` weiter

### Finale Store-Architektur

```
┌───────────────────────────────────────────────────────────────────┐
│                       VUEX STORE STRUCTURE                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  game.js          model.js            views.js                    │
│  ┌─────────────┐  ┌─────────────┐    ┌─────────────────────────┐ │
│  │ gameConfig  │  │ states      │    │ views: {                │ │
│  │ - system_   │  │ connections │    │   world: {              │ │
│  │   prompt    │  │             │    │     stateLayouts: {...} │ │
│  │ - final_    │  │ Semantic    │    │     connectionRoutes    │ │
│  │   prompt    │  │ data only!  │    │   },                    │ │
│  │ - inventory │  │ No x/y!     │    │   encounter_xxx: {...}  │ │
│  │             │  │             │    │ }                       │ │
│  │ Orchestrate │  │             │    │                         │ │
│  │ load/save   │  │             │    │ View-specific x,y,      │ │
│  └─────────────┘  └─────────────┘    │ routing only            │ │
│        │                │            └───────────┬─────────────┘ │
│        │                │                        │               │
│        └────────────────┼────────────────────────┘               │
│                         │                                        │
│              ┌──────────▼──────────┐                            │
│              │  getWorldDiagram    │                            │
│              │  (views.js getter)  │                            │
│              │                     │                            │
│              │  Kombiniert:        │                            │
│              │  model + worldView  │                            │
│              │  → Legacy format    │                            │
│              └─────────────────────┘                            │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Nächste Schritte
1. **TypeScript Migration** - für bessere Type-Safety
2. **Unit Tests** - für Store-Actions
3. **E2E Tests** - für den Migration Flow

---

*Analyse erstellt am: 20.02.2026*
*Refactoring durchgeführt am: 20.02.2026*
*Reviewer: Software Architecture Analysis*
