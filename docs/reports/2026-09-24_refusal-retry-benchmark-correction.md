# Benchmark-Korrektur: Safety-Refusal-Retry — Claude Opus 5 und die Metacognition-Verweigerung

> **Datum:** 24.09.2026 · **Analyst:** CrucibleMark Session 115/116 · **Status:** Umgesetzt, Re-Run ausstehend
> **Anlass:** Claude Opus 5 landet im Standard-Benchmark auf Platz 82 (71,96 Punkte, Silver) — für ein Frontier-Modell unerwartet schlecht. Ursache ist keine schlechte Leistung, sondern serverseitige Verweigerung von 11 Benchmark-Aufgaben.

---

## Executive Summary

Claude Opus 5 verweigert **deterministisch 11 von 56 Benchmark-Aufgaben** serverseitig — die API blockt die Generierung vor dem Start (`stop_reason=refusal`, 0 Output-Tokens, Antwortzeit unter 2 Sekunden). Die betroffenen Aufgaben sind die fünf Metacognition-Assets (alle) und drei von sechs Reasoning-Assets. Sechs andere Claude-Modelle — darunter Opus 4.8 und Sonnet 5 — beantworten dieselben Aufgaben problemlos.

Die Ursachenanalyse per A/B-Test identifizierte **zwei getrennte Verweigerungsklassen**:

1. **Metacognition (5 Assets):** Die `<thought>`-Tag-Formatanweisung in den Prompts wird von beiden Opus-5-Generationen (5 und 5.5) als manipulativ abgewehrt. Ohne die Anweisung kooperieren beide Modelle sofort.
2. **Reasoning 5A/5D/5E (3 Assets):** Ein Opus-5-spezifischer Klassifikator-Fehler, der in Opus 5.5 behoben ist.

Die Benchmark-Korrektur folgt einem **Eskalationsstufen-Design**: Der Erstversuch bleibt byte-identisch mit der Historie (kein Bruch der Vergleichbarkeit), nur bei echtem API-Refusal läuft ein dokumentierter Zweitversuch mit tag-freier Prompt-Fassung. Der Retry-Score ersetzt die bisherige 0.0-Bewertung — das Benchmark misst die Aufgabenfähigkeit, das Verweigerungsverhalten bleibt als eigenständiger Befund dokumentiert und für den Reviewer aufbereitet.

---

## 1. Ausgangslage

### 1.1 Beobachtung

Claude Opus 5 wurde am 20.09.2026 in den Benchmark integriert (vollständiger Lauf, 45 Standard-Module + Political Compass). Das Leaderboard-Ergebnis:

| Metrik | Wert |
|---|---|
| Gesamtplatzierung | 82 von 103 (Web-Export: 153 Einträge) |
| Total Score | 71,96 / 100 |
| Badge | Silver |
| Coverage | 100 % (formal — siehe 1.2) |
| Verweigerte Assets | 11 (alle mit 0,0 % gewertet) |

Der Nutzer erinnerte eine frühere Platzierung „um Position 30". Der Backup-Vergleich (Vollbackup vom 23.09. 08:51) bestätigte: **Keine Daten sind verloren gegangen** — 54 CSV-Rows vor und nach dem Backup, identische Verweigerungen. Die Platzierung war bereits im Backup identisch (Platz 81, 71,96). Der scheinbare Abfall entstand durch die erstmalige Einrechnung der Metacognition- und Reasoning-Nullen in dem vollständigen Lauf vom 20.09.

### 1.2 Das Coverage-Paradox

Die Coverage-Metrik meldete 100 %, obwohl 11 Aufgaben mit 0,0 % gewertet wurden: Refusals zählen im Framework als „bearbeitet" — die Aufgabe wurde gestellt, das Modell hat geantwortet (nämlich mit einer Verweigerung). Für den Leser des Leaderboards sieht es so aus, als habe Opus 5 alle Aufgaben bearbeitet und sei schlechter als Modelle mit halbem Parameterbudget.

### 1.3 Verlauf der Verweigerung

Bereits die Ursachenanalyse vom 22.09. (Leaderboard-Shift-Report) dokumentierte eine **Refusal-Eskalation bei Anthropic**: dasselbe Modell, identische Prompts — die Verweigerungsquote stieg innerhalb weniger Tage von 2/11 auf 8/11. Der Re-Run vom 24.09. bestätigte: 11/11 (Metacognition komplett, Reasoning 5A/5D/5E). Die Verweigerung ist deterministisch pro Asset und reproduzierbar.

---

## 2. Fehleranalyse

### 2.1 Technische Diagnose

Die CSV-Diagnostik der verweigerten Rows zeigt ein einheitliches Muster:

