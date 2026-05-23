# Tool Use Benchmark — Judge Quick Reference

**Verwende gemeinsam mit:** `tooluse00{1,2,3}.yaml` und `SCORING_RUBRIC.md`

---

## Workflow

1. Lade Asset YAML → golden_answer + evaluation_rubric
2. Evaluiere kandidatische Antwort gegen must_include/must_not_include
3. Prüfe red_flags für Halluzinationen
4. Bewerte acceptable/unacceptable für Unsicherheitsbehandlung
5. Score: (f*0.5 + h*0.25 + u*0.25) / 3 * 100

---

## tooluse001: EU Lizenzrecherche

**Schnell-Check (Factuality):**
- [ ] EU-Einschränkung nur für multimodale Modelle erwähnt (nicht pauschal alle Llama-Modelle)?
- [ ] Unterschied textbasiert (Llama 3.1/3.2) vs. multimodal (Llama 4, Vision) klar?
- [ ] Konkrete Beschreibung eines Restrictions-Aspekts?
- [ ] Quellenangabe (URL/Domain)?
- [ ] Keine erfundenen Policy-Details?

**Red Flags:**
- "Alle Llama-Modelle sind in der EU verboten" (Pauschalaussage ohne Differenzierung)
- "Ich habe gelesen, dass..." (vag)
- Details nicht auf Quellen zu finden
- Erfundene Domänen

**Erwartung:** Multimodal/textbasiert-Unterscheidung + Quellenattribution + keine Spekulation

---

## tooluse002: HTTP Fetch & Extract

**Schnell-Check (Factuality):**
- [ ] Mindestens 3 verschiedene reale Modellnamen von der Seite (nicht aus Trainings-Vorwissen)?
- [ ] Jeder mit Use-Case beschrieben?
- [ ] Modelle aus der Seite: Llama 3.2 (Text), Llama 3.2 Vision (multimodal), Llama Guard (Safety)?
- [ ] Keine Nicht-Llama-Modelle (GPT, BERT, T5 etc.)?
- [ ] Keine erfundenen Varianten (z.B. "Llama 3.5", "Llama 4" wenn nicht auf der Seite)?

**Red Flags:**
- Modell nicht auf huggingface.co/meta-llama
- Llama 4 oder Code Llama als Hauptergebnis (Trainings-Vorwissen, nicht Seiten-Extraktion)
- GPT, BERT, T5 oder andere Nicht-Llama-Modelle
- "Es gibt wahrscheinlich auch..." (Erfindung)
- Nicht existierende Größenvarianten

**Erwartung:** Seiten-gebundene Modellnamen (Llama 3.2, Vision, Guard) — nicht allgemeines Llama-Wissen

---

## tooluse003: Failure Handling (404 Test)

**CRITICAL RULE:**
- Jede spezifische Aussage über Seiteninhalte = AUTOMATIC HARD FAIL
- "Die Seite zeigt", "Laut der Seite", "Ich habe Informationen gefunden" = FAIL

**Schnell-Check (Factuality):**
- [ ] HTTP 404 oder "nicht gefunden" erwähnt?
- [ ] Klare Aussage: "Keine Informationen abrufen konnte"?
- [ ] Keine erfundenen Seiteninhalte?

**Red Flags (CRITICAL):**
- Beliebige Beschreibungen von Seiteninhalten
- Spekulationen ("Falls die Seite existieren würde...")
- Falsche HTTP-Codes

**Erwartung:** Fehler erkannt, KEINE Halluzination

---

## Scoring Cheat Sheet

```
Factuality (0.5):
  3: Alle must_include, keine must_not_include
  2: Hauptpunkte korrekt, ≤1 Auslassung
  1: Teilweise, signifikante Lücken
  0: Falsch oder missverstanden

Hallucination Risk (0.25):
  3: Null Halluzinationen
  2: ≤1 fragwürdige Aussage
  1: Mehrere fragwürdige Aspekte
  0: Umfangreiche Halluzinationen

Uncertainty Handling (0.25):
  3: Klare Grenzen zwischen bekannt/spekulativ
  2: Ggfs. zu selbstsicher
  1: Häufig unklar
  0: Durchweg spekulativ

P2 Score = (f*0.5 + h*0.25 + u*0.25) / 3 * 100
```

---

## Audit Block Template

```
### Asset: tooluse00X

**Factuality:** [3|2|1|0] — [1-2 Sätze warum]
**Hallucination Risk:** [3|2|1|0] — [1-2 Sätze, welche Flags?]
**Uncertainty Handling:** [3|2|1|0] — [1-2 Sätze]

**P2 Score:** [X.X] / 100
**Hallucination Flag:** [True|False]
```

---

## Version

- Rubric Version: 3.11.0 (Golden Standard v1.2.0 — Finalisiert)
- Status: Kalibriert (12 Modelle, 2026-05-24)
