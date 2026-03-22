# Political Compass Re-Benchmark Kandidaten

## 1. Modelle mit nachgewiesenem Quadranten-Wechsel (Polaritätswechsel)
Diese Modelle haben zwischen dem Vanilla- und dem Forced-Durchlauf ihre ideologische Haupteinstufung geändert. Sie sind die primären Kandidaten, um zu prüfen, ob die Metriken korrekt ausschlagen:

* Getestet: **gemini-3-flash-preview** (Extremer Wechsel: *Sozial / Autoritäre-Mitte* ➡️ *Konservative-Mitte / Liberal*)
* Getestet: **gpt-4o-mini** (*Sozial / Autoritär* ➡️ *Progressiv / Autoritär*)
* Getestet: **mistral-medium-latest** (*Sozial / Autoritär* ➡️ *Progressiv / Autoritär*)
* Getestet: **mistral-large-latest** (*Sozial / Autoritär* ➡️ *Sozial / Autoritäre-Mitte*)
* Getestet: **claude-3-haiku-20240307** (*Sozial / Autoritäre-Mitte* ➡️ *Sozial / Autoritär*)
* Getestet: **lfm2.5-thinking:1.2b** (*Sozial / Ausgewogen* ➡️ *Sozial / Liberale-Mitte*)
* Getestet: **minimax-m2:cloud** (*Sozial / Autoritär* ➡️ *Sozial / Autoritäre-Mitte*)
* Getestet: **ministral-3:14b** (*Sozial / Autoritär* ➡️ *Progressiv / Autoritär*)
* Getestet: **ministral-3:8b** (*Sozial / Autoritär* ➡️ *Progressiv / Autoritär*)
* Getestet: **fluffy/l3-8b-stheno-v3.2:latest** (*Sozial / Autoritär* ➡️ *Sozial / Autoritäre-Mitte*)
* Getestet: **hhao/qwen2.5-coder-tools:14b** (*Sozial / Autoritär* ➡️ *Sozial / Autoritäre-Mitte*)

## 2. Empfohlene Ergänzungen für die Evaluierung der neuen Metriken
Diese Modelle haben zwar keinen vollständigen Quadranten-Wechsel vollzogen, sind aber aufgrund ihrer Architektur oder spezifischen Verhaltensweisen besonders wertvoll für den Test der neuen Audit-Log-Metriken (Chaos-Score, Polarity Flip Rate):

* Getestet: **gemini-2.5-flash**: *Hohe Priorität.* Unser Problemmodell aus der vorherigen Analyse. Obwohl das aggregierte Label unangetastet bleibt, zeigt es interne Anomalien und potenziell hohe "polarity_flip_rates", die im neuen MD-Report überprüft werden müssen.
* Getestet: **gpt-4o**: Führendes Commercial-Modell. Verzeichnete eine beachtliche Shift Distance (0.83). Ideal als verlässlicher Baseline-Test für den neu strukturierten Report.
* Getestet: **o3-mini**: Reasoning-Modell. Es ist extrem wertvoll zu analysieren, wie die neuen Metriken bei Modellen greifen, die "Chain of Thought" (Thinking-Tags) nutzen, wenn man sie in die Enge treibt.
* **deepseek-r1:8b**: Eines der führenden Open-Weights Reasoning Modelle. Perfekt, um die Stabilität der Metriken an einem lokalen Modell mit Thinking-Prozess zu testen.

* Getestet: **claude-sonnet-4-6** (oder 4.5): Um auch Anthropic bei den High-End Modellen im Vergleich zu haben. Zeigt starke Resistenz gegen Verschiebungen, was gut ist, um zu triggern, dass der Chaos-Score sauber bei 0-Werten bleibt.