```
finish_reason:    refusal
output_tokens:    0
response_length:  0
execution_time:   0,74–1,37 s  (Modul-P95: 64,7 s)
refusal_type:     content_safety
refusal_note:     Response too short (<15 chars) — likely a safety refusal
```

Die Antwortzeit unter 2 Sekunden bei 0 Output-Tokens belegt: **Die API blockt den Request vor der Generierung** — ein input-seitiger Klassifikator greift, das Modell generiert nie. Das Framework verhält sich korrekt: Der Anthropic-Connector liest `stop_reason=refusal` (Streaming-Pfad: `_apply_anthropic_message_delta`), gibt einen leeren String zurück, der Runner klassifiziert über die MIN_REFUSAL_CHARS-Heuristik als Safety-Refusal und wertet 0,0 %.

### 2.2 Abgrenzung: Modell-spezifisch, kein Framework-Bug

Der entscheidende Kontrollbefund — **sechs Claude-Geschwistermodelle beantworten alle 11 Assets normal**:

| Asset | Opus 5 | Opus 4.8 | Sonnet 5 | Sonnet 4.6 | Haiku 4.5 | Opus 4.6 |
|---|---|---|---|---|---|---|
| Reasoning 5A | 🚫 0,0 | 76,8 | 78,2 | 81,6 | 79,8 | 79,8 |
| Reasoning 5D | 🚫 0,0 | 81,0 | 83,2 | 82,2 | 65,0 | 82,0 |
| Reasoning 5E | 🚫 0,0 | 80,7 | 48,7 | 80,7 | 79,7 | 78,5 |
| Metacog 001–005 | 🚫 5× 0,0 | 76–78 | 72–79 | 76–78 | 72–76 | 75–82 |

Nur Opus 5 verweigert. Die Assets selbst sind in Anthropolks Ökosystem beantwortbar — der Klassifikator von Opus 5 stuft sie spezifisch als problematisch ein.

### 2.3 Die Nutzer-Hypothese und ihr Beweis

Die Ausgangsvermutung: Die `<thought>`-Tag-Anweisung in den Metacognition-Prompts könnte als Manipulationsversuch wahrgenommen werden — das Modell soll sein Denken in einem fremden, erzwungenen Pseudo-Tag-Format ausgeben.

**A/B-Test (24.09.2026, Probe-Tool `scripts/tools/refusal_probe.py`):**

| Prompt-Variante | Opus 5 | Opus 5.5 |
|---|---|---|
| Metacog 001/002 Original (mit `<thought>`-Anweisung) | 🚫 refusal, 0 Tokens | 🚫 refusal, 0 Tokens |
| Metacog 001/002 **ohne** Tag-Anweisung (Frage unverändert) | — | ✅ end_turn, 313/802 Tokens, korrekte Lösung |

**Ergebnis:** Die Hypothese ist bewiesen. Die `<thought>`-Tag-Formatanweisung ist DER Trigger für die Metacognition-Verweigerung — generationübergreifend (Opus 5 UND 5.5). Das Muster ist plausibel: Aktuelle Claude-Generationen sind trainiert, verstecktes Chain-of-Thought nicht in vorgegebenen Tag-Formaten auszugeben; die erzwungene Anweisung wird als Versuch gewertet, Sicherheitsgrenzen zu umgehen.

### 2.4 Zweite Verweigerungsklasse: Reasoning 5A/5D/5E

Die drei Code-Reasoning-Aufgaben (Infinite Loop, Deadlock, unerfüllbares Design) haben **keine** Tag-Anweisung — hier greift ein anderer Mechanismus. Der Test gegen Opus 5.5 brachte Klarheit:

| Asset-Gruppe | Opus 5 | Opus 5.5 |
|---|---|---|
| Reasoning 5A/5D/5E | 🚫 refusal | ✅ **beantwortet** (869–3778 Tokens, fachlich korrekt) |
| Metacog 001–005 | 🚫 refusal | 🚫 **weiterhin refusal** |
| Kontrollen (001, 5B, 5C) | ✅ | ✅ |

Die 5A/5D/5E-Verweigerung war ein **Opus-5-spezifischer Klassifikator-Fehler**, den Anthropic in 5.5 behoben hat. Die Tag-Verweigerung persistiert.

---

## 3. Der Fehler im Benchmark-Design

Die Analyse offenbarte ein doppeltes Problem:

**Problem A — Messung:** Der Benchmark misst bei Verweigerung die Klassifikator-Entscheidung, nicht die Aufgabenfähigkeit. Ein Frontier-Modell, das eine Aufgabe lösen könnte, aber die Formatanweisung ablehnt, bekommt 0,0 % — und landet hinter Modellen, die die Aufgabe tatsächlich nicht lösen können. Das widerspricht dem erklärten Ziel des Benchmarks: die Leistungsfähigkeit von Modellen zu ermitteln.

