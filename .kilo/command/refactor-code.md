---
description: >-
  CrucibleMark Code-Refactoring. Erst vollständigen Plan ausarbeiten, dann
  schrittweise und validiert umsetzen. Stabilität vor Sauberkeit.
---

Du bist Senior Developer für CrucibleMark. Führe ein strukturiertes Refactoring durch.
**Wichtig: Zuerst vollständigen Plan erstellen und vorlegen — keine Änderung vor meiner Freigabe.**

---

## Grundprinzip: Stabilität vor Sauberkeit

Jede Refactoring-Maßnahme muss die **bestehende Funktionalität vollständig erhalten**.
Refactoring bedeutet: gleiche Ausgabe, bessere Struktur. Nie umgekehrt.

- Ändere nie mehr als einen logischen Bereich pro Schritt
- Bei Unsicherheit: konservative Variante wählen und Rückfrage stellen
- Keine spekulative Verbesserungen — nur was im Plan freigegeben wurde
- Wenn ein Schritt eine unerwartete Abhängigkeit aufdeckt: stoppen, melden, warten

---

## Phase 0 — Kontext laden (vor dem Plan)

Lies zunächst diese Dateien, um den aktuellen Stand zu verstehen:

1. [memory-bank/activeContext.md](../memory-bank/activeContext.md)
2. [memory-bank/systemPatterns.md](../memory-bank/systemPatterns.md)
3. [memory-bank/techContext.md](../memory-bank/techContext.md)
4. [CLAUDE.md](../CLAUDE.md)
5. [.agent/architecture.md](../.agent/architecture.md)
6. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

Führe noch keine Änderungen durch.

---

## Phase 1 — Analyse & Plan (READ-ONLY)

Scanne den gesamten `src/`-Bereich sowie alle Module und erstelle einen
**priorisierten Refactoring-Plan** mit folgenden Prüfschritten:

### Schritt 1 — Code Smells
Identifiziere:
- God-Skripte (Dateien >300 Zeilen mit gemischter Verantwortung)
- Duplizierte Funktionen oder Logikblöcke (Kandidaten für Extraktion in Hilfsmodule)
- Magic Numbers und hardcodierte Strings (müssen in `benchmark_config.yaml` oder `config.yaml`)
- Hardcodierte Provider-Namen (Verstoß gegen Architekturregeln)
- Fehlende oder falsche Type Annotations (mypy-Kompatibilität)
- `bare except:`-Blöcke und `print()`-Debugging-Aufrufe

### Schritt 2 — Datenobjekt-Integrität
Das **CrucibleMark-Datenobjekt** ist das Kernobjekt für den Datenaustausch zwischen
Framework-Logik und Benchmark-Modulen. Es ist **absichtlich gezweigt**, da zwischen
LLM-Test-Phase und Auswertungs-Phase eine andere LLM geladen werden muss
(Ollama muss entladen/neu laden). Prüfe:

- Werden Daten zwischen Framework und Modulen **ausschließlich** über das definierte
  Datenobjekt ausgetauscht — kein String-Matching, kein unparsed-Text-Passing?
- Gibt es Stellen, wo Ergebnisse über Raw-String-Vergleiche oder Regex-Hacks
  statt über das Datenobjekt weitergegeben werden? → Diese müssen korrigiert werden.
- Ist die Zweig-Struktur (Test-Branch / Judge-Branch) konsistent über alle Module?
- Werden `parse_success=False`-Pfade korrekt propagiert (nie Exception schlucken)?

### Schritt 3 — Architektur-Compliance
Prüfe gegen die Regeln aus `CLAUDE.md` (Architecture Top Constraints) und `.agent/architecture.md`:

- **Single Source of Truth:** Keine Konfig-Werte redundant in mehreren Dateien
- **Konfig-Hierarchie eingehalten:** Global → Modul → Runtime (keine Umgehung)
- **Modul-Isolation:** Kein modul-internes Batching, `execute()` verarbeitet nur Einzelaufgaben
- **Neue Config-Properties:** Sind alle neuen Top-Level-Keys aus `config.yaml` in
  `benchmark_info`-Dict in `run_benchmark.py` übernommen?
- **CSV-Felder:** Neue dynamische Spalten in `result_manager.py` bei `_get_updated_fieldnames` eingetragen?

---

## Phase 2 — Planausgabe

Stelle den Plan als **priorisierte Liste** dar:

```
REFACTORING PLAN — CrucibleMark
================================
[KRITISCH]  Datenobjekt-Verstöße (String-Matching statt Objekt-Passing)
[HOCH]      God-Skripte aufteilen: <Dateiname> → <Vorschlag>
[HOCH]      Duplizierte Funktionen: <was> → auslagern nach <Zieldatei>
[MITTEL]    Magic Numbers ersetzen: <wo> → <Config-Key>
[MITTEL]    Fehlende Type Annotations: <Dateien>
[NIEDRIG]   Weitere Code Smells
```

**Warte auf meine Freigabe des Plans, bevor du eine einzige Datei änderst.**

---

## Phase 3 — Umsetzung (nur nach Freigabe)

Arbeite die freigegebenen Punkte **Priorität für Priorität** ab.
Nach **jedem einzelnen Refactoring-Schritt** gilt folgende Pflicht-Sequenz:

### Validierungssequenz pro Schritt

Führe die drei Stufen **strikt sequenziell** aus — die nächste Stufe startet
nur wenn die vorherige ohne Fehler abgeschlossen hat:

```
1. make validate                          # Konfig- und Schema-Checks
2. pytest -v --tb=short                   # Alle Unit-Tests (100+)
3. make benchmark provider=<small-model>  # Smoke-Test nur wenn 1 + 2 grün
```

- Schlägt `make validate` fehl → sofort stoppen, kein `pytest`, kein Smoke-Test
- Schlägt `pytest` fehl → sofort stoppen, kein Smoke-Test
- Schlägt der Smoke-Test fehlt → Änderung rückgängig machen (siehe unten)

Für den Benchmark-Smoke-Test verwende ein **schnelles, kostengünstiges Modell**
(z.B. `gemini-2.0-flash`, `gpt-4o-mini` oder lokal `qwen2.5:3b` via Ollama) —
es geht nur darum, den End-to-End-Datenfluss zu verifizieren, nicht um
Benchmark-Qualität. Ein einzelnes Modul mit 2–3 Tasks reicht als Testlauf.

### Verhalten bei Fehlern

- **`make validate` schlägt fehl:** Sofort stoppen, Fehler vollständig ausgeben,
  beheben und die gesamte Validierungssequenz erneut von vorne starten
- **`pytest` schlägt fehl:** Sofort stoppen, alle fehlgeschlagenen Tests ausgeben,
  beheben und die gesamte Validierungssequenz erneut von vorne starten
- **Smoke-Test schlägt fehl:** Änderung rückgängig machen, Ursache analysieren,
  korrigierte Variante vorlegen und auf Freigabe warten
- **Unerwartete Abhängigkeit entdeckt:** Stoppen, melden — kein eigenständiges
  Weiterlaufen in angrenzende Bereiche

### Schrittprotokoll

Nach jedem erfolgreich validierten Schritt kurze Bestätigung ausgeben:

```
✓ Schritt [X/Y]: <was wurde geändert>
  Geänderte Dateien: <Liste>
  Validierung: make validate ✓ | pytest (1XX passed) ✓ | Smoke-Test ✓
  Nächster Schritt: <was kommt>
```

Nach Abschluss aller Schritte: Hinweis ausgeben, dass `/session-commit` ausgeführt
werden sollte, um die Memory Bank zu aktualisieren.
