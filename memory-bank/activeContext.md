# Active Context

## Aktueller Stand
- Neue Modelle von Google (Gemini 2.5/3.0 Preview) und xAI (Grok 3/4) in die `benchmark_config.yaml` integriert und im Pricing-Updater verknüpft.
- Ein fälschlicher 0-Punkte Bug im `reasoning_logic` Modul für lokale reasoning-Modelle (Zerstörung der Antwort durch `implicit_separator` Cutoff) wurde in `evaluators.py` behoben.
- Sämtliche Konfigurationsänderungen sowie Bugfixes wurden fehlerfrei im Repository committet.

## Nächster logischer Schritt
- Neu-Evaluation des Moduls `reasoning_logic` für betroffene Modelle durchführen, damit die Scores im Leaderboard durch den reparierten Parser aktualisiert werden.

## Offene Fragen oder Risiken
- Bei Modellen, die ihr Output-Limit überschreiten (wie Trinity in `metacog_005`), resultieren unvollständige JSON/Prozentausgaben zu Recht in 0 Punkten; potenzielles Risiko für unzureichend konfigurierte Max-Token bei lokalen Runs.