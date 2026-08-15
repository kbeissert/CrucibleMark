# Active Context
Aktueller Stand und nächste Schritte.

- **Abgeschlossen:** v5.1.3 — drei vorbestehende Testfehler behoben (hermes-4-36b Orphan-Card via clean-model, Tag-Whitelist normalisiert mit Native-Quant/Harmony + Deprecated-Mappings, Ornith-Test invariantisiert). 1410 Tests grün, Web-Export verifiziert. Nemotron-3.5-lightning-Benchmark aus Session 81 ist gelaufen (50 CSV-Einträge).
- **Nächster Schritt:** v5.1.3-Changes committen (32 geänderte Dateien: Cards, Vocabulary, Tests, Docs-Stempel).
- **Offen/Risiko:** `make clean-model` bereinigt jetzt auch die Model-Card-Datei selbst (im Dry-Run verifizigt) — frühere manuelle Card-Löschungen sind obsolet.
