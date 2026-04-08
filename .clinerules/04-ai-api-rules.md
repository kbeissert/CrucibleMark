# AI & API — Allgemeine Regeln

## Security (absolut)
- API Keys NIEMALS in Code, Logs, Kommentaren oder Git — ausschließlich .env
- .env in .gitignore — vor jedem Commit prüfen
- Keine API-Calls in Tests gegen Live-Endpoints — Mocks verwenden

## Datenschutz
- Für datenschutzsensible Tasks: europäische oder lokale Modelle bevorzugen
- OpenAI/Anthropic nur für nicht-sensible Daten
- Lokale Modelle via Ollama/Jan AI für alle internen/vertraulichen Inhalte

## API-Effizienz
- Prompt Caching nutzen wo möglich (Anthropic: cache_control)
- Haiku für Klassifikation/Routing, Sonnet für Reasoning
- Fehlerbehandlung + Retry mit Backoff bei allen API-Calls standardmäßig
- Token-Zählung bei neuen Prompts schätzen und dokumentieren

## Modell-Auswahl Guidance
- Reasoning / Architektur: Claude Sonnet 4.5+
- Code-Review / File-Analyse: Claude Haiku 3.5
- Lokale Tasks / Datenschutz: Ministral 8B via Ollama
- Benchmark-Judge: separates Modell vom zu testenden Modell
