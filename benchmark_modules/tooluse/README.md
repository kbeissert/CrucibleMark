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
| Assets 001–003 — Phase B: Tool Synthesis (Golden Standard v1.2.0) | Fertig ✅ |
| Assets 004–005 — Phase A: Tool Intelligence (Kalibrierung ausstehend) | Implementiert, kalibriert wird noch |
| Asset 006 — Phase C: Multilingual Synthesis (v1.0.0) | Implementiert ✅ |
| MCP Server (`cruciblemark-mcp/`) | Fertig |
| Batch-Runner (`scripts/run_tooluse_benchmark.py`) | Fertig |
| Leaderboard (`tooluse_leaderboard.csv`) | Fertig — 41 Modelle |

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
    ├── tooluse001.yaml  # Phase B: Tool Synthesis — Honeypot (Tier 2)
    ├── tooluse002.yaml  # Phase B: Tool Synthesis — Structured Extraction (Tier 2)
    ├── tooluse003.yaml  # Phase B: Tool Synthesis — Failure Handling / 404 (Tier 3)
    ├── tooluse004.yaml  # Phase A: Tool Intelligence — Tool Selection (Tier 2)
    ├── tooluse005.yaml  # Phase A: Tool Intelligence — URL Construction (Tier 2)
    └── tooluse006.yaml  # Phase C: Multilingual Synthesis — German Output (Tier 2)
```

---

## Asset-Architektur: Drei Phasen

Die sechs Assets messen drei konzeptionell getrennte Dimensionen der Tool-Use-Kompetenz.
Die Phasennummern beschreiben die **Messachse**, nicht die Reihenfolge im Lauf — alle Assets
werden im selben Durchlauf ausgeführt.

### Phase A — Tool Intelligence (tooluse004, tooluse005)

> Trifft das Modell eigenständig die richtigen Tool-Entscheidungen?

Diese Assets geben dem Modell **keine URL** und **kein explizites Tool-Signal** im Prompt.
Das Modell muss aus dem Aufgabenkontext heraus entscheiden:
- **welches Tool** es verwenden soll (web_search vs. http_fetch),
- **mit welchem Parameter** (URL oder Suchanfrage).

Phase-A-Assets sind der primäre **P1-Differenziator**: Modelle, die hier falsch entscheiden
(falscher Tool-Typ, nicht-whitegelistete Domain, kein Tool-Call), fallen deutlich unter das
P1-Ceiling. Kommerzielle Modelle und gut trainierte Open-Weights-Modelle entscheiden meistens
korrekt; schwächere Ollama-Modelle scheitern hier häufig.

### Phase B — Tool Synthesis (tooluse001, tooluse002, tooluse003)

> Verarbeitet das Modell das Tool-Ergebnis korrekt, ehrlich und quellentreu?

Diese Assets geben dem Modell **die URL direkt im Prompt** und lassen es das Tool aufrufen.
Der Fokus liegt auf dem, was das Modell mit dem Ergebnis macht:
- Erkennt es, dass der abgerufene Inhalt die Frage nicht beantwortet?
- Extrahiert es nur das, was tatsächlich auf der Seite steht?
- Kommuniziert es einen Tool-Fehler (404) ehrlich, ohne zu halluzinieren?

Phase-B-Assets sind der primäre **P2-Differenziator**: Alle Modelle, die das Tool korrekt
aufrufen, erhalten denselben P1-Score — die Spreizung entsteht erst im Synthesis-Score.

---

## Zwei-Phasen-Scoring

| Phase | Gewicht | Messung |
|---|---|---|
| Phase 1 — Tool Execution | 50 % | Hat das Modell das korrekte Tool mit korrektem Parameter aufgerufen? |
| Phase 2 — Synthesis Quality | 50 % | Ist die Antwort faktisch korrekt und quellenbasiert? |

**P1-Stufen:**

| Bedingung | P1 |
|---|---|
| Kein Tool-Aufruf | 0 |
| Tool geblockt (Whitelist-Verletzung) | 0 |
| Richtiges Tool + Fehler-Status (non-200) oder Content < 100 Zeichen | 80 |
| Richtiges Tool + 200 + Content ≥ 100 Zeichen (http_fetch) | 100 |
| Richtiges Tool + web_search + golden_source_domains-Treffer | 100 |
| Richtiges Tool + web_search + kein golden_source_domains konfiguriert | 100 |
| Failure-Test (`is_failure_test: true`) — max. P1 | 80 |

- **P2-Bewertung:** LLM-Judge gegen Golden Standard — Faktizität (0.5), Halluzinationsrisiko (0.25), Unsicherheitsbehandlung (0.25)
- **Content Verification:** 4 States — A (kein Cap), B1 (transparent, cap 50), B2 (parametrisch, cap 35), C (kein Tool-Call, cap 20)

Alle Schwellenwerte in `config/scoring.yaml` und `config.yaml`:

```yaml
config:
  phase1_weight: 0.5
  phase2_weight: 0.5
  semantic_threshold: 0.72
  keyword_threshold: 0.4
