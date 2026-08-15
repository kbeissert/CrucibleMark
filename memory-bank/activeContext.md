# Active Context
Aktueller Stand und nächste Schritte.

- **Abgeschlossen:** Code-Review-Umsetzung v5.1.4 (Session 83) — alle 23 Findings umgesetzt und verifiziert (Ruff 0 Fehler, 1411 Tests grün, Naming-Gate 122 Cards OK). Enthielt: 5 kritische Fixes (u.a. combined_score-0.0-Fallback als dokumentierte Scoring-Änderung, Preis-SSoT nach config/model_pricing.yaml), Shell-Injection-Schließung, Blind-Evaluierung (Name-Priming aus Judge-Prompt), 8 CC>12-Splits verhaltenstreu, Ruff 409→0, DRY/Performance-Konsolidierung, Maintenance-Härtung.
- **Nächster Schritt:** Arbeitsbaum committen — 123 geänderte Dateien + 2 neue (config/model_pricing.yaml, utils/provider_config_text.py) + 1 gelöschte (scripts/maintenance/verify_counts.py), uncommittet auf Zuruf.
- **Offen/Risiko:** kilo.jsonc-API-Key bleibt in der Git-Historie (lokaler Netzwerk-Endpoint) — bei erhöhten Anforderungen Key rotieren oder History-Rewrite; sonst akzeptiertes Restrisiko.
