# Tool Use Pipeline Diagnostics — Fehlerquellen trennen

**Status:** v1.0 (Preliminary)  
**Purpose:** Separate MCP/Parser/Search issues from actual model limitations  
**Approach:** A/B/C-Sanity-Check mit drei Szenarien

---

## Problem Statement

Bei Claude Sonnet 4.6 beobachten wir:
- P1 = 40.0 (Tool Execution)
- P2 = 100.0 (Synthesis Quality)
- Combined = 64.0 (mit Guardrail)

**Fragen:**
- Ist das ein echtes Modell-Verhalten oder ein Pipeline-Problem?
- Ist die Tool-Antwort zu dünn (Tavily/MCP-Quality)?
- Parse-Fehler führen zu Retry-Overhead?
- Token-Limits schneiden die Antwort ab?

---

## Diagnostic Ansatz: 3 Szenarien

### 1. MCP-Flow (Normal)
```
Prompt → Model → Tool-Call → MCP/Tavily → Tool-Output → Synthesis
```
**Was wird getestet:**  
- Full stack: Model parsing + MCP integration + Search quality + Synthesis  
- Wenn hier Score < 60, aber in anderen Szenarien > 80: Pipeline-Problem

### 2. Reference-Output (Kuratiert)
```
Prompt → Model → Tool-Call (ignored) → Known-Good Tool-Output → Synthesis
```
**Was wird getestet:**  
- Modell-Fähigkeit mit garantiert guter Eingabe  
- Wenn hier Score > 80: Model kann mit guten Daten arbeiten  
- Wenn hier Score < 60: Model hat echte Limitation

### 3. Stub-Direct (Minimal)
```
Prompt → Model → Tool-Call (ignored) → Minimal Struct. Response → Synthesis
```
**Was wird getestet:**  
- Lowest friction: Model erhält absolutes Minimum  
- Wenn hier Score > 60: Model ist robust  
- Wenn hier Score < 40: Model hat tiefe Limitation

---

## Interpretation: Gap-Matrix

| MCP | Reference | Stub | Gap Muster | Diagnose |
|---|---|---|---|---|
| 40 | 80 | 80 | MCP >> Reference | 🔴 **Tavily/Search Quality** |
| 40 | 40 | 80 | Reference < Stub | ⚠️ Model kann minimal aber nicht gutdaten |
| 40 | 40 | 40 | All < 60 | 🔴 **Echte Model Limitation** |
| 80 | 80 | 80 | Alle > 70 | ✅ **Keine Probleme erkannt** |
| 60 | 50 | 40 | Fallend trend | 🟡 **Parse/Format Degradation** |

---

## Implementierung

### Neue Module

1. **`core/diagnostics.py`** — PipelineDiagnostician
   - `measure_tool_output()`: Bytes, snippets, quality grade
   - `measure_parse()`: Parse attempts, errors, structure
   - `build_diagnostic()`: Aggregated metrics
   - `log_diagnostic()`: Structured logging

2. **`DIAGNOSTIC_SCENARIOS.md`** — Test templates
   - Reference outputs (hand-curated)
   - Stub outputs (minimal valid)
   - Scenario descriptions

3. **`scripts/run_diagnostic_scenarios.py`** — Runner
   - Load assets
   - Run all 3 scenarios für alle Modelle
   - Generate gap-matrix report

### Integration in test.py

`score_response()` now captures:
```python
result.data["pipeline_diagnostic"] = {
    "asset_id": "tooluse001",
    "scenario": "mcp_flow",
    "tool_call_valid": True,
    "output_quality": "partial",  # "full", "partial", "minimal", "empty"
    "parse_attempts": 1,
    "is_expected": True,
}
```

---

## Wie man es nutzt

### Quick Check (1 Modell, 3 Assets)
```bash
python benchmark_modules/tooluse/scripts/run_diagnostic_scenarios.py \
  --model claude-haiku-4-5 \
  --assets tooluse001 tooluse002 tooluse003 \
  --output diagnostic_haiku.md
```

**Output:** Gap-Matrix mit Diagnose für jedes Asset

### Full Diagnostic (56-Modell-Fleet)
```bash
for model in $(cat model_list.txt); do
  python benchmark_modules/tooluse/scripts/run_diagnostic_scenarios.py \
    --model "$model" \
    --output "diagnostic_${model}.md"
done
```

Dann alle Reports aggregieren → Fleet-wide Gap-Analyse

---

## Erwartete Erkenntnisse

### Falls Gap > 20 (MCP vs Reference)
→ **Tavily/MCP Quality Problem**

**Nächste Schritte:**
1. MCP-Logs prüfen: Welche Suchanfrage kam an?
2. Tavily-Response analysieren: Snippet-Länge, Quellen-Qualität
3. Ggfs. Search-Query verfeinern im Asset

### Falls Gap 10-20 (Moderate)
→ **Parse/Handling Overhead**

**Nächste Schritte:**
1. Parsing-Fehler (retry-count) analysieren
2. Token-Budgets prüfen: Genug für Synthesis?
3. System-Prompt verfeinern für Tool-Call-Zuverlässigkeit

### Falls Reference ≥ 80, MCP < 60
→ **Model kann mit gutem Input arbeiten, aber Pipeline degradiert Input**

**Nächste Schritte:**
1. Synthesis-Prompt verbessern für Low-Data-Szenarien
2. Tool-Output-Filtering optimieren
3. Fallback-Strategien testen

### Falls Alle < 60
→ **Echte Model Capability Grenze**

**Akzeptieren und:** 
1. Scoring-Rubric anpassen (zu streng?)
2. Model für diese Task nicht empfehlen
3. Oder Asset-Schwierigkeit überprüfen

---

## Schwellenwerte

| Metrik | Grün | Gelb | Rot |
|---|---|---|---|
| Gap (MCP-Reference) | < 5 | 5-20 | > 20 |
| Reference P1 | ≥ 70 | 50-70 | < 50 |
| Stub P1 | ≥ 60 | 40-60 | < 40 |
| Parse Attempts | 1 | 2 | > 2 |
| Output Quality | "full" | "partial" | "minimal"/"empty" |

---

## Logs & Telemetrie

Jeder Benchmark-Run speichert jetzt:
```json
{
  "asset_id": "tooluse001",
  "model_id": "claude-haiku-4-5",
  "scenario": "mcp_flow",
  "tool_call_valid": true,
  "output_metrics": {
    "total_bytes": 456,
    "snippet_count": 2,
    "avg_snippet_len": 228.0,
    "excerpt_quality": "partial"
  },
  "parse_metrics": {
    "parse_attempts": 1,
    "parse_success": true,
    "first_attempt_success": true,
    "contains_tool_call": true
  },
  "p1_score": 80.0,
  "is_expected": true
}
```

→ Logs gehen in `outputs/tooluse_metrics.jsonl` für spätere Analyse

---

## Nächste Schritte

1. ✅ Framework implementiert (diagnostics.py, scenarios, runner)
2. → Einen 7-Modell-Subset mit Diagnostics laufen lassen
3. → Gap-Matrix generieren
4. → Fehlerquellen nach Matrix klassifizieren
5. → Pro Fehlerquelle korrektur-Plan definieren
6. → Full 56-Modell-Run mit Updates
