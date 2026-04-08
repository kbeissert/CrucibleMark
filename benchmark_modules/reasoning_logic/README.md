# Reasoning & Logic

> Bewertet, ob ein LLM wirklich denkt — oder nur plausibel klingt. Das Modul
> prüft 11 Szenarien in drei Schwierigkeitsstufen: von klassischen Logik-Rätseln
> über mehrstufige Kausalanalysen bis zu Metakognitions-Tests, in denen das
> Modell seine eigene Unsicherheit korrekt einschätzen muss.

**Modul-ID:** `reasoning` (Leaderboard) | **Klasse:** `ReasoningLogicTest` | **Version:** 2.2.0
**Assets:** 11 | **Sprache:** Deutsch (Tier 3 erzwungen) | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

Das entscheidende Designmerkmal: **Einige Aufgaben haben keine lösbare Antwort.**
Ein Modell, dem man 3 einstündige Meetings in ein 2-Stunden-Fenster legen lassen
will, muss die Unmöglichkeit erkennen und klar kommunizieren — nicht kreativ
ausweichen oder eine falsche Lösung konstruieren. Dasselbe gilt für zirkuläre
Abhängigkeiten. Modelle, die bei unmöglichen Aufgaben Lösungen behaupten, werden
massiv abgestraft (Feasibility-Penalty).

Das Modul implementiert Anti-Ceiling-Maßnahmen: Oberflächliche Antworten, die
korrekt klingen aber keine echte Analyse enthalten, erzielen maximal 60 % —
der Rest erfordert explizites Chain-of-Thought-Reasoning.

---

## Scoring-Methodik

Standard-Fallback: `regex: 0.20 / judge: 0.80`. Asset 5A verwendet `0.30/0.70`.
Score-Contribution: `routine: 0.0 / reasoning: 1.0` (alle Assets).

Der **Reasoning Complexity Index (RCI)** als Leaderboard-Metrik:

```
RCI = (Durchschnitt Tier 1+2 × 0,6) + (Durchschnitt Tier 3 × 0,4)
```

| RCI-Wert | Klassifikation |
|---|---|
| < 50 % | Non-Thinking Model |
| 50–85 % | Thinking Model |
| > 85 % | Deep Thinking Model |

**Feasibility-Extraktion** (Assets 5C, 5D): Automatischer O(n)-Single-Pass-Regex
über 12+ Muster erkennt, ob das Modell die Unmöglichkeit korrekt kommuniziert.
Schwellenwert: Feasibility-Score < 3.0 → Unmöglichkeit erkannt.
Penalty-Multiplikator: Score × 0,3 wenn Unmöglichkeit nicht erkannt.

---

## Test Assets

### TIER 1 — Deduktives Schließen

#### `reasoning_001_river` — River Crossing Puzzle
```
Typ:       Klassisches Constraint-Satisfaction-Rätsel
Prompt:    Bauer muss Wolf, Ziege und Kohl über einen Fluss transportieren.
           Boot fasst nur Bauer + 1 weiteres. Wolf frisst Ziege, Ziege frisst Kohl.
Erwartete Antwort:
  - Vollständige Lösung in 7 Schritten
  - Explizite Begründung für jeden Schritt
  - Chain-of-Thought sichtbar (nicht nur Ergebnis)
Scoring:   regex: 0.10 / judge: 0.90 — Lösungsweg, nicht nur Resultat
```

---

### TIER 2 — Operationales Schließen (5A–5E)

#### `reasoning_5a_001` — Code Logic Debugging
```
Typ:       Bug-Identifikation in Python-Code (Endlosschleife)
Prompt:    Python-Funktion mit verstecktem Loop-Bug wird gezeigt.
Erwartete Antwort:
  - Genaue Identifikation der fehlerhaften Zeile
  - Kausalerklärung: Warum entsteht die Endlosschleife in diesem Kontext?
  - Konkreter Fix mit Begründung
Scoring:   regex: 0.30 / judge: 0.70 (hoher Regex-Anteil: Bug-Zeile per Keyword prüfbar)
```

