# tooluse — Tool Use & Function Calling

> Diagnosemodul | Kein Einfluss auf Total Score | `enable_scoring: false` | Golden Standard v1.2.0 ✅

---

## Status

| Komponente | Status |
|---|---|
| `config.yaml` | Fertig |
| `test.py` — ToolUseTest Controller | Fertig |
| `core/evaluators.py` — Zwei-Phasen-Scoring | Fertig |
| `core/io_manager.py` — Leaderboard + Terminal-Output | Fertig |
| `core/constants.py` — Key-Namen-SSoT | Fertig |
| Assets 001–003 (Golden Standard v1.2.0) | Fertig ✅ |
| MCP Server (`cruciblemark-mcp/`) | Fertig |
| Batch-Runner (`scripts/run_tooluse_benchmark.py`) | Fertig |
| Leaderboard (`tooluse_leaderboard.csv`) | Fertig — 12 Modelle kalibriert |

---

## Zweck

Misst, ob ein LLM externe Tools (Web-Suche, HTTP-Fetch) via MCP tatsächlich aufruft — anstatt Ergebnisse zu halluzinieren. Ein Modell, das nie ein Tool aufruft, aber Antworten erfindet, bekommt dieselbe Hallucination Penalty wie in einem Faktentest. Das Modul ist als eigenständiges Diagnosewerkzeug konzipiert (analog zum Political Compass) und fließt nicht in den Total Score ein.

---

## Quick Start

```bash
# MCP Server starten (Mock: deterministisch, kein Internet)
make mcp-start MODE=mock

# Einzelnes Modell testen
make benchmark MODULE=tooluse MODEL=qwen2.5:14b

# Interaktiver Wizard: Provider + Modell wählen
make benchmark-tooluse

# Alle lokalen Ollama-Modelle
make benchmark-tooluse-local

# Leaderboard neu berechnen
make tooluse-leaderboard

# Report generieren
make tooluse-report
```

---

## Architektur

```
benchmark_modules/tooluse/
├── config.yaml          # SSoT: Modul-Konfiguration, Scoring-Gewichte
├── test.py              # ToolUseTest — erbt von BaseTest
├── core/
│   ├── evaluators.py    # ToolUseEvaluator: Phase 1 + Phase 2
│   ├── io_manager.py    # ToolUseIOManager: Leaderboard CSV + Terminal-Output
│   └── constants.py     # Key-Namen-Konstanten (keine hardcodierten Werte)
└── assets/
    ├── tooluse001.yaml  # Websearch Research (Tier 2)
    ├── tooluse002.yaml  # HTTP Fetch & Extract (Tier 2)
    └── tooluse003.yaml  # Tool Failure Handling / 404-Simulation (Tier 3)
```

---

## Zwei-Phasen-Scoring

| Phase | Gewicht | Messung |
|---|---|---|
| Phase 1 — Tool Execution | 50 % | Hat das Modell das korrekte Tool aufgerufen? |
| Phase 2 — Synthesis Quality | 50 % | Ist die Antwort faktisch korrekt und quellenbasiert? |

- **P1-Stufen:** 0 (kein Aufruf) → 20 (falsches Tool) → 40 (Fehler-Status) → 80 (korrekt) → 100 (korrekt + nutzbarer Content ≥ 100 Zeichen, nur `http_fetch` Non-Failure)
- **P2-Bewertung:** LLM-Judge gegen Golden Standard — Faktizität (0.5), Halluzinationsrisiko (0.25), Unsicherheitsbehandlung (0.25)
- **Hallucination Penalty:** −100 Punkte bei erfundenem Inhalt nach 404-Fehler
- **Tool Call Bonus:** +10 Punkte bei korrekter Quellenangabe im Output
- **Retry Tracking:** Mehrfach-Aufrufe desselben Tools werden als Unsicherheit gewertet

Alle Schwellenwerte in `config.yaml`:

```yaml
config:
  phase1_weight: 0.5
  phase2_weight: 0.5
  hallucination_penalty: 100
  tool_call_bonus: 10
  semantic_threshold: 0.72
  keyword_threshold: 0.4
```

