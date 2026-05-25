# CrucibleMark: Maintenance & Fehlerbehebungen

**Zielgruppe:** Entwickler, die Änderungen am Scoring-System oder der Architektur nachvollziehen wollen.
**Inhalt:** Changelog-Einträge für Bugfixes, Architektur-Entscheidungen und Verhaltensänderungen

## Tool Use Module — Phase-A Calibration: MCP Alignment, CV Gate & Attribution Bias Fix

**Datum:** 2026-05-24
**Status:** Abgeschlossen

### Kontext

Nach den ersten Verifikations-Runs gegen `claude-sonnet-4-6`, `gpt-5.4-mini` und `gemma3:4b` im
Mock-Modus wurden mehrere Kalibrierfehler identifiziert, die die Messgenauigkeit des Benchmarks
beeinträchtigten. Alle Korrekturen wurden mit einem Re-Run verifiziert; End-Durchschnitt
claude-sonnet-4-6: **85.2%** (P1 = 96).

### 1. MCP Standard Alignment (`http_fetch` → `fetch`)

**Problem:** Das Modul verwendete `http_fetch` als Tool-Name. Anthropics MCP-Referenzimplementierung
(`@modelcontextprotocol/server-fetch`) definiert den Standard als `fetch`. Modelle, die ihrem
MCP-Training folgen (u. a. Claude Sonnet 4.6), riefen `fetch` auf und erhielten P1 = 0 — kein
Kompetenzproblem, sondern ein Namens-Mismatch im Benchmark.

**Lösung:** Route `POST /tools/http_fetch` → `POST /tools/fetch` in `cruciblemark-mcp/server.py`.
Konstante `TOOL_HTTP_FETCH = "http_fetch"` → `"fetch"` in `constants.py` (SSoT-Kaskade).
`AUTHORIZED_TOOLS` + `CANONICAL_TOOLS` in `tool_adapter_audit.py` aktualisiert. Asset-YAMLs
tooluse001/002/003/005: `tool_available`, `mcp_endpoint`, `expected_tool` angepasst.

### 2. tooluse005 — Blocked-Status durch Sprachmismatch im Prompt

**Problem:** Der deutsche Prompt ließ Modelle `de.wikipedia.org`-URLs konstruieren. Diese Domain
ist nicht in der MCP-Whitelist → `blocked` → P1 = 0. Der URL-Pfad-Präzisions-Test war damit
nicht auswertbar.

**Lösung:** Prompt um `"Verwende die englischsprachige Wikipedia (en.wikipedia.org)."` ergänzt.
Der URL-Pfad-Test (korrekter Pfad `/wiki/Python_(programming_language)`) bleibt vollständig aktiv.

### 3. Content Verification Gate — `_OVERLAP_WINDOW = 3` (war 4)

**Problem:** `_has_content_overlap()` suchte nach verbatim 4-Wort-Sequenzen in der Modellantwort.
Alle technischen Identifikatoren in tooluse004/005-Fixtures sind ≤ 3 Wörter ("Open LLM Leaderboard",
"id Software"). Obwohl Modelle diese Eigennamen korrekt aus dem Fixture übernahmen, fand das
4-Wort-Fenster keinen Treffer → fälschliche B2-Einstufung (parametrisch) → P2 auf 35 gedeckelt.

**Lösung:** `_OVERLAP_WINDOW = 3` in `core/tool_adapter_audit.py`. Neue Unit-Test-Klasse
`test_content_verification.py` (7 Tests für alle CV-Zustände A/B1/B2/C und Failure-Test-Exempt).

### 4. Mock-Fixture-Qualität (web_search Excerpts)

**Problem:** `_FIXTURE_SEARCH["_default"]` enthielt einzeilige Excerpts (~80 Zeichen). Damit
konnten Modelle keine inhaltlich substanzielle P2-Antwort liefern; der Judge bewertete die
generischen Antworten mit mittleren Scores unabhängig von der tatsächlichen Modellkompetenz.

**Lösung:** Alle drei Default-Excerpts auf ~250 Zeichen mit mehreren Fakten erweitert. Dritter
Eintrag: `raw.githubusercontent.com/openai/evals` → `huggingface.co/mistralai` (thematisch
konsistenter mit dem tooluse004-LLM-Rankings-Kontext).