#### `reasoning_5b_001` — Root Cause Analysis
```
Typ:       Mehrstufige technische Diagnose
Prompt:    Dashboard lädt 5–10 Sekunden. Gegebene Datenpunkte:
           API antwortet in 20ms / DB-CPU bei 99–100% / Netzwerklatenz normal.
Erwartete Antwort:
  - Korrekte Identifikation der Root Cause (DB, nicht API, nicht Netzwerk)
  - Logische Ausschlusskette ("API ist schnell, also liegt es nicht am Code...")
  - Lösungsvorschläge (Caching, Query-Optimierung, Indexierung)
Scoring:   Chain-of-Thought-Qualität bewertet; Ergebnis allein reicht nicht
```

#### `reasoning_5c_001` — The Scheduling Paradox ⚠️ Unmöglich
```
Typ:       Constraint Satisfaction — absichtlich unmöglich
Prompt:    "Schedule 3 meetings of 1h each between 1:00 PM and 3:00 PM."
           (3h Bedarf, 2h Fenster — keine valide Lösung existiert)
Erwartete Antwort:
  - Explizit: "Das ist nicht möglich"
  - Mathematische Begründung: 3×1h > 2h verfügbares Fenster
  - KEIN kreativer Workaround (z. B. "30-Minuten-Slots") — wird abgestraft!
Feasibility-Extraktion:
  - Modell-Feasibility-Score wird per Regex extrahiert
  - Score < 3.0: Unmöglichkeit erkannt (+volle Punkte)
  - Score > 6.0: Modell behauptet Lösung (Penalty × 0.3)
```

#### `reasoning_5d_001` — Circular Dependency ⚠️ Unmöglich
```
Typ:       Dependency-Analyse — zirkulär und unlösbar
Prompt:    System mit zirkulären Abhängigkeiten (A→B→C→A),
           Frage: Wie kann man das auflösen?
Erwartete Antwort:
  - Erkennung der Zirkularität
  - Korrekte Klassifikation als architektonisches Problem, nicht operatives
  - Lösungsvorschlag muss strukturelle Änderung beinhalten (kein Runtime-Hack)
Feasibility-Extraktion: wie 5C — falsche Lösungsversprechen werden stark abgestraft
```

#### `reasoning_5e_001` — Nested Paradox
```
Typ:       CAP-Theorem-ähnliche Trade-off-Analyse
Prompt:    Dreidimensionaler Widerspruch: System muss gleichzeitig
           konsistent, verfügbar UND partition-tolerant sein.
Erwartete Antwort:
  - Erkennung des Trade-offs (CAP-Theorem)
  - Argumentierte Priorisierung (keine universell richtige Antwort möglich)
  - Tiefe der Argumentation ist Scoring-Dimension
Scoring-Dimensionen: Analyse-Tiefe (33%) + Lösungsqualität (33%) + Argumentationstiefe (33%)
```

---

### TIER 3 — Metakognition (Tier-3-Assets)

*Alle Tier-3-Assets erzwingen `language: de`.
 Antwort-Format: `<thought>` Chain-of-Thought sichtbar, dann finale Antwort.*

#### `reasoning_metacog_001` — The Sheep Trap
```
Prompt:    "A farmer has 17 sheep. All but 9 die. How many sheep are left?"
Trap:      "All but 9" löst Instinkt-Antwort 17-9=8 aus.
           Korrekte Antwort: 9 (die 9 überleben).
Erwartete Antwort:
  - <thought>: Initiale Berechnung 17-9=8, dann Selbstkorrektur
  - Finale Antwort: 9
Scoring:   Selbstkorrektur-Keywords in <thought> gesucht:
           "wait", "actually", "correction", "mistake"
```

