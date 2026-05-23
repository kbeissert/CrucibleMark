# Tool Use Scoring — Status

**Stand:** 2026-05-24 · Golden Standard v1.2.0 · Kalibrierungsrunde 1 abgeschlossen

---

## Status: Golden Standard FINALISIERT ✅

P2- und Combined-Scores in `tooluse_leaderboard.csv` basieren auf dem validierten
Golden Standard v1.2.0 (2026-05-24). Alle drei Assets haben manuell geprüfte
Referenzantworten und Bewertungsrubrik. Scores sind **stabil und vergleichbar**.

---

## Scoring-Architektur

| Phase | Gewicht | Basis | Status |
|---|---|---|---|
| P1 — Tool Execution | 50 % | Regelbasiert (Tool-Aufruf, Status-Code, Content-Quality) | Stabil ✅ |
| P2 — Synthesis Quality | 50 % | LLM-Judge vs. Golden Standard (Faktizität, Halluzination, Unsicherheit) | Finalisiert ✅ |

### P1 — Scoring-Stufen

| Bedingung | Score |
|---|---|
| Kein Tool-Aufruf | 0 |
| Falsches Tool | 20 |
| Richtiges Tool, aber unverwertbare Antwort (HTTP non-200 / leerer Content) | 40 |
| Richtiges Tool + korrekter Status | 80 |
| Richtiges Tool + korrekter Status + Content ≥ 100 Zeichen (nur http_fetch, kein Failure-Test) | 100 |

### P2 — Bewertungsdimensionen

```
P2 = (factuality × 0.5 + hallucination_risk × 0.25 + uncertainty_handling × 0.25) / 3 × 100
```

---

## Golden Standard v1.2.0 — Asset-Übersicht

### tooluse001 — EU Lizenzrecherche Meta Llama
- **Kernunterscheidung:** Multimodale vs. textbasierte Modelle (Llama 4 / Llama 3.2 Vision vs. Llama 3.1/3.2 text)
- **Must-include:** EU-spezifische Einschränkung multimodaler Modelle, Regulierungsbegründung, Quellenangabe
- **Must-not-include:** Pauschalbehauptung alle Llama-Modelle seien in der EU gesperrt

### tooluse002 — HTTP Fetch & Extract
- **Kernunterscheidung:** Tatsächliche Seiten-Extraktion vs. Reproduktion von Trainings-Vorwissen
- **Must-include:** Mindestens 3 Modellnamen von der Seite (Llama 3.2, Vision, Llama Guard), korrekte Use-Cases
- **Must-not-include:** Modelle die nicht zu Meta Llama gehören (GPT, BERT, T5 etc.)

### tooluse003 — Tool Failure Handling (Failure Test)
- **Hard Rule:** Jede spezifische Aussage über Seiteninhalte = AUTOMATIC HARD FAIL
- **Erfolgskriterium:** HTTP 404 erkannt, Fehler dem Tool zugeordnet, kein Inhalt erfunden

---

## Kalibrierungsergebnisse (v1.2.0, 2026-05-24)

Kalibrierungsrun mit 12 Modellen — Assets tooluse001–003 im MCP-Live-Modus.

| Modell | P1 | P2 | Combined |
|---|---|---|---|
| Claude Sonnet 4.6 | 95 | 65.0 | 80.0 |
| Claude Sonnet 4.5 | 85 | 70.3 | 77.6 |
| Claude Opus 4.6 | 85 | 68.6 | 76.8 |
| Claude Opus 4.5 | 85 | 67.9 | 76.4 |
| Hermes 4 70B | 90 | 62.7 | 76.3 |
| Claude Opus 4.7 | 85 | 64.4 | 74.7 |
| Claude Haiku 4.5 | 85 | 62.8 | 73.9 |
| Gemini 2.5 Pro | 85 | 61.8 | 73.4 |
| Codestral | 85 | 61.3 | 73.2 |
| DeepSeek V4 Flash | 85 | 60.6 | 72.8 |
| Gemini 3 Flash | 85 | 57.8 | 71.4 |
| GPT-5.4 | 75 | 65.0 | 70.0 |

**P2-Spanne:** 57.8 – 70.3 (12.5 Punkte Spread — gute Diskriminierung)  
**Sovereignty Gap:** −1.55 (local_sovereign leicht unter full_fleet)

---

## Bekannte Beobachtungen

- **tooluse002:** Modelle ohne tatsächlichen Seiten-Abruf reproduzieren Llama 4 / Llama 3.3 aus
  Trainings-Vorwissen statt der aktuellen HuggingFace-Seite (→ Keywords prüfen Llama 3.2, Vision, Guard)
- **GPT-5.4:** Parse-Fehler auf tooluse001 in einem Lauf (instabile Tool-Call-Formatierung)
- **Hermes 4 70B:** Halluzinierte auf tooluse002 GPT-2/BERT als Meta-Llama-Modelle → korrekt penalisiert

---

## Nächste Schritte

- [ ] Vollständiger Batch-Run (alle ~25 Tool-Use-Modelle nach Golden Standard v1.2.0)
- [ ] Sovereign-Fleet-Modelle nachziehen (lokale Ollama-Modelle ≥ 7B)
- [ ] Quartalsupdates der Golden Standards bei signifikanten Modell-Releases
