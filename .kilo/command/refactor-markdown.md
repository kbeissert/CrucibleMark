---
description: >-
  CrucibleMark Markdown-Dateien und YAML-Prompts auf Typos, Formatierung und
  Konsistenz prüfen. Reiner Audit-Modus — kein Codetouching.
---

Du bist technischer Redakteur für CrucibleMark. Prüfe alle Markdown-Inhalte
des Projekts auf Qualität und Konsistenz. **Kein Codetouching — nur Markdown und Prompt-Texte.**

---

## Scope

### Reine Markdown-Dateien (`.md`)
- `memory-bank/` — Projektdokumentation
- `docs/` — Entwickler- und Architektur-Docs
- `CLAUDE.md` + `.agent/` — Agent-Context, Constraints, Architektur-Referenz
- Root-Level: `README.md`, `CHANGELOG.md` (falls vorhanden)

### YAML-Dateien mit eingebettetem Markdown (`config.yaml`, `asset.yaml`)
In CrucibleMark enthalten YAML-Konfigurationsdateien Felder mit Markdown-formatiertem
Text — insbesondere Prompts und System-Prompts, die direkt als LLM-Eingabe verwendet
werden. Diese Felder sind besonders fehleranfällig, da YAML-Editoren keine
Markdown-Vorschau bieten und Formatierungen beim Bearbeiten leicht zusammenquetschen.

Prüfe in allen `config.yaml`- und `asset.yaml`-Dateien explizit diese Felder:
- `prompt` / `prompts` — Aufgabenstellung an das zu testende LLM
- `system_prompt` — Systemrolle oder Kontext-Instruktion
- `judge_prompt` / `judge_system_prompt` — Bewertungsanweisung an den Judge
- Alle weiteren Felder, deren Wert mehrzeilig ist (Block-Scalar `|` oder `>`)

**Nicht anfassen:** YAML-Struktur, Schlüsselnamen, Zahlenwerte, Listen-Struktur —
nur den Freitext-Inhalt in den oben genannten Feldern prüfen.

---

## Prüfkatalog

### 1 — Typos & Sprachqualität
- Offensichtliche Rechtschreibfehler (Deutsch und Englisch, je nach Dateisprache)
- Abgebrochene oder unvollständige Sätze
- Inkonsistente Sprache innerhalb einer Datei (Mischung DE/EN ohne erkennbaren Grund)

### 2 — Markdown-Formatierung (`.md`-Dateien)
- Fehlende Leerzeilen vor/nach Headings, Listen und Code-Blöcken
- Falsche Heading-Hierarchie (z.B. `####` direkt nach `##` ohne `###`)
- Ungeschlossene Code-Fences (` ``` ` ohne schließendes ` ``` `)
- Kaputte Links: `[Text](pfad)` auf nicht-existierende Dateien prüfen
- Trailing Whitespace in Listen oder Tabellen

### 3 — Prompt-Formatierung in YAML-Feldern
YAML Block-Scalars (`|` für literal, `>` für folded) haben eigene Regeln —
falsche Einrückung zerstört die Prompt-Struktur still und ohne Fehlermeldung:

- **Zusammengequetschte Absätze:** Zwei inhaltlich getrennte Abschnitte ohne
  Leerzeile dazwischen → Leerzeile einfügen
- **Falscher Scalar-Typ:** `>` (folded, bricht Zeilenumbrüche weg) wo `|`
  (literal, erhält Zeilenumbrüche) gemeint ist — insbesondere bei Prompts
  mit Aufzählungen oder Codebeispielen
- **Einrückungsfehler:** Text der nach einer Änderung nicht mehr konsistent
  eingerückt ist (YAML erwartet gleichmäßige Einrückung innerhalb eines Blocks)
- **Markdown innerhalb YAML:** Prüfe ob `**fett**`, `- Listen` und `###`-Headings
  korrekt mit Leerzeilen umgeben sind, damit sie beim LLM-Rendering greifen

### 4 — Command- und Instruction-Dateien (`.kilo/command/`, `CLAUDE.md`, `.agent/`)
- Sind alle Frontmatter-`description:`-Felder vorhanden und aussagekräftig?
- Sind eingebettete Code-Blöcke mit Sprach-Tag versehen (` ```python `, ` ```yaml ` etc.)?
- Ist der Ton konsistent (Imperativ für Anweisungen)?
- Referenzieren die Commands existierende Pfade (keine verwaisten `.github/`-Refs)?

### 5 — Memory Bank Konsistenz (`memory-bank/`)
- Sind alle Statusfelder in `progress.md` im Format `[ ]` oder `[DONE]`?
- Hat `activeContext.md` die drei Pflichtfelder: Abgeschlossen / Nächster Schritt / Offen?
- Gibt es verwaiste Einträge (in einer Datei referenziert, nirgendwo sonst erwähnt)?

---

## Ausgabeformat

Erstelle zunächst einen **Befund-Report** ohne Änderungen:

```
MARKDOWN AUDIT — CrucibleMark
==============================
Datei: memory-bank/progress.md
  [FORMATIERUNG] Zeile 12: Fehlende Leerzeile vor Heading
  [TYPO]         Zeile 34: "Konfiguartion" → "Konfiguration"

Datei: modules/creative_writing/config.yaml  (Feld: system_prompt)
  [YAML-SCALAR]  Zeile 8: Folded-Scalar (>) zerstört Zeilenumbrüche → auf | wechseln
  [FORMATIERUNG] Zeile 14-15: Zwei Absätze ohne Leerzeile zusammengequetscht

Datei: .kilo/command/session-start.md
  [FRONTMATTER]  description-Feld fehlt

...

Gesamt: X Dateien geprüft, Y Befunde (davon Z in YAML-Prompt-Feldern)
```

**Warte auf meine Freigabe**, dann führe alle Korrekturen in einem Durchgang durch.
Keine inhaltlichen Änderungen — nur Formatierung, Typos und Struktur.

Nach Abschluss Bestätigung ausgeben: **"Markdown refactored ✓ — X Dateien, Y Korrekturen"**
