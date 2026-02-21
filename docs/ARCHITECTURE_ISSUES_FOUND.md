# Architektur-Probleme nach Subagent-Analyse

## Datum: 2026-02-20

## Kritische Bugs 🔴

### 1. ~~Fehlende Action `removeStateFromAllViews`~~ ✅ GEFIXT
**Schweregrad: KRITISCH** → **ERLEDIGT**

`model.js` ruft `views/removeStateFromAllViews` auf (Zeile ~164).

**Fix:** Action in views.js hinzugefügt (2026-02-20).

---

### 2. Dreifach-Duplizierter `gameName` State
**Schweregrad: MITTEL**

`gameName` existiert in 3 verschiedenen Stores:
- `model.js`: `state.gameName`
- `views.js`: `state.gameName`
- `game.js`: `state.gameName`

**Problem:** Synchronisation wird zum Albtraum, Daten können out-of-sync geraten.

**Empfehlung:** `gameName` nur in einem zentralen Store (z.B. `config.js` oder neuer `session.js`).

---

## Design-Probleme 🟡

### 3. CCM wird noch immer verwendet
**Schweregrad: MITTEL**

CCM wurde aus CanvasGame.vue entfernt, aber wird noch in anderen Komponenten verwendet:
- `ConnectionTriggerProperty.vue` → `CCM.handleConnectionChange()`
- `StateTriggerProperty.vue` → `CCM.handleStateTriggerChange()`
- `ImportStateDialog.vue` → `CCM.handleStateAdded()`

**Problem:** Zwei parallele Architekturen (CCM + Model/Views) existieren gleichzeitig.

**Empfehlung:** CCM komplett entfernen und alle Komponenten auf Model/Views migrieren.

---

### 4. 85% Code-Duplikation zwischen CanvasGame.vue und CanvasEncounter.vue
**Schweregrad: MITTEL**

Identisch:
- Template-Struktur
- CSS-Styles (100%)
- `composedDiagram` computed
- `handleCanvasUpdate()` 
- Message-Handler-Logik

**Unterschiede nur:**
| Aspekt | CanvasGame | CanvasEncounter |
|--------|------------|-----------------|
| iframe src | `/game/index.html` | `/encounter/index.html` |
| View ID | `'world'` | `encounter_${name}` |
| Extra Dialog | - | ImportStateDialog |

**Empfehlung:** Gemeinsame `BaseCanvas.vue` Komponente erstellen.

---

### 5. Redundante Mutations in views.js
**Schweregrad: NIEDRIG**

- `UPDATE_VIEW` und `SET_VIEW` sind nahezu identisch
- `addStateToView` und `updateStateLayout` überlappen

**Empfehlung:** Konsolidieren.

---

### 6. Legacy-Speicherung noch aktiv
**Schweregrad: NIEDRIG**

`CanvasGame.vue` speichert noch in das alte `game/updateGameDiagram` für "Rückwärtskompatibilität":
```javascript
// CanvasGame.vue Zeile 114
this.$store.dispatch('game/updateGameDiagram', diagram)
```

**Empfehlung:** Nach erfolgreicher Migration entfernen.

---

## Positive Aspekte ✅

### ViewComposer ist sauber
- Alle Funktionen sind **pure und funktional**
- Keine Seiteneffekte
- Edge Cases gut behandelt (null, undefined, leere Arrays)
- Connections werden korrekt gefiltert (Source + Target müssen sichtbar sein)

### Model/Views Trennung ist korrekt
- `model.js`: Nur semantische Daten
- `views.js`: Nur Layout-Daten
- ViewComposer kombiniert beide sauber

### Error-Handling bei API-Calls
- Beide Stores haben konsistentes Error-Handling mit `SET_ERROR`

---

## Priorisierte Fixes

| Prio | Issue | Aufwand |
|------|-------|---------|
| 1 | `removeStateFromAllViews` fehlt | 5 min |
| 2 | CCM aus verbleibenden Komponenten entfernen | 2h |
| 3 | BaseCanvas.vue extrahieren | 1h |
| 4 | gameName zentralisieren | 30 min |
| 5 | Redundante Mutations konsolidieren | 20 min |

---

## Architektur-Bewertung

**Gesamtnote: 7/10** 🟢

Die Basis-Architektur (Overlay Pattern mit Model + Views) ist **solide und erweiterbar**.
Die Hauptprobleme sind:
1. Unvollständige Migration (CCM noch aktiv)
2. Code-Duplikation (zwei Canvas-Komponenten)
3. Ein kritischer Bug (fehlende Action)

Nach den priorisierten Fixes sollte die Architektur produktionsreif sein.