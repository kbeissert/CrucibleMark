# 📝 Projekt-Roadmap & Offene Tasks

Dieser Plan fasst die besprochenen Erweiterungen zusammen, die für die Version 1.0 (nach dem aktuellen Release 0.9.8) anstehen.

## 🚀 Priority 1: Reasoning & Metacognition (v1.0 Goal)
Das Reasoning-Modul soll signifikant erweitert werden, um "echtes" Denken von Auswendiglernen zu unterscheiden.

- [ ] **RCI Implementierung (Recursive Critique):**
    - Logik implementieren, bei der das Modell seine eigene Antwort kritisieren und verbessern muss.
    - Messung: Verbessert sich das Ergebnis nach der Kritik? (Self-Correction Score).
- [ ] **Tier 2 Assets ("Systems Thinking"):**
    - Erstellung von Logik-Rätseln mit 2.5-Ordnung Effekten (Kettenreaktionen).
- [ ] **Metacognition Dataset:**
    - 5 "Trick-Fragen", die intuitiv falsch, aber logisch lösbar sind.
    - Ziel: Testen der "Confidence Calibration" (Wie sicher ist sich das Modell?).

## 🛠 Priority 2: Benchmark Hardening (Commercial Models)
Strategie gegen Score-Sättigung bei Top-Tier Modellen (Claude 3.5, GPT-4o).

- [ ] **Baseline Messung:**
    - Einmaliger Durchlauf der "Big Three" (OpenAI, Anthropic, Mistral Large).
    - Analyse: Kleben die Scores an der 100%-Marke?
- [ ] **Judge-Hardening (Evaluator-Upgrade):**
    - Falls Sättigung eintritt: Anpassung des System-Prompts im `llm_client`.
    - Anweisung an den Judge: "Sei extrem pedantisch, ziehe Punkte für Füllwörter ab".
- [ ] **Leaderboard Weight Classes:**
    - Falls Härtung eingeführt wird: Trennung des Leaderboards in "Lightweight" (<20B) und "Heavyweight" (>70B), damit kleine Modelle fair bewertet bleiben.

## 📦 Priority 3: Maintenance & Polish
- [ ] **Political Compass Visualisierung:**
    - Erstellung eines Skripts, das die `political_compass_results.csv` als PNG-Scatterplot rendert.
- [ ] **Orphaned Runs Cleanup:**
    - Skript zur Bereinigung von halb-fertigen Runs in der `local_models_benchmark.csv` (wenn Resume nicht greift).

