# Documentation Quality Test Module

## Übersicht

Das **Documentation Quality** Modul bewertet die Qualität von Code-Dokumentation, README-Dateien und API-Dokumentation. Es prüft Struktur, Vollständigkeit, technische Korrektheit und Usability.

## Features

- ✅ **Strukturanalyse**: Sections, TOC, logischer Flow, Formatierung
- ✅ **Vollständigkeits-Check**: Installation, Usage, Examples, Configuration, Troubleshooting
- ✅ **Technische Korrektheit**: Syntax Highlighting, valide Links, Versions-Info
- ✅ **Usability-Bewertung**: Zielgruppe, Keywords, Contribution Guide, Visual Hierarchy

## Bewertungskategorien

Das Modul bewertet nach einem **zweistufigen System** (Total: 130 Punkte):

### 1. Error Detection (100 Punkte)
Hierbei wird geprüft, ob das Modell die versteckten Fehler im Dokumentations-Asset findet. Die Fehler sind in 4 Schwierigkeitsstufen unterteilt:

- **Labeled Issues (Easy - 25 Punkte)**: Explizit markierte Fehler (z.B. `<!-- TODO: Add installation steps -->`).
- **Standard Issues (Medium - 30 Punkte)**: Offensichtliche Lücken (z.B. fehlende Prerequisites).
- **Advanced Issues (Hard - 25 Punkte)**: Subtile Fehler (z.B. falsche Syntax in Code-Beispielen, tote Links).
- **Expert Issues (Very Hard - 20 Punkte)**: Komplexe Probleme (z.B. inkonsistente API-Versionierung, fehlende Security-Hinweise).

### 2. Solution Quality (30 Punkte)
Hierbei wird die Qualität der generierten Verbesserungsvorschläge bewertet:

- **Code-Beispiele**: Sind die Beispiele syntaktisch korrekt und hilfreich?
- **Best Practices**: Werden gängige Standards (z.B. Semantic Versioning, Conventional Commits) eingehalten?
- **Struktur & Klarheit**: Ist die Dokumentation logisch aufgebaut und verständlich?

## Verfügbare Test-Assets

### Asset 001: README Quality Assessment
- **Kategorie**: README.md Bewertung
- **Schwierigkeit**: Tiered (Easy → Expert)
- **Issues**: 17 (25P Labeled, 30P Standard, 25P Advanced, 20P Expert)
- **Kontext**: CLI-Tool für Log-Analyse (Python)
- **Zielgruppe**: DevOps Engineers, Backend Developers
- **Test**: Analysiere unvollständige README und identifiziere Verbesserungspotential

**Was wird getestet:**
- Erkennung fehlender Best Practices (TOC, Badges, Contributing)
- Identifikation unvollständiger Sections (Installation, Configuration)
- Code-Beispiel-Qualität (Syntax Highlighting fehlt)
- Open Source Conventions

### Asset 002: REST API Endpoint Documentation
- **Kategorie**: API-Dokumentation
- **Schwierigkeit**: Tiered (Easy → Expert)
- **Issues**: 14 (25P Labeled, 30P Standard, 25P Advanced, 20P Expert)
- **Kontext**: E-Commerce POST /api/v1/orders Endpoint
- **Zielgruppe**: Backend Developers, API Consumers
- **Test**: Bewerte unvollständige REST API Dokumentation

**Was wird getestet:**
- Security/Authentication (Bearer Tokens, API Keys)
- REST Semantics (Status Codes, Idempotency, HTTP Methods)
- Error Handling (Structured Responses, Rate Limiting)
- Developer Experience (OpenAPI Specs, Examples, Edge Cases)

### Asset 003: Component Library Props Documentation
- **Kategorie**: Component Documentation
- **Schwierigkeit**: Tiered (Easy → Expert)
- **Issues**: 16 (25P Labeled, 30P Standard, 25P Advanced, 20P Expert)
- **Kontext**: React DataTable Component mit TypeScript
- **Zielgruppe**: Frontend Developers, Design System Engineers
- **Test**: Analysiere unvollständige React Component Props Dokumentation