#### `reasoning_metacog_002` — Green Sky Premise
```
Prompt:    Aufgabe mit einer falsch formulierten Prämisse als Ausgangslage.
           ("Der Himmel ist grün. Was folgt logisch daraus?")
Erwartete Antwort:
  - Prämisse anfechten statt akzeptieren
  - Erklären, warum die Prämisse falsch ist
  - Nicht einfach logisch weiterrechnen auf Basis einer Falschannahme
Scoring:   Ground-Truth-Datensatz aus YAML geladen
```

#### `reasoning_metacog_003` — The Two Doors
```
Typ:       Ambiguität erkennen und mehrere Interpretationen ausarbeiten
Prompt:    Mehrdeutiges Szenario, das mehrere valide Lösungsansätze hat.
Erwartete Antwort:
  - Mindestens 2 valide Interpretationen explizit ausgearbeitet
  - Keine willkürliche Auswahl einer einzelnen Interpretation
Scoring:   Anzahl und Qualität der ausgearbeiteten Interpretationen
```

#### `reasoning_metacog_004` — The Monty Hall Problem
```
Typ:       Iterative Verfeinerung nach Feedback
Ablauf:    Modell gibt erste Antwort → erhält korrigierendes Feedback →
           muss Position neu bewerten
Erwartete Antwort:
  - Robustheit gegen korrektes Feedback: Position wird revidiert
  - Keine sture Beibehaltung einer falschen Antwort
Scoring:   Positionsänderung nach Feedback + mathematische Korrektheit
```

#### `reasoning_metacog_005` — The Birthday Paradox
```
Typ:       Uncertainty Calibration (statistische Schätzung)
Prompt:    Statistische Frage mit kontraintuitiver Antwort.
           (In einer Gruppe von 23 Personen: Wahrscheinlichkeit gemeinsamer Geburtstag?)
Erwartete Antwort:
  - Kalibriertes Konfidenz-Level: weder überconfident noch unnötig vage
  - Korrekte Schätzung (~50%) mit Begründung
  - Kommuniziert Unsicherheit angemessen
Scoring:   Mathematische Korrektheit (Annäherung) + Kalibrierung des Konfidenz-Levels
```

---

## Technischer Aufbau

Strukturen in `core/`:

| Datei | Zuständig für |
|---|---|
| `evaluators.py` | Facade: Dispatch auf Tier-Scorer |
| `scorers/standard.py` | Tier 0/1 |
| `scorers/tier1_physics.py` | Asset 5C (impossible task) |
| `scorers/tier2_systems.py` | Assets 5B, 5D |
| `scorers/tier2_expert.py` | Asset 5E |
| `scorers/tier3/metacog_00[1-5].py` | Je ein Tier-3-Asset |
| `robust_metrics.py` | Feasibility-Extraktion (12+ Regex-Patterns) |
| `validation_dataset.py` | Ground-Truth YAML für metacog 001/002 |
| `constants/thresholds.py` | Alle Schwellenwerte |

---

## Konfiguration

```yaml
# config.yaml (Auszug)
metadata:
  id: "reasoning"    # Leaderboard-ID (nicht "reasoning_logic"!)

scoring:
  fallback_weights:
    regex: 0.20
    judge: 0.80

integration:
  leaderboard:
    default_contribution:
      routine: 0.0
      reasoning: 1.0
```

```python
# core/constants/thresholds.py (Auszug)
FEASIBILITY_IMPOSSIBLE_THRESHOLD = 3.0    # Unter diesem Score: Unmöglichkeit erkannt
FEASIBILITY_PENALTY_MULTIPLIER = 0.3      # Score × 0.3 wenn Unmöglichkeit nicht erkannt
RCI_TIER3_WEIGHT = 0.4                    # Tier-3-Gewichtung im RCI
```

---

## Token-Budget

**Kein Token-Budget** — `reasoning_logic` ist bewusst von `token_budgets` in `benchmark_config.yaml` ausgenommen (Eintrag `null` / nicht gesetzt). Reasoning-Module können systembedingt längere Intermediate-Thought-Chains produzieren; ein hartes Output-Limit würde diese Fähigkeit verfälschen und das Modul gegenüber Modellen mit kurzen, direkt-assertiven Antworten benachteiligen.
