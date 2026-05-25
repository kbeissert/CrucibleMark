# Tool Use Benchmark — Unified Scoring Standard

**Version:** 3.12.0 (5-Asset-Erweiterung — Phase A + Phase B)  
**Status:** Phase B kalibriert (v1.2.0) | Phase A Kalibrierung ausstehend  
**Last Updated:** 2026-05-24

---

## Overview

Alle fünf Tool Use Assets nutzen ein einheitliches, kompaktes Scoring-Framework:

```yaml
golden_answer: [Referenzantwort der Auditors]

evaluation:
  phase2_rubric:
    weights:
      factuality: 0.5
      hallucination_risk: 0.25
      uncertainty_handling: 0.25
    
    factuality:
      must_include: [...]
      must_not_include: [...]
    
    hallucination_risk:
      red_flags: [...]
      acceptable_patterns: [...]
    
    uncertainty_handling:
      acceptable: [...]
      unacceptable: [...]
    
    output_format:
      required_structure: [...]
      acceptable_refusal: [true/false]
```

Die YAML ist **Single Source of Truth**. Diese Dokumentation ist Referenz, kein Dogma.

---

## Scoring Dimensions

### Factuality (0.5)
Korrektheit und Vollständigkeit gegen die golden_answer.
- **3 Punkte**: Alle must_include, keine must_not_include
- **2 Punkte**: Hauptpunkte korrekt, ≤1 Auslassung
- **1 Punkt**: Teilweise korrekt, signifikante Lücken
- **0 Punkte**: Falsch, unvollständig oder missverstanden

### Hallucination Risk (0.25)
Erfundenes, nicht Quellengestütztes.
- **3 Punkte**: Null Halluzinationen, alle Aussagen attributierbar
- **2 Punkte**: ≤1 fragwürdige Aussage, leicht zu identifizieren
- **1 Punkt**: Mehrere fragwürdige Aspekte vermischt mit korrekten
- **0 Punkte**: Umfangreiche oder kritische Halluzinationen

### Uncertainty Handling (0.25)
Angemessene Differenzierung zwischen bekannt und spekulativ.
- **3 Punkte**: Klare Grenzen, Unsicherheit zugestanden
- **2 Punkte**: Ggfs. zu selbstsicher in Details
- **1 Punkt**: Häufig unklar, ob spekulativ oder faktisch
- **0 Punkte**: Durchweg spekulativ oder zu selbstsicher

---

## Computation

```
score = (factuality * 0.5 + hallucination_risk * 0.25 + uncertainty_handling * 0.25) / 3 * 100
hallucination_flag = (hallucination_risk ≤ 1)
```

---

## Combined Score Computation (with Guardrail)

Phase 1 (Tool Execution) and Phase 2 (Synthesis Quality) are independently scored, then combined with a safety guardrail:

**Base Formula:**
```
combined = (p1 * 0.4) + (p2 * 0.6)
```

**P1 Scoring Stufen:**

| Bedingung | P1 Score |
|---|---|
| Kein Tool-Aufruf | 0 |
| Falsches Tool aufgerufen | 20 |
| Richtiges Tool, Fehler-Status (non-200) oder leerer Content | 40 |
| Richtiges Tool + korrekter Status | 80 |
| Richtiges Tool + korrekter Status + Content ≥ 100 Zeichen (`http_fetch`)¹ | 100 |
| Richtiges Tool + `web_search` + `golden_source_domains`-Treffer | 100 |
| Richtiges Tool + `web_search` ohne `golden_source_domains` (neutral) | 100 |

¹ Content-Prüfung nur für `http_fetch` non-failure-tests. Bei `is_failure_test: true` ist source quality nicht anwendbar — max. P1=80.

**Guardrail Thresholds:**

| Condition | Result |
|-----------|--------|
| `tool_call_valid = false` OR `p1 = 0` | Capped at 60 |
| `p1 < 40` | `combined - 10` (malus) |
| `p1 < 60` | `combined - 3` (malus) |
| `p1 >= 60` | No malus applied |

**Rationale:**
- P2 remains **independent** — high synthesis quality is always valuable diagnostic information
- Combined score is guarded to prevent weak execution from being masked by excellent synthesis
- Tiered penalties reflect severity: hard execution failures (p1 < 40) get -10; moderate issues (p1 < 60) get -3

---

## Hallucination Cap (Zweistufenregel)

Wenn der LLM-Judge `hallucination_detected: true` zurückgibt, wird **P2 gekappt** — unabhängig vom ursprünglichen Judge-Score. Die Schwere der Halluzination bestimmt den Cap anhand des konvertierten P2-Scores **vor** der Kappung:

| P2 vor Cap | Klassifikation | Cap |
|---|---|---|
| ≤ 40 | **Fabrication** — vollständige Erfindung, ganzer Themenblock | `cap_hard = 15` |
| > 40 | **Milde Halluzination** — partielle Fabrication, einzelne Details | `cap_moderate = 35` |

**Schwellenwert:** `threshold_severe = 40` (konfigurierbar in `config/scoring.yaml`)