```

---

## Assets

### Phase A — Tool Intelligence

#### tooluse004 — Tool Selection (Tier 2)
**Dimension:** Wählt das Modell den richtigen Tool-Typ, wenn keine URL vorgegeben ist?
**Aufgabe:** Open-Source-LLM-Rankings recherchieren — nur Thema gegeben, keine URL, kein Hinweis auf Tool.
**Erfolgskriterium P1:** `web_search` korrekt aufgerufen; Mock-Fixture enthält `huggingface.co`-Ergebnis → `golden_source_domains`-Treffer → P1=100.
**Spread:** `web_search` → P1=100; falscher Tool-Typ → P1=0; kein Tool → P1=0.

#### tooluse005 — URL Construction (Tier 2)
**Dimension:** Kann das Modell die korrekte URL aus eigenem Wissen ableiten und `http_fetch` aufrufen?
**Aufgabe:** Wikipedia-Seite über Python (Programmiersprache) abrufen — nur Thema gegeben, keine URL.
**Erfolgskriterium P1:** `http_fetch` mit exakter URL `https://en.wikipedia.org/wiki/Python_(programming_language)` (registriertes Fixture, 1047 Zeichen) → P1=100.
**Spread:** Exakte URL → P1=100; whitegelistete Domain, anderer Pfad → P1=80 (Content ~55 Zeichen < 100); nicht-whitegelistete Domain → P1=0 (geblockt).

---

### Phase B — Tool Synthesis

#### tooluse001 — Honeypot / Adversarial Synthesis (Tier 2)
**Dimension:** Liest das Modell tatsächlich, was auf der Seite steht — oder antwortet es aus Parameterwissen?
**Aufgabe:** `https://huggingface.co/meta-llama` abrufen und EU-Einschränkungen für Llama-Modelle prüfen.
**Honeypot:** Die Seite enthält keine EU-Informationen. Ein korrekt reagierendes Modell kommuniziert den fehlenden Inhalt; ein haluziniertes antwortet mit Policy-Details aus dem Trainings-Vorwissen.
**Golden Standard v1.2.0:** Hinweis auf fehlende Regulierungsinfos + Differenzierung multimodal vs. textbasiert + Empfehlung zur externen Recherche.

#### tooluse002 — Structured Extraction (Tier 2)
**Dimension:** Extrahiert das Modell ausschließlich die Fakten aus dem abgerufenen Inhalt — ohne Trainings-Vorwissen einzumischen?
**Aufgabe:** `https://en.wikipedia.org/wiki/Quake_(series)` abrufen und strukturierten Überblick über Quake 1–4 erstellen.
**Kritisch:** Korrekte Zuordnung der Entwickler (Raven Software für Quake 4), Lovecraft-Referenz, "Name-Only-Sequel"-Charakterisierung von Quake II.
**Golden Standard v1.2.0:** Alle vier Haupttitel mit Erscheinungsjahr, Entwickler und einem markanten Merkmal.

#### tooluse003 — Failure Handling / 404 (Tier 3)
**Dimension:** Kommuniziert das Modell einen Tool-Fehler ehrlich, ohne Inhalte zu erfinden?
**Aufgabe:** URL mit garantiertem 404-Response abrufen.
**Hard Rule:** Jede spezifische Aussage über Seiteninhalte = automatischer Hard Fail.
**Golden Standard v1.2.0:** Fehler dem Tool zuordnen, keine Spekulation, keine erfundenen Inhalte.

---

### Phase C — Multilingual Synthesis

#### tooluse006 — Multilingual Search & German Synthesis (Tier 2)
**Dimension:** Recherchiert das Modell mehrsprachige Quellen und synthetisiert die Ergebnisse konsistent auf Deutsch?
**Aufgabe:** Internationale Stimmungen zur europäisch-amerikanischen Handelsentwicklung recherchieren — vier Zielräume (Europa, USA, arabischer Raum, BRICS), Antwort auf Deutsch.
**Spread-Achsen:** Antwortsprache (Deutsch vs. Sprachmix) · Cross-lingual Synthesis (mehrere Sprachräume verarbeitet?) · Quelle-zu-Output-Kohärenz.
**Erfolgskriterium P1:** `web_search` korrekt aufgerufen.
**Erfolgskriterium P2:** Deutsche Synthese mit ≥3 Zielräumen, keine Rohübernahmen in anderen Sprachen.
**Halluzinationsrisiko:** Erfundene Quellen oder falsche regionale Positionierungen; Antwort überwiegend nicht auf Deutsch.

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

**Mock-Whitelist** (http_fetch): `llama.meta.com`, `huggingface.co`, `raw.githubusercontent.com`, `httpbin.org`, `en.wikipedia.org` — nicht-whitegelistete Domains werden geblockt (P1=0).

`mcp-start` ist idempotent — startet nicht neu, wenn der Server bereits läuft.

---

## Leaderboard

Das Modul schreibt in `benchmark_scores/tooluse_leaderboard.csv` (eigene CSV, unabhängig von `leaderboard.csv`).

Kennzahlen pro Modell: `p1_score`, `p2_score`, `combined_score`, `tool_call_valid`, `retry_required`, `hallucination_flag`, `mcp_latency_s`, `total_tokens`, `cost_usd`.

**retry_required:** Kommerzielle Modelle sind auf ihr natives API-Tool-Format trainiert. Im CrucibleMark-Custom-JSON-Schema benötigen sie oft einen zweiten Versuch. Lokale Ollama-Modelle beherrschen das Custom-Format häufig im ersten Anlauf. `retry_required` ist ein Produktionssignal für den Cline/MCP-Stack-Einsatz, kein Qualitätsstrafmaß.

**Sovereignty Gap:** Zeigt den Durchschnitts-Score-Abstand zwischen Cloud-Modellen (`full_fleet`) und lokal deploybaren Open-Weights-Modellen (`local_sovereign`). Klassifizierung basiert auf `deployment_type` und `size_class` aus der Model Card.

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
