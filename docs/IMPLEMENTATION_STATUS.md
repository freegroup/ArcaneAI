# Implementation Status - Overlay Pattern

## Datum: 2026-02-20

## Übersicht

Die Architektur wurde erfolgreich vom problematischen CCM (Content Change Manager) Pattern 
auf das **Overlay Pattern** migriert.

## Implementierte Komponenten

### 1. Model Store (`editor/ui/src/store/model.js`)
- **Single Source of Truth** für alle semantischen Daten
- States und Connections werden als normalisierte Objekte gespeichert
- Actions: `addState`, `updateState`, `deleteState`, `addConnection`, `deleteConnection`, `mergeModel`
- Backend-Persistenz via `model.json`

### 2. Views Store (`editor/ui/src/store/views.js`)  
- Speichert **nur Layout-Informationen** (x, y, routing)
- Multiple Views möglich: `world`, `encounter_xxx`
- Actions: `addStateToView`, `updateStateLayout`, `createEncounterView`, `saveAllViews`
- Backend-Persistenz via `/views/{viewId}.json`

### 3. ViewComposer (`editor/ui/src/utils/ViewComposer.js`)
- Kombiniert Model + View zu einem Canvas-tauglichen Format
- `compose(model, view)` → `{ states: [...], connections: [...], rafts: [...] }`
- Nur States/Connections mit Layout in der View werden inkludiert

### 4. CanvasGame.vue (World View)
- Lädt `model.json` in den Model Store
- Setzt `currentViewId = 'world'`
- Nutzt ViewComposer für Canvas-Rendering
- Reagiert auf Canvas-Events und propagiert zu Model + Views

### 5. CanvasEncounter.vue (Encounter View)
- Lädt zugehörige View mit `encounter_{name}` ID
- Nutzt **gleichen Model Store** wie World
- ViewComposer filtert nur relevante States/Connections

## Datenfluss

```
┌─────────────────────────────────────────────────────────┐
│                     User Action                          │
│                    (z.B. State erstellen)                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                Vue Component                             │
│    (CanvasGame.vue / CanvasEncounter.vue)               │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐           ┌─────────────────┐
│   Model Store   │           │   Views Store   │
│  (semantisch)   │           │   (layout)      │
│                 │           │                 │
│ - addState()    │           │ - addState      │
│ - updateState() │           │   ToView()      │
│ - deleteState() │           │ - updateState   │
│                 │           │   Layout()      │
└────────┬────────┘           └────────┬────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
                    ▼
         ┌─────────────────┐
         │  ViewComposer   │
         │   .compose()    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │     Canvas      │
         │   (postMessage) │
         └─────────────────┘
```

## Gelöste Probleme

### 1. Single Source of Truth
- **Vorher (CCM)**: Daten wurden in jedem Encounter dupliziert
- **Nachher**: Ein Model Store, Views sind nur Overlays

### 2. Synchronisation
- **Vorher**: Änderungen mussten manuell in alle Encounters propagiert werden
- **Nachher**: Änderung im Model ist automatisch überall sichtbar

### 3. Löschoperationen
- **Vorher**: State löschen hinterließ verwaiste Daten
- **Nachher**: `deleteState` entfernt State + zugehörige Connections aus Model und allen Views

### 4. Code-Komplexität
- **Vorher**: CCM mit komplexer Event-Verkettung
- **Nachher**: Klare, funktionale Komposition mit ViewComposer

## Bekannte Einschränkungen

1. **Legacy CCM**: Noch vorhanden für Backwards-Compatibility, aber deprecated
2. **Canvas Integration**: Nutzt noch `postMessage` statt direkter Store-Bindung
3. **Backend Migration**: Alte Encounter-Dateien müssen beim Laden migriert werden

## Nächste Schritte

- [ ] CCM vollständig entfernen nach erfolgreichen Tests
- [ ] Canvas-Komponente direkt an Vuex binden
- [ ] Automatische Migration alter Datenformate im Backend
- [ ] Unit Tests für ViewComposer

## Dateien

```
editor/ui/src/
├── store/
│   ├── model.js      # Semantische Daten (States, Connections)
│   ├── views.js      # Layout-Daten (Positionen, Routing)
│   └── index.js      # Store-Konfiguration
├── utils/
│   ├── ViewComposer.js    # Model + View → Canvas Format
│   └── LegacyMigration.js # Alte Formate konvertieren
└── views/
    ├── CanvasGame.vue      # World View
    └── CanvasEncounter.vue # Encounter Views