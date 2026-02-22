# Store Architecture Analysis

## Current State - Legacy + New Mix

The current store architecture has evolved during the Overlay Pattern implementation, resulting in a mix of legacy patterns and the new architecture.

## Store Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         STORES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   game.js   │     │  config.js  │     │  games.js   │       │
│  │ Orchestrator│     │  Prompts &  │     │ Game List   │       │
│  │ + DUPLICATES│     │  Inventory  │     │             │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                   │                                    │
│         │ dispatches to     │                                    │
│         ▼                   ▼                                    │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  model.js   │     │  views.js   │     │encounters.js│       │
│  │   Semantic  │     │   Layout    │     │  Metadata   │       │
│  │States/Conns │     │  Positions  │     │  Only       │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                  │
│  ┌─────────────┐                                                │
│  │  sounds.js  │                                                │
│  │Sound Effects│                                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Store Analysis

### 1. `game.js` - Orchestrator ✅ CLEANED

**Purpose**: Orchestrates loading/saving across all stores

**State** (All clean now):
| Property | Status | Description |
|----------|--------|-------------|
| `gameName` | ✅ OK | Single source of truth |
| `loading` | ✅ OK | Orchestration status |
| `error` | ✅ OK | Orchestration status |

**Actions** (All clean now):
| Action | Status | Notes |
|--------|--------|-------|
| `loadGame()` | ✅ KEEP | Orchestration - coordinates all stores |
| `saveGame()` | ✅ KEEP | Orchestration - coordinates all stores |

**Getters** (All clean now):
| Getter | Status | Notes |
|--------|--------|-------|
| `gameName` | ✅ KEEP | Used by many components |
| `isLoading` | ✅ KEEP | UI status |
| `error` | ✅ KEEP | UI status |
| `gameDiagram` | ✅ OK | Delegates to `views/getWorldDiagram` |

---

### 2. `config.js` - Game Configuration (AUTHORITATIVE)

**Purpose**: Stores personality, inventory

**Status**: ✅ This is the authoritative source for config data

**State**:
| Property | Status |
|----------|--------|
| `systemPrompt` | ✅ Authoritative |
| `finalPrompt` | ✅ Authoritative |
| `inventory` | ✅ Authoritative |
| `gameName` | ⚠️ Duplicate of `game.gameName` |

---

### 3. `model.js` - Semantic Data (AUTHORITATIVE)

**Purpose**: Stores states and connections (without layout)

**Status**: ✅ Correctly implemented for Overlay Pattern

**State**:
| Property | Status |
|----------|--------|
| `states` | ✅ Semantic state data (no x/y) |
| `connections` | ✅ Semantic connection data (no vertices) |
| `gameName` | ⚠️ Duplicate |

---

### 4. `views.js` - Layout Data (AUTHORITATIVE)

**Purpose**: Stores view definitions with layout positions

**Status**: ✅ Correctly implemented for Overlay Pattern

**State**:
| Property | Status |
|----------|--------|
| `views` | ✅ View definitions with stateLayouts |
| `currentViewId` | ✅ Active view selection |
| `gameName` | ⚠️ Duplicate |

---

### 5. `encounters.js` - Encounter Metadata (SIMPLIFIED)

**Purpose**: ~~Stores encounter diagrams~~ → Now only metadata

**Status**: ⚠️ Partially cleaned, but legacy references remain

**State**:
| Property | Status |
|----------|--------|
| `encounters` | ✅ Metadata only (name, description) |
| `currentEncounterName` | ✅ Selection state |

**Legacy Issues**:
- `currentEncounterConfig` getter was used for `.diagram` access
- Components still reference `encounterConfig.diagram` (legacy)

---

## Legacy Patterns Still in Use

### 1. `ImportStateDialog.vue` - Legacy Diagram Access

```javascript
// LEGACY - accessing diagram from encounterConfig
encounterStateNames() {
  if (!this.currentEncounterConfig?.diagram ...) // ← LEGACY!
}
```

