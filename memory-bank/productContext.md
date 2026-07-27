# Product Context

## Warum CrucibleMark?

LLMs werden schnell und zahlreich — es gibt kaum unabhængiges, reproduzierbares Testing, das Modell-Vergleiche auf standardisierten Aufgaben erlaubt. Bestehende Benchmarks (MMLU, HumanEval) sind statisch und werden oft "gelöst" — bei jedem neuen Release sind sie sofort überholt.

CrucibleMark geht einen anderen Weg: Es bewertet Modelle anhand von Aufgaben, die echte kognitive Anforderungen stellen (Code-Qualität, UXWriting, Politische Kompass-Analyse, Tool-Use). Die Bewertungen erfolgen blind durch einen unabhängigen LLM-Judge, der den zu testenden Modellnamen nicht kennt.

## Design-Philosophie

1. **Faire Vergleichbarkeit:** Sequentielle Modell-Abarbeitung, kein "warmer Cache"-Vorteil. Jede Bewertung ist ein frischer API-Call.
2. **Blind-Evaluierung:** Der Judge kennt den Modellnamen NICHT — verhindert Bias durch Markenwahrnehmung.
3. **Transparenz:** Full-Audit-Logs pro Task, pro Modell, mit Raw API-Response, Tokens, Reasoning-Content.
4. **Wiederholbarkeit:** Jede Config, jede Task, jeder Run kann reproduziert werden — CSV-Write-Through schützt vor Datenverlust.
5. **Extensibility:** Neue Benchmark-Module als Plugins, neue Provider als Connector-Klassen, neue Cards via Card-Research.
6. **Cost-Bewusstsein:** Token-Budgets, Pricing-Daten, Reasoning-Tokens-Tracking — der Nutzer sieht immer den CO2/Cost-Aufwand.

## Kernnutzer

- **Selbstnutzer (Single-User-Kontext):** Der Autor testet Modelle vor Einsatz in eigenen Projekten und vergleicht sie.
- **Community (Web-Export):** Geführte Leaderboards als Entscheidungsgrundlage für Andere.
- **Forschung:** Reproduzierbare Benchmark-Ergebnisse fuer akademische Vergleiche.

## Nutzer-Story (gekürzt)

"In einer Welt, in der Model-Provider ihre eigenen Scores veröffentlichen und Benchmarks schnell obsolet werden: Wer liefert die Wahrheit?"
→ CrucibleMark: Unabhängige, auditierte, reproduzierbare LLM-Bewertung — blind durch einen Judge.