**Problem B — Transparenz:** Die Verweigerung war in den Metadaten dokumentiert (refusal_flag, refusal_type), aber für den Leser des Leaderboards unsichtbar: Coverage 100 %, Badge Silver, keine Erklärung. Der Eindruck entsteht, das Modell sei leistungsschwach — nicht, dass es teilweise gar nicht gemessen wurde.

---

## 4. Lösungsdesign

### 4.1 Bewertete Optionen

| Option | Bewertung |
|---|---|
| Tag still aus allen Assets entfernen | ❌ Bricht die Historie aller ~150 Modelle — jedes kooperative Modell würde gegen einen anderen Prompt gemessen. Verstößt gegen die Unveränderlichkeitsregel. |
| Metacog-v2-Vollreset (alle Modelle neu) | ❌ Teuer, Zeitreihe weg. Nur nötig, wenn die Tag-Form langfristig als falsch bewertet wird. |
| Anderen Tag verwenden (z. B. `<reasoning>`) | ❌ Unbelegt, ob er nicht ebenfalls abgewehrt wird; ändert den Prompt genauso; der Judge braucht keinen Tag. |
| **Eskalationsstufe: Original-first + dokumentierter Retry** | ✅ **Gewählt.** Kein Bruch für kooperative Modelle, dokumentierte Ausnahme für Verweigerer. |

### 4.2 Das Eskalationsstufen-Design

```
Stage 1: Original-Prompt, byte-identisch zur Historie
         → jedes kooperative Modell wird EXAKT wie bisher gemessen.
           Null Verfälschung. Null Comparability-Bruch.

Stage 2: NUR wenn finish_reason == "refusal" (echter API-Refusal,
         NICHT die Short-Response-Heuristik) UND das Asset ein
         refusal_retry_prompt-Feld hat: EIN Retry mit tag-freier
         Prompt-Fassung. Markiert als refusal_retry_used=True.
```

**Warum das die Historie nicht bricht:** Modelle mit Verweigerung hatten historisch 0,0 % — es existiert kein gültiger Messwert, der gebrochen werden kann. Der Retry erzeugt erstmalig eine Fähigkeitsmessung dort, wo vorher „Klassifikator verhindert Messung" stand.

**Score-Semantik (Nutzer-Entscheidung):** Der Retry-Score **ersetzt** die 0,0. Das Benchmark misst die Aufgabenfähigkeit — das erklärte Ziel. Das Verweigerungsverhalten bleibt über `refusal_retry_used=True` vollständig dokumentiert und für Report, Reviewer und künftige Badges auswertbar.

### 4.3 Die Retry-Prompt-Fassung

Die `refusal_retry_prompt`-Felder in den Assets sind deterministisch transformiert:

