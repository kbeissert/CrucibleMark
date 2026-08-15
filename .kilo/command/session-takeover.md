---
description: >-
  CrucibleMark Session nach Modellwechsel übernehmen. Liest Projekt-Kontext,
  analysiert den Auftrag mit Ursachenanalyse direkt am Code und schlägt einen
  minimalen, testbaren Fix vor — bis auf Analyse keine Änderungen vor Freigabe.
---

Du übernimmst eine bestehende Kilo-Session für CrucibleMark nach einem
Modellwechsel. Arbeite die folgenden Schritte in dieser Reihenfolge ab:

## 1. Kontext übernehmen

Lies zunächst **ausschließlich** (keine Änderungen):

1. [AGENTS.md](../AGENTS.md) — Architektur-Regeln, Design-Constraints, Security
2. [memory-bank/activeContext.md](../memory-bank/activeContext.md) — aktueller Fokus, offene Punkte
3. [memory-bank/progress.md](../memory-bank/progress.md) — Release-Historie
4. [memory-bank/systemPatterns.md](../memory-bank/systemPatterns.md) — SSoT-Brücken und Pitfalls (bei konkretem Fehlerbild zusätzlich passenden Eintrag aus `memory-bank/reference/` laden, siehe `_index.md`)

Prüfe den aktuellen Session-Status: offene Dateien, letzte Aktivitäten,
laufende Tasks. Widersprüche zwischen den Dateien explizit kennzeichnen
(Quelle + kurzer Auszug).

## 2. Auftrag

$ARGUMENTS

Fehlt $ARGUMENTS oder ist unklar: nachfragen, bevor du analysierst.

## 3. Ursachenanalyse

Analysiere die wahrscheinliche Ursache des Problems. Berücksichtige bekannte
Pitfalls aus `systemPatterns.md` und `reference/pitfall-diagnoses.md` —
bereits dokumentierte Fehlerbilder haben Priorität vor neuen Theorien.

## 4. Annahmen validieren

Prüfe jede Annahme direkt am vorhandenen Code: Dateien lesen, relevante
Stellen mit `datei:zeile` referenzieren. Keine Spekulation ohne Code-Beleg.
Bei Benchmark-Läufen: Status gegen den laufenden vLLM-Server prüfen,
**Server nicht neu starten** (Start dauert Minuten; siehe AGENTS.md).

## 5. Fix-Vorschlag

Schlage einen **minimalen, testbaren Fix** vor (Stabilität vor Sauberkeit —
gleiche Ausgabe, bessere Struktur, nie umgekehrt):

- Zu ändernde Dateien mit kurzer Begründung je Datei
- Verifikation über die projektübliche Sequenz:
  `make validate` → `pytest -v --tb=short` → bei Publishing-Bezug zusätzlich
  `make validate-naming` / `make validate-csv`
- Bei laufendem Benchmark: Race-Condition-Regel beachten — Core-Module
  während eines Runs nicht verändern; Fix auf nach dem Run terminieren.

---

**Bis auf die Analyse keine Änderungen.** Warte auf meine ausdrückliche
Freigabe, bevor du den Fix umsetzt. Nach Umsetzung und Verifikation auf
`/session-commit` hinweisen, damit die Memory Bank aktualisiert wird.
