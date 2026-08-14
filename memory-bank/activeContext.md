# Active Context
Aktueller Stand und nächste Schritte.

- **Abgeschlossen:** probe_thinking.py Fallback von `ollama` → `openrouter` mit `deepseek/deepseek-v4-flash` als Fallback-Modell. Hardcoded-Konstanten entfernt, Werte aus `benchmark_config.yaml:probe_thinking` gelesen (Config-Driven). Model-Card `nvidia/nemotron-3.5-lightning` korrigiert: `model_id` mit Slash für OpenRouter-Erkennung. Thinking-Probe erfolgreich (detected=true, confidence=medium).
- **Nächster Schritt:** `make benchmark-auto MODEL=nvidia/nemotron-3.5-lightning` für ersten Benchmark-Run
- **Offen/Risiko:** `params_total_b` / `params_active_b` unbekannt (null) — muss nach Recherche oder erstem Run gefüllt werden. Card bleibt `card_status: draft` bis `profile_verified: true`.