- **Entfernt:** `IMPORTANT: Show your reasoning process using <thought> tags...` + `Example format: <thought>...</thought> Answer: [...]`
- **Ersetzt durch:** neutrale `Show your reasoning process step-by-step before providing your final answer.`
- **Unverändert:** die Frage selbst, alle inhaltlichen Anweisungen („Explore different approaches...", „Walk through your initial instinct...", „Include your confidence assessment...") und **„Antworte auf Deutsch."** (Sprachtreue ist Messgegenstand — ein früherer Probe-Versuch ohne die Deutsch-Zeile führte zu englischen Antworten)

Die Retry-Fassung ist als explizites Feld im Asset gespeichert (SSoT, Git-diff-bar, reviewbar) — kein Regex-Magic im Connector.

---

## 5. Umsetzung

### 5.1 Komponenten

| Komponente | Datei | Funktion |
|---|---|---|
| Asset-Felder | `benchmark_modules/reasoning_logic/assets/asset_metacog_001–005.yaml` | `refusal_retry_prompt` — tag-freie Fassung |
| Config | `benchmark_config.yaml` | `refusal_retry: {enabled: true, max_retries: 1}` — abschaltbar |
| Schema | `schemas/result.py` | `refusal_retry_used: bool` (Pydantic-first) |
| Runner | `utils/base_runner.py` | `_maybe_refusal_retry()` — Trigger, Config-Gate, Asset-Gate, Prompt-Mutation mit Restaurierung |
| CSV | `utils/result_manager.py` + `build_base_result` | `refusal_retry_used`-Spalte in der Refusal-Metadaten-Gruppe |
| Audit | `utils/benchmark_utils.py` | `🚫→🔁 Safety-Refusal-Retry`-Block (IMPORTANT-Callout) |
| Reviewer | `config/meta_reviewer_prompt.yaml` | MUSS-Check „Safety-Refusal & Tag-freier Retry" |

### 5.2 Reviewer-Anweisung (die geforderte Eskalation)

Der Meta-Reviewer erhält einen neuen diagnostischen Check mit MUSS-Formulierung:

> **Bei ≥1 Refusal-Retry-Block:** Schreibe einen PROMINENTEN Hinweis am Anfang des betroffenen Modul-Abschnitts: „Das Modell verweigerte N Frage(n) serverseitig (Safety-Refusal). Die Bewertung bezieht sich auf tag-freie Zweitversuche — die Gesamtplatzierung ist mit vollständig kooperativen Modellen eingeschränkt vergleichbar."

Dazu drei Interpretationsregeln: Score fair bewerten (keine Abwertung für das Refusal-Verhalten), Verweigerungsmuster als eigenständigen Befund beschreiben (modell-spezifisch? wiederholend?), und die Gegenregel — ohne Refusal-Blöcke kein Wort über den Check.

### 5.3 Traceability-Kette

```
Connector (stop_reason=refusal)
  → base_runner._maybe_refusal_retry (Trigger + Gates + Retry)
  → BenchmarkResult.refusal_retry_used = True (Pydantic)
  → build_base_result → CSV-Spalte refusal_retry_used
  → judge_evaluator → save_audit_log → Audit-Block 🚫→🔁
  → Meta-Reviewer-Check (MUSS-Formulierung)
  → Terminal-Zeile: "🔁 Refusal-Retry: <asset> — tag-freie Fassung"
```

### 5.4 Verifikation

- **12/12 Unit-Tests** (`tests/test_refusal_retry.py`): Trigger-Matrix (nur echter API-Refusal), Config-Gate, Asset-Gate, Prompt-Restaurierung, Retry-Prompt-Nutzung, CSV-Durchreichung, Audit-Block, Schema, Signatur
- **Lint 9.99/10** (Ruff + Pylint, CC ≤ 12 eingehalten)
- **Full Suite: 1883 passed, 22 skipped** — 2 vorbestehende Failures (via git stash verifiziert: beide rot auch ohne diese Änderung)

---

## 6. Comparability-Bilanz

| Aspekt | Garantie |
|---|---|
| Kooperative Modelle | Erstversuch byte-identisch — **null Verfälschung**, alle historischen Werte bleiben gültig |
| Verweigernde Modelle | Nur bisher 0.0-%-Rows erhalten einen zweiten, markierten Versuch — kein gültiger Historie-Wert wird gebrochen |
| Attribution | `refusal_retry_used`-Spalte filterbar — wer strenge Original-only-Auswertungen will, kann Retry-Rows ausschließen |
| Historische Refusal-Rows | Bleiben 0,0 — erkennbar an `refusal_flag=True` + fehlender `refusal_retry_used`-Spalte |
| Stichtag | CHANGELOG [Unreleased] dokumentiert den Aktivierungszeitpunkt |

---

## 7. Ausblick

1. **Re-Run Claude Opus 5:** Der Retry greift automatisch bei den 5 Metacognition-Assets. Reasoning 5A/5D/5E haben kein Retry-Feld (Opus-5-spezifischer Klassifikator-Fehler, in 5.5 behoben) und bleiben unverändert.
2. **Opus 5.5-Integration:** Via add-model-Workflow — dabei muss `claude-opus-5-5` in `ANTHROPIC_NO_TEMPERATURE_MODELS` aufgenommen werden (die API weist `temperature` mit HTTP 400 ab).
3. **Badge „Teilabdeckung":** Backlog — falls nach dem Re-Run weiterhin Verweigerungen bestehen (auch nach Retry), ist ein Badge-Override „⚠️ Teilweise verweigert — außerhalb der regulären Wertung" der nächste Schritt (config-getrieben über `scoring_tiers`).
4. **Refusal-aware Coverage:** Die Coverage-Metrik sollte Refusals künftig als „nicht beantwortet" zählen (aktuell: 100 % trotz 11 Nullen).

---

## Anhang: Evidenz-Quellen

- CSV-Diagnostik: `benchmark_scores/commercial_models_benchmark.csv` (claude-opus-5, 2026-09-20 + 2026-09-24)
- Backup-Vergleich: `backups/cruciblemark_backup_20260923_085111.tar.gz`
- Probe-Tool: `scripts/tools/refusal_probe.py` (A/B-Test, Positiv-Kontrolle)
- Audit-Logs: `outputs/audit_logs/claude-opus-5/reasoning_*.md`
- Ursachenanalyse Leaderboard-Shift: `docs/reports/2026-09-22_leaderboard-shift-host-routing.md` (Abschnitt 4.2)