**Was wird getestet:**
- Struktur & Vollständigkeit (Props-Tabelle, Required/Optional, Default Values)
- Technische Korrektheit (TypeScript Types, Event-Handler-Signaturen, Generics)
- Beispiele & Use Cases (Code-Beispiele, Edge Cases, Storybook)
- Developer Experience (Accessibility, Performance, Component Library Principles)

### Asset 004: Setup Guide - Local Dev Environment
- **Kategorie**: Setup Guide & Troubleshooting
- **Schwierigkeit**: Tiered (Easy → Expert)
- **Issues**: 16 (25P Labeled, 30P Standard, 25P Advanced, 20P Expert)
- **Kontext**: E-Commerce-Platform (Docker + Vite + Node.js + PostgreSQL)
- **Zielgruppe**: Junior bis Mid-Level Frontend/Backend Developers
- **Test**: Bewerte unvollständige Setup-Anleitung für lokales Dev-Environment

**Was wird getestet:**
- Struktur & Vollständigkeit (Prerequisites, nummerierte Schritte, Erfolgs-Checks)
- Technische Korrektheit (Copy-pastable Commands, ENV-Vars, Ports, Versionen)
- Troubleshooting & Error Handling (5+ häufige Fehler, Lösungen mit Commands)
- Developer Experience (Quick Start, OS-Hinweise Mac M1/M2/Linux/Windows, DevOps Best Practices)

### Asset 005: Changelog - Git Commits to Release Notes
- **Kategorie**: Changelog & Release Notes
- **Schwierigkeit**: Tiered (Easy → Expert)
- **Issues**: 17 (25P Labeled, 30P Standard, 25P Advanced, 20P Expert)
- **Kontext**: TaskFlow SaaS (15 Git-Commits → User-Facing Release Notes)
- **Zielgruppe**: End-User, Admins, Developers (3 Segmente)
- **Test**: Transformiere technische Git-Commits in nutzerfreundliche Release Notes

**Was wird getestet:**
- Struktur & Kategorisierung (Keep a Changelog Format, Added/Changed/Fixed/Security, Semantic Versioning)
- User-Centricity (User-Benefits statt Tech-Details, verständliche Sprache, Features vs Code)
- Vollständigkeit & Priorisierung (Breaking Changes, Security, Migration Guides, Links zu Issues)
- Format & Wartbarkeit (Keep a Changelog Standard, Zielgruppen-Segmentierung, Rollback-Infos)

## Verwendung

### Einzelnes Asset testen

```bash
python run_benchmark.py \
  --module documentation_quality \
  --asset 001 \
  --model qwen2.5:14b
```

### Alle Assets des Moduls

```bash
python run_benchmark.py \
  --module documentation_quality \
  --model mistral-large-latest \
  --provider mistral
```

### Mit Commercial Models

```bash
# Claude 3.5 Sonnet
python run_benchmark.py \
  --module documentation_quality \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022

# GPT-4o
python run_benchmark.py \
  --module documentation_quality \
  --provider openai \
  --model gpt-4o
```

## Scoring-System

Das Modul verwendet ein **100-Punkte-System**:

```
90-100: Excellent  ⭐⭐⭐⭐⭐
75-89:  Good       ⭐⭐⭐⭐
60-74:  Acceptable ⭐⭐⭐
40-59:  Needs Work ⭐⭐
0-39:   Poor       ⭐
```

### Score-Berechnung

```python
total_score = (
    structure_clarity_score +    # 25 Punkte
    completeness_score +         # 25 Punkte
    technical_accuracy_score +   # 25 Punkte
    usability_score              # 25 Punkte
)
```

### Beispiel-Output

