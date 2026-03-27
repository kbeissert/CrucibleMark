# Active Context

**Last Updated:** 2026-03-27
**Session:** Dokumentations-Überarbeitung (vollständig)

## Erledigte Aufgaben (diese Session)

### Textüberarbeitung: README.md & PROJECT_STATUS.md
- Version-Inkonsistenz behoben: README badge → v3.2.0 (war: v3.1.0)
- Stil nach autor.md-Regeln: direkt, kein Passiv, max. 20 Wörter pro Satz
- PROJECT_STATUS.md: Veraltete v1.x-Roadmap-Einträge bereinigt

### Textüberarbeitung: docs/ (alle 12 Dateien)
- **GOLDEN_STANDARDS.md**: Stil-Überarbeitung, "Was Sie hier finden" → "Was du hier findest"
- **AGGREGATION_LOGIC.md**: Stil-Überarbeitung, Tabellen-Formatierung gefixt
- **MAINTENANCE_LOG.md**: Stil-Überarbeitung
- **BACKUP_STRATEGY.md**: Stil-Überarbeitung
- **SCORING_METHODOLOGY.md**: Platinum-Tier ergänzt, Schwellenwerte dokumentiert
- **SETUP_GUIDE.md**: Stil-Überarbeitung, Passiv-Konstruktionen beseitigt
- **ARCHITECTURE.md**: Provider-Tabelle gefixt (war broken inline), Roadmap-Status aktualisiert (v1.x abgeschlossen), LLM-as-Judge als implementiert markiert, "für"-Encoding-Fehler korrigiert
- **AUDIT_AND_METAREVIEW.md**: Vollständige Stil-Überarbeitung
- **POLITICAL_COMPASS_KONZEPT.md**: Vollständige Stil-Überarbeitung
- **MODEL_CLASSIFICATION.md**: Badge-Tabelle synchronisiert (Platinum/Gold 80/Silver 65/Bronze 50/Standard <50), Verteilung aktualisiert (Gold = 1: Mistral Medium)
- **DEVELOPER_GUIDE.md**: Englische Prosa-Abschnitte übersetzt, "Happy Coding!" entfernt
- **USER_GUIDE.md**: Dreifaches Duplikat Abschnitt C bereinigt (→ einmalig), Badge-Tabelle synchronisiert, Speed-Classes-Tabelle gefixt, "Sie" → "du" durchgängig

## Kritische Informationen für nächste Session

### Versions-Stand
- **Framework:** v3.2.0 (aktuell, production-ready)
- **Alle Docs:** auf v3.2.0-kompatiblen Stand gebracht

### Badge-Schwellenwerte (kanonisch, SSOT: benchmark_config.yaml)
- 💎 Platinum: ≥ 95 %
- 🏆 Gold: ≥ 80 % (Mistral Medium: 81,3)
- 🥈 Silver: ≥ 65 %
- 🥉 Bronze: ≥ 50 %
- ⚖️ Standard: < 50 %

### Speed-Class-Schwellenwerte (kanonisch)
- ⚡ Fast: < 40s
- ⏱️ Medium: 40–80s
- 🐢 Slow: > 80s

### Offene technische Schulden (aus ARCHITECTURE.md)
- Test Coverage: ~60 % (Ziel: 95 %)
- CI/CD Pipeline: fehlt
- Rollback-Mechanismus: fehlt
- Diff Reports: fehlt

## Nächste mögliche Aufgaben
- CHANGELOG.md aktualisieren (enthält noch alte v1.x-Einträge)
- README.md Web-Export-Pipeline: Doku vervollständigen
- CI/CD Pipeline aufbauen (GitHub Actions)
