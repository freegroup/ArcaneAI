# STORY.md - Stilrichtlinien und Anforderungen

## Zweck dieses Dokuments
Dieses Dokument definiert, wie die STORY.md Datei gestaltet und geschrieben werden soll. Es dient als Referenz für zukünftige Arbeit am Story-Plot.

---

## Grundprinzipien

### 1. Lesbarkeit
- Die STORY.md soll ein gut lesbares, fließendes Dokument sein
- Text in natürlicher Fließform, nicht in Stichpunkten oder Aufzählungen wo Prosa besser passt
- Klare Absätze mit logischem Aufbau

### 2. Keine Meta-Kommentare
- **KEINE** Warnungen wie "⚠️ WICHTIG:"
- **KEINE** Ankerungen wie "BEACHTE:" oder "HINWEIS:"
- **KEINE** direkten Anweisungen an den Leser
- Alle Informationen ergeben sich natürlich aus dem Text

### 3. Sprache
- Deutsch
- Beschreibender, erzählerischer Stil
- Präzise, aber nicht technisch
- Professionell, aber zugänglich

### 4. Struktur

#### Hauptabschnitte:
1. **Setting & Storyplay** - Präambel, die dem Spieler den Einstieg in die Welt gibt
2. **Grundidee** - Das zentrale Konzept der Geschichte (Designer-Perspektive)
3. **Räume & States** - Einzelne Räume mit:
   - **Raumname** als Überschrift
   - **Raumbeschreibung** als Fließtext (Atmosphäre, Sinneseindrücke)
   - **Übergänge** als Fließtext (Vorbedingungen, Interaktionen, Verbindungen zu anderen Räumen)
   - **Notizen**  Arbeitsbereich für Ideen

### 5. Inkrementelle Entwicklung
- Die STORY.md wird schrittweise entwickelt
- Neue Informationen werden organisch in den bestehenden Text eingearbeitet
- Konsistenz wird kontinuierlich geprüft
- Platzhalter wie `[Details folgen]` sind erlaubt, aber werden sukzessive ersetzt

### 6. Konsistenzprüfung
- Bei jeder Ergänzung wird geprüft, ob sie logisch zum Bestehenden passt
- Widersprüche werden sofort angesprochen
- Unklarheiten werden hinterfragt

---

## Beispiel für guten Stil

### Allgemeiner Text
✅ **Gut:**
"Das Spiel startet in der Traumwelt - einem Wald mit einem alten Haus. Der Spieler kennt nur diese Realität und hat die Aufgabe, goldene Eier zu finden und einem Troll zu übergeben, um aus dieser Welt zu entkommen. Er weiß nicht, dass er träumt."

❌ **Schlecht:**
"⚠️ WICHTIG: Der Spieler weiß nicht, dass er träumt!
- Setting: Wald
- Quest: Eier finden
- Ziel: Entkommen"

### Raumbeschreibung
✅ **Gut:**
"Die Waldlichtung ist von uralten Eichen umgeben, deren knorrige Äste sich wie Finger zum düsteren Himmel strecken. Am Boden liegt dichtes Moos, feucht vom nächtlichen Tau. In der Luft hängt der Geruch von feuchtem Holz und Pilzen. Zwischen den Bäumen flackert ein schwaches, goldenes Licht."

❌ **Schlecht:**
"Waldlichtung
- Bäume: alte Eichen
- Boden: Moos
- Geruch: Holz
- Licht: golden"

### Übergänge zwischen Räumen
✅ **Gut:**
"Der Spieler kann dem goldenen Licht zwischen den Bäumen folgen, was ihn zum alten Haus führt. Allerdings versperren dichte Dornenranken den direkten Weg - er muss erst ein Werkzeug finden, um sie zu durchqueren. Alternativ kann er den schmalen Pfad nach Norden nehmen, der zum Fluss führt, wo das Rauschen des Wassers zu hören ist."

❌ **Schlecht:**
"Übergänge:
→ Altes Haus (Bedingung: Werkzeug)
→ Fluss (immer möglich)"

---

## Arbeitsweise

### Schrittweise Entwicklung:
1. User gibt neue Information
2. Information wird in passenden Abschnitt der STORY.md eingearbeitet
3. Text wird in Fließform geschrieben
4. Konsistenz wird geprüft
5. Bei Inkonsistenzen wird User informiert
6. Weiter zu nächster Information

### Bei Inkonsistenzen:
"Diese Information widerspricht [vorherige Information]. Wie soll das aufgelöst werden?"

### Bei Unklarheiten:
"Ist [Element A] gemeint als [Interpretation X] oder [Interpretation Y]?"

---

## Format-Elemente

### Erlaubt:
- **Fett** für Unterpunkte und wichtige Begriffe
- *Kursiv* für Betonungen (sparsam einsetzen)
- `Code-Format` nur für technische Begriffe (z.B. Dateinamen)
- Symbolische Pfeile für Verbindungen: ↔
- Normale Absätze und Zeilenumbrüche
- Überschriften mit # ## ###

### Nicht erlaubt:
- ⚠️ ❗ ℹ️ Emoji-Symbole für Warnungen
- TODO, FIXME, NOTE Marker
- Kommentare in <!-- -->
- Tabellen (außer bei sehr strukturierten Daten)

---

## Zielgruppe
Das Dokument richtet sich an:
- Den Game Designer (der die Story entwickelt)
- Entwickler (die später die State Engine aufbauen)
- Tester (die die Story-Konsistenz prüfen)

Das Dokument soll für alle drei Gruppen verständlich und nützlich sein.