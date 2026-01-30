# CrucibleMark Module: Logical Reasoning (v2.2)

> **Technical Metadata**
> - **ID:** `reasoning_logic`
> - **Namespace:** `benchmark_modules.reasoning_logic`
> - **Class:** `ReasoningLogicTest`
> - **Evaluator:** `ReasoningEvaluator` (Facade + Strategy Pattern)
> - **Version:** v2.2.0 (Anti-Ceiling Measures)
> - **Type:** Cognitive, Logic Processing, Metacognition

## 🔍 Module Overview

Das **Logical Reasoning** Modul ist eines der anspruchsvollsten Testfelder in CrucibleMark. Es evaluiert die Fähigkeit von LLMs, logische Schlüsse zu ziehen, Fehlschlüsse zu erkennen und komplexe Denkmuster (Reasoning Chains) aufzubauen.

In Version 2.2 liegt der Fokus auf **Anti-Ceiling Measures**: Durch gehärtete Physics-Traps, Deadlock-Erkennung und mehrdimensionale Paradoxien wird die Unterscheidbarkeit der Top-Tier Modelle drastisch erhöht.

---

## 🎯 Fokus & Ziele (v2.2)

1.  **Eliminierung des Ceiling Effects**:
    *   Verhinderung von 100% Scores für Modelle, die nur "Ja-Sager" spielen oder Heuristiken folgen, ohne das Problem tief zu durchdringen.
2.  **Feasibility Awareness**:
    *   KI muss erkennen, wenn eine Aufgabe **unmöglich** oder **widersprüchlich** ist.
    *   Optimistische Antworten ("I can do this...") werden bei Paradoxien rigoros bestraft (0-15%).
3.  **Tiered Evaluation**:
    *   Von einfacher Deduktion (Tier 1) bis hin zu abstrakten Metakognitions-Tests (Tier 3).

---

## 🏗 Struktur & Assets

Das Modul besteht aus 11 Assets, unterteilt in drei Tiers:

### 🔹 Tier 1: Operational Logic (Deduktion)
*Prüft grundlegende logische Operationen und Faktenprüfung.*

*   **Logic 001 - River Crossing**: Klassisches Logik-Rätsel mit Variation.
*   **Logic 5C - Physics Trap (Härter in v2.2)**:
    *   *Szenario*: "Transportiere Mount Everest in eine Standard-Box."
    *   *Erwartung*: **Refusal** ("Impossible").
    *   *Technik*: **Bidirektionale Negations-Erkennung**. Unterscheidet zuverlässig zwischen echten Workarounds (prohibited) und dem Zitieren von Regeln ("no machinery allowed" penalty-free).
    *   *Hardening*: Keine Teilpunkte mehr für "kreative Workarounds" (Schrumpfstrahl, Metaphern). Nur klare Ablehnung zählt.

### 🔹 Tier 2: Systems Thinking (Analyse)
*Prüft das Verständnis komplexer Zusammenhänge und Abhängigkeiten in Systemen.*

*   **Logic 5A - Error Recovery**: Debugging von Code-Logik.
*   **Logic 5B - Complex Chains**: Multi-Step Reasoning.
*   **Logic 5D - Deadlock Detection (Härter in v2.2)**:
    *   *Szenario*: Zirkuläre Abhängigkeiten in Projektplänen (A braucht B braucht C braucht A).
    *   *Erwartung*: Erkenntnis: "Deadlock" / "Unsolvable". Feasibility Assessment: 0/10.
    *   *Hardening*: Regex-gestützte Feasibility-Extraction. Wer 0 sagt, gewinnt. Wer Lösungen vorschlägt, verliert.
*   **Logic 5E - Expert Paradox (Neu in v2.2)**:
    *   *Szenario*: Distributed Transaction Manager mit 3 widersprüchlichen Constraints (CAP-Theorem Style).
    *   *Erwartung*: Erkenntnis des Trade-Offs.
    *   *Scoring*: 3-Dimension-Score (Analysis, Solution Quality, Depth). Bestraft Optimismus.

### 🔹 Tier 3: Metacognition (Selbstreflexion)
*Prüft die Fähigkeit des Modells, eigene Annahmen zu hinterfragen.*

*   **Metacog 001-005**:
    *   Erkennen von Fangfragen ("The Green Sky").
    *   Selbstkorrektur bei falschen Prämissen.
    *   Vermeidung von Halluzinationen bei Fake-Facts.

---

## 📊 Scoring & Metriken

### Reasoning Complexity Index (RCI)
Der **RCI** misst die Tiefe des Denkprozesses.
*   **Formel**: `(Avg_Tier1_2 * 0.6) + (Avg_Tier3 * 0.4)`
*   **Klassen**:
    *   `< 50%`: Non-Thinking Model
    *   `50-85%`: Thinking Model
    *   `> 85%`: Deep Thinking Model

### Feasibility Extraction (Neu in v2.2)
Das System extrahiert automatisch die Selbsteinschätzung des Modells ("Feasibility: 2/10").
*   Wenn `Feasibility > Threshold` bei Fallen → **Massiver Punktabzug**.
*   Verhindert, dass halluzinierte "Lösungen" für unlösbare Probleme Punkte erhalten.

---

## 🚀 How to Run

### Option 1: Interaktiv (Empfohlen)
```bash
python run_benchmark.py
# Wähle "reasoning" -> "local" -> Modell
```

### Option 2: CLI (Schnell)
```bash
# Alles testen
python run_benchmark.py --benchmark "Logical Reasoning" --model gemma2:9b
```

---

## 📂 Assets Structure

*   `assets/reasoning_001_river.yaml` (Tier 0: Sanity)
*   `assets/reasoning_5*.yaml` (Tier 1 & 2: Systems & Physics)
*   `assets/reasoning_metacog_001.yaml` (Self-Correction)
*   `assets/reasoning_metacog_002.yaml` (Premise Challenge)
*   `assets/reasoning_metacog_003.yaml` (Alternatives)
*   `assets/reasoning_metacog_004.yaml` (Iterative Refinement)
*   `assets/reasoning_metacog_005.yaml` (Confidence Calibration)
