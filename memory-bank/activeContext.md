# Active Context
Aktueller Stand und nächste Schritte.

- **Abgeschlossen:** Web-Export Provider-Code-first-Auflösung (Session 85) — SPRK/VSPK-Runs emittieren jetzt den korrekten Inferenz-Server ('Llama.cpp (asusGX10)'/'vLLM (asusGX10)'), 432 Tests grün. Vorher: Echte-Token-Pipeline v5.1.5 (Session 84) — TPS/Judge-Context/Audit-Log laufen jetzt auf echten Provider-Tokens (neue CSV-Spalten `input_tokens`/`output_tokens`, Visible-Output-Formel fixt), 1572 Tests grün. Vorher: Code-Review-Umsetzung v5.1.4 (Session 83).
- **Nächster Schritt:** Verlorene CSV-Row `qwen3_8-27b-nvfp4 / code_quality_001` neu laufen lassen (durch Simulations-Write ersetzt, Audit-Log intakt), dann Arbeitsbaum committen (v5.1.4 + v5.1.5) auf Zuruf und `make docs-version-sync YES=1` beim Release.
- **Offen/Risiko:** (1) TPS-Semantik-Wechsel v5.1.5 — historische CSV-Zeilen behalten Schätzwerte (Upsert rechnet nicht neu durch), Leaderboard mischt alte/neue TPS bis Re-Runs. (2) `reasoning_tokens`-Spalte teils leer bei vLLM-Standard-Profilen — `think_content` ist die zuverlässigere Thinking-Quelle. (3) kilo.jsonc-API-Key in Git-Historie (lokaler Endpoint) — akzeptiertes Restrisiko.