```
Documentation Quality Test Results
===================================

Model: qwen2.5:14b
Asset: documentation_quality_001 (README Quality Assessment)

Score: 78/100 (Good) ⭐⭐⭐⭐

Breakdown:
  1. Struktur & Klarheit:     20/25 (✓ Sections erkannt, ⚠ TOC fehlt)
  2. Vollständigkeit:         19/25 (⚠ Installation zu kurz, ⚠ FAQ fehlt)
  3. Technische Korrektheit:  18/25 (⚠ Syntax Highlighting fehlt, ⚠ Links fehlen)
  4. Usability:               21/25 (✓ Zielgruppe klar, ⚠ Contributing fehlt)

Execution Time: 12.4s
Tokens Used: ~890
```

## Entwicklung

### Neue Assets hinzufügen

1. Erstelle neue YAML-Datei in `assets/`:
   ```bash
   touch assets/asset_002_api_docs.yaml
   ```

2. Verwende Template aus `asset_001_readme_quality.yaml`

3. Definiere:
   - `metadata`: ID, Name, Category, Tags
   - `context`: Hintergrund des Test-Szenarios
   - `prompt`: Aufgabenstellung für LLM
   - `scoring`: Bewertungskriterien (4 Kategorien)
   - `expected_output`: Was eine gute Response enthalten sollte

4. Update `config.yaml`:
   ```yaml
   assets:
     count: 2  # Erhöhen
   ```

### Testing

```bash
# Alle Tests für das Modul
pytest benchmark_modules/documentation_quality/tests/

# Mit Coverage
pytest --cov=benchmark_modules/documentation_quality tests/
```

## Modulstatus

✅ **5 Assets vollständig implementiert und getestet**

- **80 Gesamt-Issues** (Asset 001: 17, Asset 002: 14, Asset 003: 16, Asset 004: 16, Asset 005: 17)
- **Tiered Difficulty**: Alle Assets mit Labeled → Standard → Advanced → Expert
- **100-Punkte-Scoring**: 30P Error Detection + 30P Solution Quality + 20P Formatting + 20P Expertise
- **Pytest**: 11/11 Tests passing
- **Production-Ready**: Bereit für Benchmarks mit Local & Commercial Models

## Mögliche zukünftige Erweiterungen

### Scoring-Verbesserungen

- **Automated Link Checking**: Tatsächliche URL-Validierung
- **Readability Metrics**: Flesch-Kincaid Score für Lesbarkeit
- **Image/Diagram Detection**: Prüfung auf visuelle Elemente
- **Accessibility Scoring**: Alt-Text für Bilder, Clear Language

### Zusätzliche Dokumentationstypen

- Architecture Decision Records (ADRs)
- OpenAPI/Swagger Specification Quality
- Inline Code Comments & Docstrings (Python/TypeScript)
- Tutorial vs Reference Documentation Balance

### Scoring-Erweiterungen

- **Automated Link Checking**: Tatsächliche URL-Validierung
- **Readability Metrics**: Flesch-Kincaid Score für Lesbarkeit
- **Image/Diagram Detection**: Prüfung auf visuelle Elemente
- **Accessibility**: Alt-Text für Bilder, Clear Language

## Konfiguration

Siehe [`config.yaml`](config.yaml) für:
- Scoring-Gewichte pro Kategorie
- Schwellwerte (Excellent, Good, Acceptable)
- Asset-Metadaten

## Beste Praktiken

### Für Test-Design
- **Realistische Szenarien**: Verwende echte Projekt-Beispiele
- **Klare Bewertungskriterien**: Definiere messbare Qualitätsmerkmale
- **Ausgewogene Schwierigkeit**: Mix aus offensichtlichen und subtilen Problemen

### Für LLM-Testing
- **Temperature**: 0.3 (Balance zwischen Konsistenz und Kreativität)
- **Context Window**: Dokumentation sollte < 4000 Tokens sein
- **Prompt Clarity**: Strukturierte Aufgabenstellung mit Beispielen

## Siehe auch

- [ADDING_MODULES.md](../../docs/ADDING_MODULES.md) - Neue Module erstellen
- [BENCHMARK_SCENARIOS.md](../../docs/BENCHMARK_SCENARIOS.md) - Scenario-Design
- [Code Quality Module](../code_quality/README.md) - Verwandtes Modul

## Lizenz

Teil des CrucibleMark Benchmark Frameworks.