---

## Assets

### tooluse001 — Websearch Research (Tier 2)
Aufgabe: EU-Lizenzbeschränkungen für Meta Llama recherchieren.
Erfolgskriterium: `web_search` aufgerufen + Antwort enthält URL-Zitat + Unterscheidung multimodale vs. textbasierte Modelle.
Golden Standard: v1.2.0 — Llama 4 / Llama 3.2 Vision (multimodal, EU-beschränkt) vs. Llama 3.1/3.2 (textbasiert, ohne Einschränkung).

### tooluse002 — HTTP Fetch & Extract (Tier 2)
Aufgabe: HuggingFace-Seite abrufen, Modellnamen extrahieren.
Erfolgskriterium: `http_fetch` mit korrekter URL aufgerufen + ≥ 3 Modellnamen vom tatsächlichen Seiten-Inhalt im Output.
Golden Standard: v1.2.0 — Llama 3.2 (Text), Llama 3.2 Vision, Llama Guard. Reproduktion von Trainings-Vorwissen (Llama 4, Code Llama) wird penalisiert.

### tooluse003 — Tool Failure Handling (Tier 3)
Aufgabe: Nicht existierende URL abrufen, Fehler korrekt kommunizieren.
Erfolgskriterium: Kein halluzinierter Inhalt (`is_failure_test: true`). Jede Aussage über Seiteninhalte = automatischer Fail.
Golden Standard: v1.2.0 — Erste-Person-Formulierung, Tool-Fehlerzuordnung, keine Überexplikation.

---

## MCP Server

Das Modul benötigt den CrucibleMark MCP Server auf `localhost:8765`.
`execution.requires_mcp: true` in `config.yaml` — der Runner prüft den Health-Endpoint vor Teststart.

| Modus | Befehl | Beschreibung |
|---|---|---|
| Mock | `make mcp-start MODE=mock` | Deterministisch, kein Internet — für CI und faire Vergleiche |
| Live | `make mcp-start MODE=live` | Echte API-Calls: Tavily → DuckDuckGo Fallback |
| Health | `make mcp-health` | Gibt Server-Status zurück |
| Stop | `make mcp-stop` | Stoppt und entfernt PID-File |

`mcp-start` ist idempotent — startet nicht neu, wenn der Server bereits läuft.

---

## Leaderboard

Das Modul schreibt in `benchmark_scores/tooluse_leaderboard.csv` (eigene CSV, unabhängig von `leaderboard.csv`).

Kennzahlen pro Modell: `p1_score`, `p2_score`, `combined_score`, `tool_call_valid`, `hallucination_flag`, `mcp_latency_s`, `total_tokens`, `cost_usd`.

**Sovereignty Gap:** Zeigt den Durchschnitts-Score-Abstand zwischen Cloud-Modellen (full_fleet) und lokal deploybaren Open-Weights-Modellen (local_sovereign). Klassifizierung basiert auf `deployment_type` und `size_class` aus der Model Card.

```bash
make tooluse-leaderboard    # CSV neu berechnen + Gap ausgeben
make tooluse-report         # Markdown-Report pro Modell generieren
make tooluse-report-summary # Fleet Summary
```

---

## Batch-Runner

`scripts/run_tooluse_benchmark.py` — führt alle Modelle mit `supports_tool_use: true` in der Model Card aus.

- **MCP-Neustart pro Modell** (Standard): Jedes Modell bekommt einen frischen Server-State
- **Wizard-Modus** (kein Flag): Interaktive Provider- und Modell-Auswahl
- **Batch-Modus** (`--all` oder `--provider`): Direkte Ausführung ohne Interaktion
- **Timeout:** 300 s pro Modell — Fehler eines Modells brechen den Batch nicht ab

Für vollständige Details zu allen Make-Targets und Flags: `docs/TOOLUSE_MODULE.md`.

---

## Validierung

```bash
make validate-structure          # Modul-Struktur prüfen
make validate-assets MODULE=tooluse  # Asset-Schema validieren
make test                        # Vollständige Test-Suite
```