**Should be**:
```javascript
// NEW - use views store
encounterStateNames() {
  const view = this.$store.getters['views/currentView'];
  return new Set(Object.keys(view?.stateLayouts || {}));
}
```

### 2. Multiple `gameName` Sources

`gameName` is stored in:
- `game.js` ← Should be single source
- `config.js` 
- `model.js`
- `views.js`

---

## Refactoring Plan

### Phase 1: Remove Duplicates from `game.js`

1. Remove `gameConfig` state from `game.js`
2. Remove inventory mutations from `game.js`
3. Change `gameConfig` getter to delegate to `config/gameConfig`
4. Update components to use `config` store directly for inventory

### Phase 2: Fix Legacy References in Components

1. Update `ImportStateDialog.vue`:
   - Remove `currentEncounterConfig?.diagram` access
   - Use `views/currentView.stateLayouts` instead

### Phase 3: Consolidate `gameName`

1. Keep `gameName` only in `game.js`
2. Other stores receive it via action parameters
3. Remove duplicate `gameName` from `config.js`, `model.js`, `views.js`

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLEAN ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │   game.js   │  gameName, loading, error                      │
│  │ Orchestrator│  loadGame(), saveGame()                        │
│  └──────┬──────┘                                                │
│         │ dispatches to                                          │
│         ▼                                                        │
│  ┌──────┴──────┬─────────────┬─────────────┬─────────────┐     │
│  │             │             │             │             │     │
│  ▼             ▼             ▼             ▼             ▼     │
│ config.js   model.js     views.js    encounters.js  sounds.js  │
│ (prompts)   (semantic)   (layout)    (metadata)    (audio)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
                   MODEL (semantic)
                   ┌─────────────┐
                   │   states    │
                   │ connections │
                   └──────┬──────┘
                          │
                          │ ViewComposer.compose()
                          │
                          ▼
┌─────────────┐    ┌─────────────┐
│ World View  │    │Encounter    │
│ (all states)│    │View (subset)│
└─────────────┘    └─────────────┘
      │                   │
      ▼                   ▼
   CANVAS              CANVAS
```

## Migration Priority

| Priority | Task | Effort | Status |
|----------|------|--------|--------|
| ~~HIGH~~ | ~~Fix `ImportStateDialog.vue` legacy diagram access~~ | ~~Small~~ | ✅ DONE |
| ~~MEDIUM~~ | ~~Remove config duplicates from `game.js`~~ | ~~Medium~~ | ✅ DONE |
| LOW | Consolidate `gameName` to single source | Large | Pending |

---

## Completed Fixes

### ✅ ImportStateDialog.vue (Fixed 2026-02-21)

**Changes Made:**
- Removed `currentEncounterConfig` getter mapping from encounters store
- Removed legacy `encounterStateNames()` computed property that used `this.currentEncounterConfig?.diagram`
- Updated `gameStateNames()` to filter states using `statesInCurrentView` (IDs from views store)

**Result:** Now correctly uses Overlay Pattern - checks `views/currentView.stateLayouts` for state IDs

### ✅ game.js Cleanup (Fixed 2026-02-21)

**Removed:**
- `gameConfig` state (was duplicate of `config.js`)
- `SET_GAME_CONFIG` mutation
- `ADD_INVENTORY_ITEM`, `UPDATE_INVENTORY_ITEM`, `REMOVE_INVENTORY_ITEM` mutations
- `updateGameConfig()`, `addInventoryItem()`, `updateInventoryItem()`, `removeInventoryItem()` actions
- `gameConfig` getter

**Kept (essential for orchestration):**
- `gameName`, `loading`, `error` state
- `loadGame()`, `saveGame()` actions
- `gameName`, `isLoading`, `error`, `gameDiagram` getters

**Result:** `game.js` is now a pure orchestrator without duplicate data storage