**Rationale:**
- Ein niedriger Judge-Score (0–2 / 5) mit `hallucination_detected` signalisiert vollständige Fabrication — das Modell hat ganze Themenblöcke erfunden
- Ein hoher Judge-Score (3–4 / 5) mit `hallucination_detected` bedeutet, die Antwort war überwiegend korrekt, enthält aber fabricierte Details
- Beide Fälle sollen sichtbar unter dem „brauchbaren" Bereich (> 50) bleiben, aber Fabrication fällt deutlich tiefer als partielle Halluzination
- Die Kappung gilt nur im Judge-Modus (nicht im Fallback-Modus)

**Calibration Examples (v3.11.0 — 2026-05-24):**
- Claude Sonnet 4.6: P1=95, P2=65.0 → combined=79.98
- Claude Sonnet 4.5: P1=85, P2=70.3 → combined=77.63
- Hermes 4 70B: P1=90, P2=62.7 → combined=76.33
- GPT-5.4: P1=75, P2=65.0 → combined=70.02

---

## Asset-Specific Profiles

### tooluse001: EU Lizenzrecherche
**Kritisch:** Unterscheidung multimodale (Llama 4, Vision — EU-beschränkt) vs. textbasierte Modelle (Llama 3.1/3.2 — ohne Einschränkung). Korrekte Quellenangabe.

**Common Fails:**
- "Alle Llama-Modelle sind in der EU verboten" (Pauschalaussage)
- Erfundene Policy-Klauseln
- Keine Quellenangabe trotz spezifischer Claims
- Fehlende text/multimodal-Differenzierung

### tooluse002: HTTP Fetch & Extract  
**Kritisch:** Seiten-gebundene Modellnamen — Llama 3.2, Llama 3.2 Vision, Llama Guard. Reproduktion von Trainings-Vorwissen (Llama 4, Code Llama, ältere Versionen) ist ein Fail.

**Common Fails:**
- Llama 4 oder Code Llama als Hauptergebnis (Trainings-Vorwissen)
- Nicht-Llama-Modelle (GPT, BERT, T5 etc.)
- Falsche Use-Case-Zuordnungen
- "Es gibt wahrscheinlich auch X" (Spekulation)

### tooluse003: Failure Handling (404 Test)
**Kritisch:** Null Toleranz für Halluzinationen. Fehler muss dem Tool zugeordnet werden.

**HARD RULE:**
- Jede spezifische Aussage über Seiteninhalte = AUTOMATIC HARD FAIL für Halluzination
- "Die Seite zeigt...", "Laut der Seite..." = instant fail

---

## Phase A — Tool Intelligence: Asset-Profile

### tooluse004: Tool Selection (web_search)
**Testdimension:** Wählt das Modell `web_search` für eine Recherche-Aufgabe, wenn keine URL gegeben ist?

**P1-Spread (primär):**
- `web_search` korrekt → P1=100 (Mock: `_default`-Fixture enthält `huggingface.co`-URL → `golden_source_domains`-Treffer)
- `http_fetch` (falscher Typ) → P1=0
- Kein Tool-Call → P1=0

**Common Fails (P1):**
- Modell versucht `http_fetch` mit einer erfundenen Recherche-URL
- Modell antwortet ohne Tool-Call aus Parameterwissen

**Common Fails (P2):**
- Spezifische Benchmark-Scores oder Modell-Rankings ohne Basis im Tool-Ergebnis
- Keine Synthese aus den abgerufenen Suchergebnissen

**Hinweis für den Judge:** Mock liefert HuggingFace-Leaderboard, Llama und OpenAI Evals als Ergebnisse — kein EU AI Act-Content. Modelle im State B2 (parametrische Antwort über LLM-Rankings ohne Tool-Basis) werden auf cap_B2=35 gedeckelt.

### tooluse005: URL Construction (http_fetch)
**Testdimension:** Kann das Modell die korrekte Wikipedia-URL aus eigenem Wissen ableiten?

**P1-Spread (primär):**
- `https://en.wikipedia.org/wiki/Python_(programming_language)` → registriertes Fixture, 1047 Zeichen → P1=100
- Andere Wikipedia-URL (z.B. `/wiki/Python`) → nicht registriert, ~55 Zeichen < 100 → P1=80
- Nicht-whitegelistete Domain (z.B. `python.org`, `docs.python.org`) → geblockt → P1=0
- `web_search` statt `http_fetch` → falscher Typ → P1=0

**Common Fails (P1):**
- Modell ruft `python.org` oder andere nicht-whitegelistete Domains auf
- Modell wählt `web_search` statt direkten Wikipedia-Fetch
- Wikipedia-URL ohne Disambiguierungssuffix (`_(programming_language)`)

**Common Fails (P2):**
- Python-Features aus Parameterwissen ohne Bezug auf den abgerufenen Artikel
- Falsches Erscheinungsjahr (Python 1991 ist korrekt, andere Jahre = Fail)

---

## Integration

### Judge Input
1. Candidate response (Modelloutput)
2. Asset YAML (golden_answer + evaluation_rubric)
3. Scoring dimensions

### Judge Output
- p2_score (0–100)
- hallucination_flag (True/False)
- audit_block (1–2 Sätze pro Dimension)

---

## References

- Asset definitions: `benchmark_modules/tooluse/assets/tooluse00{1,2,3,4,5}.yaml`
- Judge implementation: `benchmark_modules/tooluse/core/judge_handler.py` (TBD)
- Quick reference: `JUDGE_CHECKLIST.md`
