# ToolUse-Modul: Technische Referenz

> **Modul-Typ:** Diagnosemodul — kein Einfluss auf den Total Score  
> **Voraussetzung:** CrucibleMark MCP Server läuft auf `localhost:8765`  
> **Verfügbare Assets:** 3 (tooluse001–003)  
> **Getestete Modelle (Fleet):** Alle Modelle mit `supports_tool_use: true` in der Model Card

---

## Inhalt

1. [Überblick](#1-überblick)
2. [Architektur & Komponenten](#2-architektur--komponenten)
3. [Execution-Flow im Detail](#3-execution-flow-im-detail)
4. [MCP Server](#4-mcp-server)
5. [Zwei-Phasen-Scoring](#5-zwei-phasen-scoring)
6. [Test-Assets](#6-test-assets)
7. [Konfiguration](#7-konfiguration)
8. [Terminal-Ausgabe](#8-terminal-ausgabe)
9. [Leaderboard & Sovereignty Gap](#9-leaderboard--sovereignty-gap)
10. [Report-Generierung](#10-report-generierung)
11. [Batch Runner & Wizard](#11-batch-runner--wizard)
12. [Make-Befehlsreferenz](#12-make-befehlsreferenz)
13. [Test-Suite](#13-test-suite)
14. [Neue Assets hinzufügen](#14-neue-assets-hinzufügen)

---

## 1. Überblick

Das ToolUse-Modul prüft, ob ein LLM externe Tools (Web-Suche, HTTP-Fetch) via MCP tatsächlich aufruft — statt Ergebnisse zu halluzinieren. Es misst zwei Dimensionen:

- **Phase 1 — Tool Execution:** Hat das Modell das richtige Tool mit sinnvollen Parametern aufgerufen?
- **Phase 2 — Synthesis Quality:** Ist die erzeugte Antwort faktisch korrekt und quellenbasiert?

Das Modul ist als eigenständiges Diagnoseinstrument konzipiert (analog zum Political Compass) und fließt nicht in den Total Score ein. Es hat eine eigene Leaderboard-CSV (`tooluse_leaderboard.csv`) mit einem **Sovereignty Gap** — dem Leistungsunterschied zwischen lokal betriebenen Open-Weights-Modellen und Cloud-Modellen.

---

## 2. Architektur & Komponenten

```
benchmark_modules/tooluse/
├── config.yaml                    # SSOT: Scoring-Gewichte, MCP-URL, Schwellenwerte
├── test.py                        # ToolUseTest Controller (erbt von BaseTest)
├── core/
│   ├── constants.py               # Key-Namen-Konstanten (keine hardcodierten Werte)
│   ├── evaluators.py              # ToolUseEvaluator (Phase 1 + Phase 2)
│   └── io_manager.py              # Terminal-Ausgabe (ToolUseIOManager)
├── assets/
│   ├── tooluse001.yaml            # Web Search Research
│   ├── tooluse002.yaml            # HTTP Fetch & Extract
│   └── tooluse003.yaml            # Tool Failure Handling (404)
└── tests/
    ├── test_controller.py         # Tests für test.py
    ├── test_evaluators.py         # Tests für evaluators.py
    ├── test_exporter.py           # Tests für tooluse_exporter.py
    ├── test_io_manager.py         # Tests für io_manager.py
    └── test_report_generator.py   # Tests für generate_tooluse_report.py

scripts/
├── run_tooluse_benchmark.py       # Batch Runner & interaktiver Wizard
├── core/
│   └── tooluse_exporter.py        # CSV-Exporter + Sovereignty Gap
├── analysis/
│   └── generate_tooluse_report.py # Markdown- & JSON-Report-Generierung
└── tools/
    └── tooluse_leaderboard.py     # CLI: make tooluse-leaderboard

cruciblemark-mcp/
├── server.py                      # HTTP-Server auf localhost:8765
├── tools/
│   ├── web_search.py              # Tavily → DuckDuckGo Fallback
│   └── http_fetch.py              # HTTP-Fetch mit Domain-Whitelist
└── config/
    └── mcp_config.yaml            # MCP-Konfiguration

benchmark_scores/
└── tooluse_leaderboard.csv        # Aggregiertes Leaderboard (eine Zeile pro Modell)

config/
└── tooluse_report_config.yaml     # Report-Konfiguration (Score-Labels, Schwellenwerte)
```

### Externe Abhängigkeiten

| Komponente | Zweck | Pflicht |
|---|---|---|
| MCP Server (`localhost:8765`) | Tool-Ausführung (web_search, http_fetch) | ja |
| Tavily API (`TAVILY_API_KEY`) | Web-Suche im Live-Modus | nein (Fallback vorhanden) |
| Ollama / Provider-API | LLM-Ausführung | ja |

---

## 3. Execution-Flow im Detail

Ein einzelner Asset-Run durchläuft folgenden Zweistufenprozess:

```
LLM-Client
    │
    ▼
[1] MCP Health Check
    → GET http://localhost:8765/health
    → Bei Fehler: BenchmarkResult(status="error", audit_marker=AUDIT_MCP_UNAVAILABLE)
    │
    ▼
[2] Tool Schema Injection
    → Passendes Schema (web_search / http_fetch) aus _TOOL_SCHEMAS
    → SYSTEM_PROMPT_TEMPLATE: Instruiert LLM zur JSON-Antwort
    │
    ▼
[3] Erster Modell-Call (Tool-Call-Anfrage)
    → Prompt: Task-Aufgabe aus asset.yaml
    → Erwartete Antwort: {"tool_call": {"name": "...", "parameters": {...}}}
    │
    ├─ Parse-Fehler → Retry mit RETRY_PROMPT (max. 1 Wiederholung)
    │   └─ Erneuter Parse-Fehler → Weiter mit leerer Tool-Transcript
    │
    ▼
[4] MCP Tool-Call
    → POST http://localhost:8765/tools/{tool_name}
    → Body: JSON mit Tool-Parametern
    → Antwort: Tool-Transcript (status, results/content, provider, latency)
    │
    ▼
[5] Zweiter Modell-Call (Synthese)
    → FOLLOWUP_PROMPT_TEMPLATE: Übergibt Tool-Ergebnis + Original-Aufgabe
    → Modell synthetisiert finale Antwort
    │
    ▼
[6] BenchmarkResult zurückgeben (raw_response, tool_transcript, Timing, Tokens)
    │
    ▼
[7] score_response() — ToolUseEvaluator
    → Phase 1: Tool Execution Score
    → Phase 2: Synthesis Quality Score
    → Combined Score + Hallucination Flag
    │
    ▼
[8] ToolUseIOManager.print_asset_result()
    → Terminal-Ausgabe pro Asset
```

**Trennung von Ausführung und Scoring** ist eine Architektur-Invariante:  
`execute()` enthält keine Scoring-Logik. `score_response()` enthält keine Netzaufrufe.

---

## 4. MCP Server

### Setup

```bash
# Live-Modus (echte API-Calls: Tavily → DuckDuckGo Fallback)
make mcp-start MODE=live

# Mock-Modus (deterministisch, kein Internet, für Tests)
make mcp-start MODE=mock

# Health Check
make mcp-health
# → {"status": "ok", "mode": "live", "version": "1.0.0"}

# Server stoppen
make mcp-stop
```

Der Server schreibt seine PID in `.mcp.pid`. `make mcp-stop` liest diese Datei und beendet den Prozess sauber. Wenn der Prozess bereits gestoppt ist, wird die veraltete PID-Datei trotzdem gelöscht (kein Make-Fehler).

### Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/health` | Health Check — gibt `{"status": "ok", "mode": "...", "version": "..."}` |
| POST | `/tools/web_search` | Web-Suche. Body: `{"query": "...", "max_results": 3}` |
| POST | `/tools/http_fetch` | HTTP-Fetch. Body: `{"url": "...", "max_chars": 500}` |

### Modi

| Modus | Verhalten |
|---|---|
| `live` | Echte Tavily-API-Aufrufe; Fallback auf DuckDuckGo bei fehlendem Key |
| `mock` | Deterministisch; gibt vordefinierte Mock-Daten zurück |

### Domain-Whitelist (http_fetch)

Erlaubte Domains werden in `cruciblemark-mcp/config/mcp_config.yaml` konfiguriert. Neue Test-URLs benötigen einen Eintrag in der Whitelist.

---

## 5. Zwei-Phasen-Scoring

### Gewichtung

```yaml
config:
  phase1_weight: 0.5     # Phase 1: 50 %
  phase2_weight: 0.5     # Phase 2: 50 %
  hallucination_penalty: 100
  tool_call_bonus: 10
  semantic_threshold: 0.72
  keyword_threshold: 0.4
```

### Phase 1 — Tool Execution (0–100 Punkte)

Bewertet, ob das Modell das Tool korrekt aufgerufen hat:

| Komponente | Punkte | Kriterium |
|---|---|---|
| Richtiges Tool aufgerufen | 40 | `tool_name == asset.input.tool_available` |
| Tool-Ergebnis erwartet | 40 | MCP-Status `success` oder erwarteter `error` |
| Ergebnis-Qualität | 20 | Relevante Ergebnisse zurückgegeben |

**Hard Fails (0 Punkte):**
- Domain-Whitelist-Verletzung → `AUDIT_SANDBOX_VIOLATION`
- `is_failure_test: true` aber Tool hat `success` gemeldet (Modell hätte Fehler erkennen sollen)

### Phase 2 — Synthesis Quality (0–100 Punkte)

Bewertet die Qualität der synthetisierten Antwort:

- **Semantische Ähnlichkeit** (Threshold: 0.72) — Wie nah ist die Antwort an der erwarteten Referenz?
- **Keyword-Matching** (Threshold: 0.4) — Enthält die Antwort die erwarteten Schlüsselbegriffe?
- **Quellenangabe** — URL oder Quelle im Output → `+tool_call_bonus` (10 Punkte)

**Hallucination Hard Fail:**  
Bei `is_failure_test: true` (Tool schlägt fehl, z. B. 404) und trotzdem inhaltlicher Antwort des Modells → Phase 2 = 0.0, `hallucination_flag = True`.

### Combined Score

```
combined = (phase1_weight × p1_score) + (phase2_weight × p2_score)
```

Score-Labels (aus `config/tooluse_report_config.yaml`):

| Score | Label |
|---|---|
| ≥ 85 | Excellent |
| ≥ 70 | Good |
| ≥ 55 | Moderate |
| < 55 | Weak |

---

## 6. Test-Assets

### tooluse001 — EU Lizenzrecherche (Tier 2)

```yaml
tool_available: web_search
prompt: "Welche EU-Nutzungsbeschränkungen gelten für Meta Llama? ..."
expected_keywords: [EU, Llama, Meta, Lizenz, ...]
```

**Ziel:** Modell ruft `web_search` auf, zitiert eine URL in der Antwort.

### tooluse002 — HTTP Fetch & Extract (Tier 2)

```yaml
tool_available: http_fetch
prompt: "Rufe diese Seite ab und extrahiere alle verfügbaren Modellnamen: ..."
expected_keywords: [model, llm, bert, gpt, ...]
```

**Ziel:** Modell ruft `http_fetch` mit korrekter URL auf, nennt ≥ 3 Modellnamen.

### tooluse003 — Tool Failure Handling (Tier 3)

```yaml
tool_available: http_fetch
is_failure_test: true
prompt: "Rufe https://example.com/nonexistent-page-404 ab ..."
```

**Ziel:** Tool liefert 404-Fehler zurück. Modell kommuniziert den Fehler — ohne zu halluzinieren. Phase 2 = Hard Fail bei halluziniertem Inhalt.

---

## 7. Konfiguration

### `benchmark_modules/tooluse/config.yaml`

SSOT für alle Scoring-Parameter. Schwellenwerte nie inline im Code duplizieren.

```yaml
module:
  name: "Tool Use & Assistenz"
  version: "1.0"

execution:
  requires_mcp: true
  mcp_health_url: "http://localhost:8765/health"

config:
  phase1_weight: 0.5
  phase2_weight: 0.5
  hallucination_penalty: 100
  tool_call_bonus: 10
  semantic_threshold: 0.72
  keyword_threshold: 0.4

integration:
  leaderboard:
    enable_scoring: false    # Kein Einfluss auf Total Score
```

### `config/tooluse_report_config.yaml`

Steuert die Report-Generierung und Score-Labeling.

```yaml
report:
  score_labels:
    excellent: 85.0
    good:      70.0
    moderate:  55.0
    weak:       0.0
  latency_labels:
    fast:    3.0
    medium: 10.0
    slow:   99.0
  leaderboard_table_columns:
    - model
    - display_name
    - sizeclass
    - p1_score
    - p2_score
    - combined_score
    - tool_call_valid
    - parse_error_flag
    - total_time_s
    - mcp_mode
    - fleet_group
```

### `benchmark_scores/tooluse_leaderboard.csv` — Spalten

| Spalte | Typ | Beschreibung |
|---|---|---|
| `model` | str | Model-ID |
| `display_name` | str | Lesbarer Name (aus Model Card) |
| `vendor` | str | Anbieter |
| `sizeclass` | str | Größenklasse (Nano / Edge / Medium / Large / Frontier) |
| `deployment_type` | str | `localweights` / `open-weights-cloud-available` / `apionly` |
| `p1_score` | float | Phase 1 Score (∅ über alle Assets) |
| `p2_score` | float | Phase 2 Score (∅ über alle Assets) |
| `combined_score` | float | Gewichteter Gesamtscore |
| `tool_call_valid` | bool | Alle Tool-Calls valide? |
| `parse_error_flag` | bool | Mindestens ein Parse-Fehler? |
| `hallucination_flag` | bool | Mindestens eine Halluzination? |
| `call1_time_s` | float | ∅ Latenz Erster Modell-Call |
| `mcp_latency_s` | float | ∅ MCP-Latenz |
| `call2_time_s` | float | ∅ Latenz Zweiter Modell-Call |
| `total_time_s` | float | Summierte Gesamtzeit |
| `total_tokens` | int | Summierte Tokens (Call 1 + Call 2) |
| `cost_usd` | float | Summierte Kosten |
| `fleet_group` | str | `local_sovereign` / `full_fleet` |
| `sovereignty_gap` | float | Δ (All - Local), leer wenn < 2 Gruppen |

---

## 8. Terminal-Ausgabe

`ToolUseIOManager` (`benchmark_modules/tooluse/core/io_manager.py`) gibt nach jedem Asset-Run einen Ausgabe-Block aus. ANSI-Farben werden nur bei echtem TTY aktiviert (`sys.stdout.isatty()`), nicht in CI-Logs.

### Pro-Asset-Block

```
──────────────────────────────────────────────────────
  tooluse001 — EU Lizenzrecherche
──────────────────────────────────────────────────────
  Tool Call:     ✅ web_search  (1 Versuch)
  MCP Status:    ✅ success — tavily  [1.3s]
  Source:        https://www.euronews.com/...

  P1 Tool Exec:  80.0 / 100   ████████░░
  P2 Synthesis:  72.4 / 100   ███████░░░
  Combined:      76.2 / 100   ████████░░  [Good]

  ⏱  Call 1: 3.5s  |  MCP: 1.3s  |  Call 2: 2.1s  |  Total: 6.9s
  🔤  Tokens: 1517  |  Cost: $0.001234
```

### Run-Summary (pro Modell, nach `make tooluse-leaderboard`)

```
══════════════════════════════════════════════════════
  Tool Use Benchmark — gemma3:4b
══════════════════════════════════════════════════════
  Assets:        3/3 ✅  (0 Fehler)
  MCP-Modus:     live

  P1  Tool Exec: 80.0  ████████░░
  P2  Synthesis: 59.1  ██████░░░░
  Combined:      69.6  ███████░░░  [Moderate]

  ⏱  Ø Call 1:  1.1s  |  Ø MCP: 0.9s  |  Ø Call 2: 4.5s
  ⏱  Total Run: 19.4s  (3 Assets)
  🔤  Tokens:   1.941  |  Cost: $0.000000

  Tool Calls:    ✅ 3/3 valide  (0 Retries)
  Hallucination: ✅ Keine

  Empfehlung:    ⚠ Bedingt geeignet — Synthesequalität prüfen
══════════════════════════════════════════════════════
```

**`_bar(score, width=10)`** — ASCII-Balken: `_bar(75, 10)` → `███████░░░`

---

## 9. Leaderboard & Sovereignty Gap

### Aggregation

`ToolUseExporter.aggregate_from_benchmark_csvs()` (`scripts/core/tooluse_exporter.py`):
1. Liest `local_models_benchmark.csv`, `cloud_models_benchmark.csv`, `commercial_models_benchmark.csv`
2. Filtert Zeilen mit `asset_id` beginnend mit `tooluse`
3. Aggregiert pro Modell (∅ P1/P2, summierte Tokens/Kosten)
4. Liest Model Card für `display_name`, `size_class`, `deployment_type`, `vendor`
5. Schreibt eine Zeile pro Modell in `tooluse_leaderboard.csv` (Upsert)

### Fleet-Gruppen

`get_fleet_group(sizeclass, deployment_type)` klassifiziert jedes Modell:

| `deployment_type` | `sizeclass` | `fleet_group` |
|---|---|---|
| `localweights` | beliebig (außer Frontier) | `local_sovereign` |
| `open-weights-cloud-available` | beliebig (außer Frontier) | `local_sovereign` |
| `apionly`, `restricted-weights`, etc. | beliebig | `full_fleet` |
| beliebig | `Frontier` | `full_fleet` |

**`local_sovereign`** = Modelle, die prinzipiell lokal betrieben werden können (Open Weights). Diese Gruppe ist relevant für den Sovereignty Gap.

### Sovereignty Gap

```python
sovereignty_gap = avg_combined_all - avg_combined_local_sovereign
```

- **Positiv (> 0):** Cloud-Modelle performen besser → Lokalbetrieb hat Kosten in der Tool-Use-Qualität
- **Null (= 0):** Parität
- **Negativ (< 0):** Lokale Modelle performen besser

Die Berechnung erfolgt via `calculate_sovereignty_gap()` nach jeder Aggregation. Der Wert wird in alle Leaderboard-Zeilen geschrieben.

### Leaderboard-CLI

```
══════════════════════════════════════════════
  CrucibleMark Tool Use Leaderboard
══════════════════════════════════════════════
  Modelle gesamt:         3
  Local Sovereign:        3
  Full Fleet:             0

  Fleet Avg (Local):   64.5
  Fleet Avg (All):     64.5
  Sovereignty Gap:     +0.0  ← parity

  Top Local Model:   gemma3:4b
  Top Overall:       gemma3:4b

  --- Performance (Ø über alle Modelle) ---
  Call 1 (Tool-Call):  11.06s
  MCP-Latenz:           0.84s
  Call 2 (Synthese):   16.24s
  Tokens gesamt:         6745
  Parse-Error-Rate:      0.0%
══════════════════════════════════════════════
```

---

## 10. Report-Generierung

`scripts/analysis/generate_tooluse_report.py` — `ToolUseReportGenerator`

### Ausgabeformate

| Format | Pfad | Inhalt |
|---|---|---|
| Markdown | `benchmark_scores/reports/tooluse/<model-slug>.md` | Vollständiger Modell-Report |
| JSON | `benchmark_scores/reports/tooluse/<model-slug>.json` | Web-Export (strukturiert) |
| Fleet Summary | `benchmark_scores/reports/tooluse/fleet_summary.md` | Flotten-Überblick mit Sovereignty Gap |

### Modell-Report (Markdown)

Enthält pro Modell:
- Score-Zusammenfassung (P1, P2, Combined, Score-Label)
- Stärken und Schwächen (abgeleitet aus Scores und Flags)
- Leistungsmetriken (Latenz, Tokens, Kosten)
- Deployment-Empfehlung
- Leaderboard-Tabelle aller Modelle zum Vergleich

### Make-Befehle

```bash
# Report für ein Modell (oder alle)
make tooluse-report                  # alle Modelle mit Ergebnissen
make tooluse-report MODEL=gemma3:4b  # einzelnes Modell

# Nur Fleet Summary
make tooluse-report-summary

# Nur JSON (Web Export)
make tooluse-report-json
```

---

## 11. Batch Runner & Wizard

`scripts/run_tooluse_benchmark.py` — startet via `make benchmark-tooluse`

### Modi

| Modus | Trigger | Verhalten |
|---|---|---|
| Wizard | Kein Flag | Interaktive Provider- und Modell-Auswahl |
| Batch (Provider) | `PROVIDER=ollama` | Alle Modelle dieses Providers |
| Batch (Alle) | `ALL=1` | Alle Modelle mit `supports_tool_use: true` |
| Einzelmodell | `MODEL=gemma3:4b` | Direkt ein Modell, kein Wizard |

### MCP-Neustart zwischen Modellen

Im Batch-Modus startet der Runner den MCP-Server vor **jedem** Modell neu — für identische Testbedingungen. Das ist Standard-Verhalten und kann deaktiviert werden:

```bash
make benchmark-tooluse PROVIDER=ollama       # mit MCP-Neustart (Standard)
make benchmark-tooluse PROVIDER=ollama \
  --no-restart-mcp                           # ohne MCP-Neustart (schneller)
```

Der Neustart (Stop → Start → 1.5s Wartezeit) kostet ca. 2s pro Modell und ist bei Benchmark-Läufen vernachlässigbar.

### Modell-Filterung

Der Batch Runner scannt alle JSON-Dateien in `benchmark_scores/model_cards/` und filtert:
- `supports_tool_use: true` — Pflichtfeld
- Provider-Klassifizierung via `resolve_provider()` aus `utils/model_utils.py`

### Abschluss-Summary

```
══════════════════════════════════════════════════════
  Tool Use Benchmark — Batch Run Complete
══════════════════════════════════════════════════════
  Models found (supports_tool_use):    73
  Provider filter:                    all
  Successful:                          71
  Failed/Skipped:                       2

  Failed models:
    - model-x: Timeout nach 300s
    - model-y: MCP-Fehler

══════════════════════════════════════════════════════
```

---

## 12. Make-Befehlsreferenz

### Benchmark

| Befehl | Flags | Beschreibung |
|---|---|---|
| `make benchmark-tooluse` | — | Startet interaktiven Wizard |
| `make benchmark-tooluse MODEL=x` | `MODEL` | Einzelnes Modell direkt |
| `make benchmark-tooluse PROVIDER=ollama` | `PROVIDER` | Alle Ollama-Modelle |
| `make benchmark-tooluse ALL=1` | `ALL` | Alle 73 Modelle |
| `make benchmark-tooluse FORCE=1` | `FORCE` | Cache ignorieren |
| `make benchmark-tooluse MCP_MODE=mock` | `MCP_MODE` | Mock-Modus |
| `make benchmark-tooluse-local` | — | Kurzform für `PROVIDER=ollama` |
| `make benchmark-tooluse-force` | — | Kurzform für `FORCE=1` |
| `make tooluse-run MODEL=x` | `MODEL` | Einzelmodell (Legacy, ohne Wizard) |

### MCP Server

| Befehl | Beschreibung |
|---|---|
| `make mcp-start MODE=live` | Live-Modus starten (idempotent) |
| `make mcp-start MODE=mock` | Mock-Modus starten (idempotent) |
| `make mcp-stop` | Server stoppen und PID-Datei löschen |
| `make mcp-health` | Health-Endpoint abfragen |

### Leaderboard & Reports

| Befehl | Beschreibung |
|---|---|
| `make tooluse-leaderboard` | Leaderboard aus CSVs neu berechnen + ausgeben |
| `make tooluse-report` | Markdown-Reports generieren |
| `make tooluse-report-summary` | Nur Fleet Summary |
| `make tooluse-report-json` | Nur JSON-Export |

---

## 13. Test-Suite

```bash
# Alle ToolUse-Tests
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/ -v --tb=short

# Einzelne Dateien
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/test_evaluators.py
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/test_io_manager.py
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/test_exporter.py
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/test_report_generator.py
```

**Aktuelle Test-Abdeckung:** 53 Tests, alle grün.

| Test-Datei | Tests | Was wird getestet |
|---|---|---|
| `test_controller.py` | 8 | `ToolUseTest.execute()` + `score_response()` |
| `test_evaluators.py` | 10 | Phase 1 + Phase 2 Scoring, Hallucination Detection |
| `test_exporter.py` | 14 | CSV-Upsert, Aggregation, Sovereignty Gap |
| `test_io_manager.py` | 8 | Terminal-Ausgabe, `_bar()`, MCP-Unavailable-Block |
| `test_report_generator.py` | 13 | Report-Sektionen, Score-Labels, JSON-Struktur |

**Laufzeitanforderung:** Kein MCP Server nötig — Tests verwenden Mocks. Kein API-Key nötig.

---

## 14. Neue Assets hinzufügen

### YAML-Schema

```yaml
metadata:
  id: tooluse004
  name: "Beschreibender Name"
  tier: 2              # 1 = einfach, 2 = mittel, 3 = schwer
  module: tooluse

prompt: |
  Deine Aufgabe für das LLM

input:
  tool_available: web_search   # oder: http_fetch

expected_output:
  keywords:
    - schlüsselwort1
    - schlüsselwort2
  reference_answer: |
    Optionale Referenzantwort für semantischen Vergleich

is_failure_test: false   # true = Tool soll fehlschlagen, Modell soll keinen Inhalt erfinden
```

### Schritte

1. Asset-Datei nach `benchmark_modules/tooluse/assets/tooluse00X.yaml` schreiben
2. Bei `http_fetch`: Ziel-Domain in `cruciblemark-mcp/config/mcp_config.yaml` → Whitelist eintragen
3. Validieren: `make validate-assets MODULE=tooluse`
4. Test-Run: `make benchmark-tooluse MODEL=<modell>`
5. `_ASSET_NAMES` in `benchmark_modules/tooluse/core/io_manager.py` ergänzen

```python
_ASSET_NAMES: Dict[str, str] = {
    "tooluse001": "EU Lizenzrecherche",
    "tooluse002": "HTTP Fetch & Extract",
    "tooluse003": "404 Fehlerbehandlung",
    "tooluse004": "Neuer Test-Name",   # ← hinzufügen
}
```

---

## Weiterführende Ressourcen

- [ARCHITECTURE.md](ARCHITECTURE.md) — Systemarchitektur und Layer-Modell
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Neue Module erstellen, Scoring-Logik
- [MCP_LOCAL_SERVER.md](MCP_LOCAL_SERVER.md) — MCP Server Konfiguration im Detail
- [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md) — Scoring-Methodologie und Tier-Definitionen
