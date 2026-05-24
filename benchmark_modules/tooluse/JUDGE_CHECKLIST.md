# Tool Use Benchmark — Judge Quick Reference

**Verwende gemeinsam mit:** `tooluse00{1,2,3,4,5}.yaml` und `SCORING_RUBRIC.md`

---

## Workflow

1. Lade Asset YAML → golden_answer + evaluation_rubric
2. Evaluiere kandidatische Antwort gegen must_include/must_not_include
3. Prüfe red_flags für Halluzinationen
4. Bewerte acceptable/unacceptable für Unsicherheitsbehandlung
5. Score: (f*0.5 + h*0.25 + u*0.25) / 3 * 100

---

## tooluse001: EU Lizenzrecherche

> **Phase B — Tool Synthesis:** URL vorgegeben. Bewertet: liest das Modell, was auf der Seite steht, oder antwortet es aus Parameterwissen?

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

> **Phase B — Tool Synthesis:** URL vorgegeben. Bewertet: extrahiert das Modell ausschließlich die Fakten aus dem Seiten-Inhalt?

**Schnell-Check (Factuality):**
- [ ] Mindestens 3 verschiedene reale Modellnamen von der Seite (nicht aus Trainings-Vorwissen)?
- [ ] Jeder mit Use-Case beschrieben?
- [ ] Llama 4 Scout/Maverick als aktuelle Hauptfamilie erwähnt?
- [ ] Llama Guard oder Llama 3.x als weitere Familien referenziert?
- [ ] Keine Nicht-Llama-Modelle (GPT, BERT, T5 etc.)?
- [ ] Keine erfundenen Varianten?

**Red Flags:**
- Modell nicht auf huggingface.co/meta-llama
- GPT, BERT, T5 oder andere Nicht-Llama-Modelle (Hermes-Fehler-Typ)
- Code Llama als Hauptergebnis ohne weitere Modelle (veraltetes Trainings-Vorwissen)
- "Es gibt wahrscheinlich auch..." (Erfindung)
- Nicht existierende Größenvarianten

**Erwartung:** Seiten-gebundene Modellnamen — Llama 4 Scout/Maverick prominent, Guard und Llama 3.x als weitere Familien (Golden Standard v1.3.0)

---

## tooluse003: Failure Handling (404 Test)

> **Phase B — Tool Synthesis:** URL vorgegeben (404). Bewertet: kommuniziert das Modell den Fehler ehrlich ohne Halluzination?

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

## tooluse004: Tool Selection (web_search)

> **Phase A — Tool Intelligence:** Keine URL vorgegeben. Bewertet: wählt das Modell `web_search` für eine Recherche-Aufgabe?

**P1-Prüfung (automatisch — kein Judge-Input nötig):**
- `web_search` aufgerufen → P1=100 ✅
- `http_fetch` aufgerufen → P1=0 ❌
- Kein Tool → P1=0 ❌

**Schnell-Check (Factuality — nur wenn P1=100):**
- [ ] Bezug auf mindestens ein Ergebnis aus dem Tool-Call (HuggingFace, Llama oder OpenAI Evals)?
- [ ] Keine Benchmark-Scores oder Modell-Rankings behauptet, die nicht aus dem Tool-Ergebnis stammen?
- [ ] Antwort synthetisiert Suchergebnisse statt Parameterwissen?

**Red Flags:**
- Spezifische MMLU- oder HELM-Scores ohne Tool-Basis
- Konkrete Modell-Versionen oder Leaderboard-Platzierungen ohne Quellenreferenz
- Antwort ignoriert die abgerufenen Ergebnisse vollständig (State B2 → cap_B2=35)

**Hinweis:** Mock liefert HuggingFace-Leaderboard, Llama und OpenAI Evals — kein EU AI Act-Content. State B2 (parametrische Antwort über LLM-Rankings ohne Tool-Basis) ist das häufigste schwache Muster.

**Erwartung:** Tool korrekt gewählt + Synthese aus den Suchergebnissen

---

## tooluse005: URL Construction (http_fetch)

> **Phase A — Tool Intelligence:** Keine URL vorgegeben. Bewertet: leitet das Modell die korrekte Wikipedia-URL aus eigenem Wissen ab?

**P1-Prüfung (automatisch — kein Judge-Input nötig):**
- `http_fetch` mit `en.wikipedia.org/wiki/Python_(programming_language)` → P1=100 ✅
- `http_fetch` mit anderer Wikipedia-URL (z.B. `/wiki/Python`) → P1=80 ⚠
- `http_fetch` mit nicht-whitegelisteter Domain (z.B. `python.org`) → P1=0 ❌
- `web_search` aufgerufen → P1=0 (falscher Typ) ❌
- Kein Tool → P1=0 ❌

**Schnell-Check (Factuality — nur wenn P1 > 0):**
- [ ] Python als hochniveauige, generell einsetzbare Sprache beschrieben?
- [ ] Mindestens zwei Einsatzbereiche genannt (z.B. Data Science, Web, KI)?
- [ ] Guido van Rossum oder Erscheinungsjahr 1991 korrekt?
- [ ] Keine spezifischen Python-Features behauptet, die nicht im abgerufenen Artikel stehen?

**Red Flags:**
- Python-Syntax-Beispiele als Erklärung ohne Artikel-Grundlage
- Falsches Erscheinungsjahr (1991 ist korrekt)
- Behauptungen über Performance oder Benchmarks ohne Tool-Basis
- Antwort ausschließlich aus Parameterwissen ohne Artikel-Referenz (State B2)

**Erwartung:** Korrekte URL konstruiert + Antwort aus dem abgerufenen Artikel-Inhalt

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

- Rubric Version: 3.12.0 (5 Assets — Phase A + Phase B)
- Phase B kalibriert: Golden Standard v1.3.0 (tooluse001–003, 2026-05-24)
- Phase A Kalibrierung ausstehend: tooluse004/005 (Calibration Run geplant)
