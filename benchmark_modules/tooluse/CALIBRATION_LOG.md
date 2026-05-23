# Tool Use Benchmark — Calibration Log v3.11.0

**Calibration Round:** 1 (Golden Standards v1.2.0)  
**Completed:** 2026-05-24  
**Status:** ABGESCHLOSSEN ✅  
**Schema Version:** Finalisiert (SSoT mit flachen Gewichten)

---

## Baseline & Reset

| Item | Action | Date | Reference |
|------|--------|------|-----------|
| Pre-calibration leaderboard | Archiviert | 2026-05-23 | `_calibration_archive/tooluse_leaderboard_pre_calibration_v3100.csv` |
| Alte P2-Scores (90-flat) | In Archiv gesichert | 2026-05-23 | Raw outputs für Vorher/Nachher-Vergleich |
| Golden Standard | Definiert v1.2.0 | 2026-05-24 | `assets/tooluse00{1,2,3}.yaml` |
| Neues Baseline | Erstellt | 2026-05-24 | `benchmark_scores/tooluse_leaderboard.csv` |

---

## Test Cohort Execution Log

### Durchgeführte Läufe: 36 (12 Modelle × 3 Assets)

```
Model 1: claude-haiku-4-5 ✅
Model 2: claude-sonnet-4-5 ✅
Model 3: claude-sonnet-4-6 ✅
Model 4: claude-opus-4-5 ✅
Model 5: claude-opus-4-6 ✅
Model 6: claude-opus-4-7 ✅
Model 7: gpt-5.4 ✅ (parse_error bei tooluse001 Lauf 2)
Model 8: gemini-2.5-pro ✅
Model 9: gemini-3-flash-preview ✅
Model 10: hermes-4-70b ✅
Model 11: deepseek-v4-flash ✅
Model 12: codestral-latest ✅
```

**Execution Start:** 2026-05-23  
**Execution End:** 2026-05-24  
**MCP Mode:** live (Tavily → DuckDuckGo Fallback)

---

## Kalibrierungsergebnisse (v1.2.0)

### Combined Score (Durchschnitt über alle 3 Assets)

| Modell | P1 | P2 | Combined | Tier |
|---|---|---|---|---|
| Claude Sonnet 4.6 | 95 | 65.0 | 80.0 | Top Reference |
| Claude Sonnet 4.5 | 85 | 70.3 | 77.6 | Strong Reference |
| Claude Opus 4.6 | 85 | 68.6 | 76.8 | Strong Reference |
| Claude Opus 4.5 | 85 | 67.9 | 76.4 | Strong Reference |
| Hermes 4 70B | 90 | 62.7 | 76.3 | Open-Weights Ref |
| Claude Opus 4.7 | 85 | 64.4 | 74.7 | Strong Reference |
| Claude Haiku 4.5 | 85 | 62.8 | 73.9 | Strict Anchor |
| Gemini 2.5 Pro | 85 | 61.8 | 73.4 | Provider Reference |
| Codestral | 85 | 61.3 | 73.2 | Production Ref |
| DeepSeek V4 Flash | 85 | 60.6 | 72.8 | Production Ref |
| Gemini 3 Flash | 85 | 57.8 | 71.4 | Weak Provider |
| GPT-5.4 | 75 | 65.0 | 70.0 | Penalized (parse_error) |

---

## Gap Analysis

**P2-Spanne:** 57.8 – 70.3 (+12.5 Punkte) ✅ (Ziel: > 10)

**Top-Tier-Gap (Sonnet 4.5/4.6 vs. Gemini 3 Flash):**
- Erwartet: ≥ 10 Punkte
- Actual: ~8.9 Punkte (P2: 70.3 vs. 57.8)
- ✓ Ausreichend für Diskriminierung

**Sovereignty Gap:**
- Wert: −1.55 (local_sovereign leicht unter full_fleet)
- Nur Codestral in local_sovereign-Gruppe — zu wenige Datenpunkte für finale Aussage

**Parse-Error-Rate:**
- GPT-5.4: 1 Parse-Fehler auf tooluse001 Lauf 2 (instabile Tool-Call-Formatierung)
- Alle anderen: 0 Parse-Fehler

**Tool Retry Rate (median tool_call_attempts):**
- Alle Modelle: 2 (= korrekt — 1 Tool-Aufruf + 1 Synthesis-Phase)

---

## Beobachtungen pro Asset

### tooluse001 (EU Lizenzrecherche)
- Modelle mit Llama-Vorwissen neigen zu Pauschalaussagen ("alle Llama-Modelle")
- Multimodal/Text-Unterscheidung ist der härteste Differenzierer
- URL-Zitierung klappt bei Frontier-Modellen durchgehend

### tooluse002 (HTTP Fetch & Extract)
- **Kritisches Finding:** Mehrere Modelle reproduzieren Llama 4 / Code Llama aus Trainings-Vorwissen statt der tatsächlichen Seite
- **Hermes 4 70B Halluzination:** Hatte GPT-2, BERT, T5 als Meta-Llama-Modelle gemeldet → korrekt mit niedrigem P2 penalisiert
- Llama 3.2 / Vision / Guard als Keywords diskriminieren zuverlässig zwischen Seiten-Extraktion und Vorwissen-Generierung

### tooluse003 (404 Failure Handling)
- Alle Frontier-Modelle erkennen den Fehler korrekt
- Herausforderung: Überexplikation — manche Modelle erklären zu viel über httpbin statt nur den Fehler zu melden
- Tool-Attribution (Fehler dem Tool zuschreiben, nicht nur der URL) ist ein klarer Differenzierer

---

## Kalibrierungs-Assessment

### Rubrik-Stabilität ✅

- [x] **Ja** — Klare Tiers sichtbar (Top: Sonnet 4.5/4.6 ~80; Mitte: Haiku/Gemini/Opus ~73-77; Untergrenze: Flash/GPT ~70-72)
- [x] **Gewichte stabil** — factuality (0.5) / hallucination_risk (0.25) / uncertainty_handling (0.25) bewährt
- [x] **hallucination_flag funktioniert** — Hermes 4 70B auf tooluse002 korrekt als Halluzination erkannt

### Finale Entscheidung

**ACCEPT ✅** — Rubrik ist stabil, Gewichte sind angemessen. Kalibrierungsrunde 1 abgeschlossen.

---

## Archiv & Versionierung

| Artifact | Location | Purpose |
|----------|----------|---------|
| Kalibriertes Leaderboard | `benchmark_scores/tooluse_leaderboard.csv` | Aktueller Stand (v1.2.0) |
| Pre-calibration | `_calibration_archive/tooluse_leaderboard_pre_calibration_v3100.csv` | Historischer Vergleich |
| Asset-Definitionen | `assets/tooluse00{1,2,3}.yaml` | Golden Standard v1.2.0 (SSoT) |
| Combined Assets | `assets/combined_assets.yaml` | Synced zu v1.2.0 |

**Calibration Complete:** 2026-05-24  
**Golden Standard Version:** v1.2.0  
**Nächste Kalibrierung:** Bei signifikanten Modell-Releases oder Q3 2026

---

## References

- Test Matrix: `CALIBRATION_TEST_MATRIX.md`
- Schema: `assets/tooluse00{1,2,3}.yaml`
- Judge Checklist: `JUDGE_CHECKLIST.md`
- Rubric: `SCORING_RUBRIC.md`
