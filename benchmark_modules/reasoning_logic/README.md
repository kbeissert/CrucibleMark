# Reasoning Logic Module

> **Technical Metadata**
> - **ID:** `reasoning_logic`
> - **Namespace:** `benchmark_modules.reasoning_logic`
> - **Class:** `ReasoningLogicTest`
> - **Evaluator:** `ReasoningEvaluator` (Facade + Strategy Pattern)
> - **Version:** v2.0.0 (Tiered Architecture + Metacognition)
> - **Type:** Cognitive, Logic Processing, Metacognition

## 🔍 Module Overview

Dieses Modul testet die kognitive Leistungsfähigkeit von LLMs in verschiedenen Tiefen (Tiers). Es reicht von einfachen Logik-Checks bis hin zur **Metakognition** (das Überdenken des eigenen Denkprozesses).

Besonders für Reasoning-Modelle (wie DeepSeek R1) analysiert das Modul nicht nur das Ergebnis, sondern auch den Inhalt der `<thought>` Tags, um echte Denkprozesse von "Lucky Guesses" zu unterscheiden.

---

## 🏗 Architecture & Tiers

Das Modul ist in **Tiers (Stufen)** unterteilt, um verschiedene kognitive Fähigkeiten zu prüfen.

### **Tier 0: Sanity Check**
*   **Fokus:** Grundlegende Logik und Instruktionsbefolgung.
*   **Beispiel:** River Crossing Puzzle.
*   **Ziel:** Filtern von Modellen, die bereits an einfachsten Aufgaben scheitern.

### **Tier 1: Operational Logic (Physics)**
*   **Fokus:** Kausale Zusammenhänge und physikalische Paradoxien.
*   **Beispiel:** Paradoxien Auflösung.

### **Tier 2: Deep Reasoning (Systems)**
*   **Fokus:** Komplexe Systeme, Deadlocks und Multi-Step Logic.
*   **Assets:** 5A-5D (z.B. Deadlock-Erkennung, System-Invarianz).

### **Tier 3: Metacognition (Self-Reflection) ⭐ NEU**
*   **Fokus:** Die Fähigkeit des Modells, eigene Fehler zu erkennen und Prämissen zu hinterfragen.
*   **Assets:** `METACOG_001` bis `METACOG_005`.
*   **Besonderheit:** Berechnet den **RCI (Reasoning Complexity Index)**.

---

## 🧪 Scoring Logic & Metacognition Methodology (v2.0)

Für Tier 3 (Metacognition) nutzt das Modul nun **Hybride Robuste Metriken**, um "echtes" Denken von Simulation zu unterscheiden.

### 1. Robust Self-Correction ("The Sheep Trap")
Wir prüfen, ob das Modell einen anfänglichen Fehler *im Denkprozess* korrigiert. Die Erkennung erfolgt auf 3 Ebenen:
1.  **Keywords:** Suche nach Signalen wie _"wait, let me reconsider"_, _"initially I thought"_.
2.  **Struktur:** Analyse des Argumentationsflusses (These -> Antithese -> Synthese).
3.  **Trajektorie:** Das Modell muss von einer falschen Annahme zu einer richtigen Schlussfolgerung wechseln.

### 2. Premise Challenge ("The Green Sky")
Wir erzwingen eine explizite Ablehnung falscher Prämissen.
*   **Anforderung:** Das Modell muss erkennen, dass die Frage ("Warum ist der Himmel grün?") auf einer Lüge basiert.
*   **Erkennung:** Flexible Suche nach Konzepten wie "false premise", "incorrect assumption" oder "wrong setup".

### 3. RCI (Reasoning Complexity Index)
Der RCI ist eine Kennzahl (0-100%), die angibt, wie "tief" das Modell denkt.
*   Formel: `RCI = (Avg_Tier1_2_Score * 0.6) + (Avg_Tier3_Score * 0.4)`
*   **Klassifizierung:**
    *   `< 50%`: Non-Thinking Model (z.B. Dolphin 8B Baseline ~42%)
    *   `50-70%`: Basic Thinking Model (z.B. Qwen 2.5 ~65%)
    *   `> 85%`: Deep Thinking Model (z.B. DeepSeek R1 ~87%)

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
python run_benchmark.py --module reasoning --provider local --model qwen2.5-coder:14b

# Nur Metacognition Tier 3 testen (Quick Mode)
python scripts/test_reasoning_metacog.py --model dolphin:latest --quick
```

### Option 3: Developer Tests
```bash
# Reproduzierbarkeit & Ground Truth prüfen
python benchmark_modules/reasoning_logic/tests/test_reproducibility.py

# Scoring-Regeln und Tags testen
python benchmark_modules/reasoning_logic/tests/test_tags.py
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