### 5. `web.search`-Variante — Tool-Name-Normalisierung

**Problem:** `gpt-5.4-mini` verwendet `web.search` (Punkt statt Unterstrich). Diese Variante
war nicht in `AUTHORIZED_TOOLS` eingetragen → normalisiert zu `unknown` → MCP-Endpunkt
`/tools/web.search` (404) → P1 = 0.

**Lösung:** `"web.search"` als Alias in `AUTHORIZED_TOOLS["web_search"]` in
`core/tool_adapter_audit.py` ergänzt.

### 6. tooluse002 v2.1.0 — Rubrik-Korrektur: Attribution Bias

**Problem:** `uncertainty_handling`-Gewicht 0.25 listete "Klare Attribution an die abgerufene
Seite" als positiv bewertetes Kriterium und "Fakten ohne Quellennennung" als Abzugsgrund.
Das benachteiligte systematisch Modelle mit autoritativem Integrationsstil (Claude: "Quake II
ist ein Name-only-Sequel") gegenüber Modellen mit expliziter Quellenbindung (GPT-Stil: "Laut
dem Wikipedia-Artikel..."). Bei inhaltlich gleichwertigen, quellenbasierten Antworten entstanden
Scores von 57 vs. 88 — ein Rubrik-Defekt, kein Modell-Unterschied.

**Lösung:**
- Gewichte: `factuality: 0.65`, `hallucination_risk: 0.30`, `uncertainty_handling: 0.05`
- `uncertainty_handling.acceptable`: "Klare Attribution" entfernt; "Antwort bleibt im Rahmen
  der Fixture-Inhalte" als Kriterium eingesetzt
- `uncertainty_handling.unacceptable`: "Fakten ohne Quellennennung" entfernt; "Fakten
  hinzufügen die nicht im Fixture stehen" als Kernkriterium eingesetzt

**Wichtig für spätere Leser:** Dieses Fix verbessert **nicht das Modell**, sondern trennt
die Bewertung sauber zwischen Inhaltsqualität und stilistischer Quellenbindung. Eine Antwort,
die factually korrekt ist und sich im Fixture-Rahmen hält, soll nicht schlechter bewertet werden
als eine mit expliziten "laut Wikipedia"-Phrasen.

**Ergebnis:** tooluse002 P2 Claude Sonnet 4.6: 57 → 86. Combined: 93.1%.

### 7. Infrastructure-Fixes

- **`TIMEOUT_PER_MODEL`**: 300s → 600s in `scripts/run_tooluse_benchmark.py` (Anthropic-API
  benötigt an langsamen Tagen bis zu 147s für ein einzelnes Asset)
- **`make mcp-stop`**: `pkill -f "cruciblemark-mcp/server.py"` als Fallback wenn `.mcp.pid`
  fehlt (Szenario: Server über Batch-Runner gestartet, kein PID-Eintrag)

***

## Provider Shortcode System & Versioning Overhaul (v3.5)

**Datum:** 2026-07-15
**Status:** Abgeschlossen

### Problembeschreibung

Das Leaderboard zeigte für viele Modelle `k.A.` als Versions-String (fehlende Behandlung neuer Modell-Familien wie Qwen, GLM, MiniMax, o4-Series, Kimi). Außerdem fehlte jede Information, über welchen Provider ein Modell getestet wurde — bei Modellen wie `kimi-k2`, die sowohl via OpenRouter als auch Groq laufen, war das Ergebnis ohne Provider-Kontext nicht interpretierbar.

### Lösung

1. **`_PROVIDER_SHORTCODES` + `get_provider_shortcode()` in `utils/model_utils.py`:**
   Neues Mapping-Dict und neue Funktion für die Shortcodes `API` (proprietäre Direkt-APIs), `OR` (OpenRouter), `GR` (Groq), `LCL` (Ollama/Lokal).

2. **`short_code`-Feld pro Provider in `benchmark_config.yaml`:**
   Jeder Provider-Block trägt jetzt ein `short_code`-Feld. Beide Orte (Config + `model_utils.py`) müssen synchron gehalten werden.

3. **Erweiterte Versionserkennung in `get_model_version()`:**
   Neue Handler für `codestral`/`magistral` (mit Vorrang-Check für magistral, verhindert false `2312`-Match), `qwen`, `glm`, `minimax`, `o4`, erweiterte kimi-Regex für `-thinking`/`-instruct`-Suffixe.

4. **Provider re-attach in `scripts/leaderboard/__init__.py`:**
   `score_calculator.py` verliert die `provider`-Spalte beim `groupby`. Nach `calculate_scores()` wird sie per pandas `mode()`-Merge neu angehängt. Danach: `Provider Code`-Spalte via `get_provider_shortcode()`.

5. **Kombinierte Anzeige in `scripts/leaderboard/exporter.py`:**
   - Kompakt-CSV: `Version` = `k2/OR` (kombinierter String)
   - Detailliert-CSV: `Version` + `Provider Code` als separate Spalten

6. **CSV-Migration via `scripts/maintenance/migrate_model_versions.py`:**
   Einmalig ausgeführt — hat alle `k.A.`/`unknown`/`""` Versionswerte in den drei Benchmark-CSVs rückwirkend befüllt (`.bak`-Backups wurden angelegt).

### Hinweis für Entwickler

Wird ein neues Modell hinzugefügt, das ein Provider-Shortcode-Lookup benötigt, **immer beide SSoT-Stellen aktualisieren**: `_PROVIDER_SHORTCODES` in `utils/model_utils.py` und das `short_code`-Feld in `benchmark_config.yaml`.

***

## Leaderboard Numerator Fix (v2.2)

**Datum:** 2026-03-16
**Status:** Behoben

### Problembeschreibung

Nach dem Entkoppeln des Political Compass zeigte der `Tests Run`-Zähler noch immer einen überhöhten Numerator (z. B. "44/43"). `scripts/leaderboard/score_calculator.py` iterierte blind über alle einzigartigen Kategorien im Datensatz, ohne zu prüfen, ob `enable_scoring: false` in den Modul-Configs gesetzt war. So erfasste der Calculator versehentlich Political Compass- oder System Probe-Artefakte.

### Lösung

1. **Category Filtering:** `_calculate_run_counts` in `score_calculator.py` erhielt ein `counting_cats`-Set. Nur Module mit aktivem Scoring (`enable_scoring: True`) oder explizitem `display_test_count` fließen in die Zählung ein.
2. **Docs Cleanup:** Veraltete `display_test_count: 9`-Artefakte aus Modul-READMEs und Entwicklungsanleitungen entfernt.

***

## Political Compass Architecture Decoupling (v2.1)

**Datum:** 2026-03-14
**Status:** Behoben

### Problembeschreibung

Die Logik, die das Political Compass Modul über "Ghost Rows" in die Haupt-DataFrames eintrug, führte zu mathematisch ungenauen UI-Metadaten ("Test Runs: 165/156"). Das Einbetten eines rein informativen ethischen Surveys in die primäre DataFramestruktur verfälschte Code-Quality-Test-Zähler und Zeitbenchmarks.

### Lösung

1. **Full Decoupling:** Ghost-Row-Injektionsroutinen in `scripts/leaderboard/data_loader.py` für das PC-Modul entfernt. Die Config-Eigenschaft `display_test_count` des Moduls entkoppelt.
2. **Isolating Outputs:** Ausgaben aufgeteilt in `benchmark_scores/political_compass_results.csv` (Run Records) und `benchmark_scores/political_compass_leaderboard.csv` (Shift-Aggregationen).
3. **Post-Evaluation Stitching:** Die finalen Schritte von `generate_leaderboard.py` extrahieren nur den Vanilla Alignment Tag und den Shift-String als eigenständige rechtsbündige Textspalte, unabhängig vom `score_calculator.py`.

***

## Ghost Entries & Versioning Refactor

**Datum:** 2026-02-06
**Status:** Behoben

### Problembeschreibung

Das Leaderboard zeigte Duplikat-Einträge für einzelne Modelle (z. B. "Claude Haiku"). Ein Eintrag enthielt Benchmark-Scores, ein zweiter "Ghost Entry" nur Political Compass-Ergebnisse.
**Ursache:** Inkonsistente Versions-Strings zwischen Benchmark Runner (`8717af19`) und Political Compass Runner (`unknown`).

### Lösung

1. **Centralization:** Versions-Logik nach `utils/model_utils.py` (`get_model_version`) als SSOT verschoben.
2. **Deterministic Mapping:** Behavior-Hash-Fingerprinting entfernt, um Ghost-Duplikate zu verhindern.
3. **Data Patch:** Split-Einträge in CSVs zusammengeführt und historische Cache-Einträge angeglichen.
4. **Golden Standard Optimization:** Political Compass aus der Golden Standard-Generierung ausgeschlossen (Methodik-Update).

***

## Aggregation Verification Report

**Datum:** 2026-02-04
**Status:** Behoben

### Befunde

Das Leaderboard zeigte zuvor "46/37 Tests Run". Die Diskrepanz entstand, weil das `Political Compass`-Modul über ein explizites Override (neun logische Tests) zum **Numerator** beitrug, aber wegen deaktiviertem Scoring (`enable_scoring: false`) aus dem **Denominator** ausgeschlossen blieb.

### Verifikationsdaten

```python
aggregation_report = {
    "total_unique_assets_in_csv": 38,
    "breakdown": {
        "scoring_assets": 37,
        "political_compass_rows": 1
    },
    "logical_test_counts": {
        "scoring_tests": 37,
        "political_compass_logical": 9,
        "total_logical": 46
    },
    "previous_display": "46/37",
    "fixed_display": "46/46",

    "aggregation_rules": {
        "method": "last-value-wins",
        "implementation": "df.drop_duplicates(subset=[model, version, asset_id], keep='last')",
        "models_with_duplicates": "All (Historical runs are preserved in raw CSV, filtered at load time)",
        "duplicate_runs_intentional": True
    }
}
```

### Maßnahmen

1. **Code Update:** `scripts/leaderboard/score_calculator.py` bezieht jetzt Module mit explizitem `display_test_count` in den "Expected Count" (Denominator) ein, auch wenn Scoring deaktiviert ist.
   - *Ergebnis:* Denominator stieg von 37 auf 46. Das Leaderboard zeigt nun "46/46".

2. **Duplicate Handling:** `data_loader.py` verarbeitet Mehrfach-Runs korrekt und wählt jeweils den neuesten Eintrag anhand des Timestamps.
   - *Ergebnis:* Benchmarks sind beliebig oft wiederholbar. Das Leaderboard spiegelt stets den aktuellen Stand wider.

### Reproduktion

```bash
python scripts/maintenance/verify_counts.py
```

***

## API Timeout & Nested Pydantic Serialization (v3.0.0)

**Datum:** 2026-03-18
**Status:** Behoben

### Problembeschreibung

Zwei strukturelle Probleme blockierten die kontinuierliche Evaluierung strikt zensierter Modelle (Gemini, Claude) im Political Compass:

1. **Refusal Stalling:** Modelle, die "Sorry, I can't answer this" zurückgaben, lösten einen sofortigen Fehler beim Metrik-Parsing aus. Das brach die Batch-Evaluierungssequenz ab, anstatt alternative Permutationen zu versuchen.
2. **Verify Anomalies Crashes:** Das Prüfen von Shift-Werten erzeugte einen `AttributeError`. Der Code rief `.get()` nativ auf dem Pydantic-Schema-Return (`base_result.raw_response`) auf. Dieser ist strikt als JSON-String gespeichert, nicht als generisches Dict.

### Lösung

1. **3-Tier Refusal Loop:** Eine robuste `while True`-Schleife mit progressiven Temperatur-Checks (`0.1`, `0.4`, `0.7`) greift direkt in der Ausführungsschleife (`_run_single_block` in `political_compass/test.py`). Das System bricht Zensurfilter autonom auf.
2. **Pydantic Deserialize:** Alle `raw_response`-Lesezugriffe in Verify-Skripten nutzen jetzt `json.loads(str)`, um Dict-Konformität vor dem Zugriff auf verschachtelte Variablen (Vanilla/Forced) sicherzustellen.
