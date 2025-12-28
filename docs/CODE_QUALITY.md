# Code Quality Module - Dokumentation

## Übersicht

Das Code Quality Module testet die Fähigkeit von LLMs, Code-Probleme in verschiedenen Bereichen zu identifizieren und zu beheben:

- **WCAG Accessibility** - Barrierefreiheit nach WCAG 2.2 Standards
- **Security (OWASP)** - Sicherheitslücken gemäß OWASP Top 10
- **Performance** - Web Performance & Core Web Vitals Optimierung
- **API Design** - REST API Best Practices
- **Code Smells** - Refactoring-Bedarf und Maintainability

---

## Test Assets

### Asset-Struktur

Jedes Test-Asset ist eine YAML-Datei mit folgenden Komponenten:

```yaml
metadata:           # ID, Name, Kategorie, Schwierigkeit, Tags
context:            # Szenario-Beschreibung für das LLM
prompt:             # Aufgabenstellung mit Code-Beispiel
test_data:          # Issues die erkannt werden sollen (Tiered: Labeled, Standard, Advanced)
scoring:            # Bewertungskriterien (100 Punkte)
golden_standard:    # Referenz-Modelle für Vergleich
expected_results:   # Erwartete Score-Bereiche
notes:              # Hinweise und Besonderheiten
```

### Verfügbare Assets

Alle Assets nutzen nun das **Tiered Difficulty System** (Level 1-4).

| Asset | Issues | Schwierigkeit | Golden Standard |
|-------|--------|---------------|-----------------|
| **001 - WCAG Accessibility** | 11 | Tiered (1-4) | ✅ Mistral Large |
| **002 - Security (OWASP)** | 11 | Tiered (1-4) | ✅ Mistral Large |
| **003 - Performance** | 11 | Tiered (1-4) | ✅ Mistral Large |
| **004 - API Design** | 12 | Tiered (1-4) | ✅ Mistral Large |
| **005 - Code Smells** | 11 | Tiered (1-3) | ✅ Mistral Large |

---

## Scoring-System

Das Scoring basiert auf einem **hybriden Ansatz** (Keyword/Regex + Semantic Similarity) in 4 Kategorien:

### 1. Error Detection (60 Punkte)
- **Methode**: Keyword & Regex Matching
- **Tiered Scoring**:
    - **Labeled (Easy)**: Geringe Punktzahl
    - **Standard (Medium)**: Mittlere Punktzahl
    - **Advanced (Hard)**: Hohe Punktzahl
    - **Expert (Very Hard)**: Sehr hohe Punktzahl (nur für Top-Modelle)

### 2. Solution Quality (30 Punkte)
- **Methode**: Semantic Similarity (Vergleich mit Golden Standard)
- Korrektheit der vorgeschlagenen Lösungen
- Code-Beispiele vorhanden und syntaktisch korrekt

### 3. Formatting (15 Punkte)
- Markdown-Struktur mit Headers
- Code-Blöcke korrekt formatiert
- Priorisierung erkennbar

### 4. Expertise (10 Punkte)
- Fachbegriffe korrekt verwendet
- Tiefes Verständnis demonstriert
- Standards/Richtlinien referenziert

---

## Golden Standards

### Was sind Golden Standards?

Golden Standards sind Referenz-Antworten von leistungsstarken LLMs (z.B. Claude Sonnet, Mistral Large), die als Vergleichsbasis für lokale Modelle dienen.

### Verwendete Modelle

**Primary:** Mistral Large (verfügbar via Mistral API)
- Sehr gute Code-Analyse-Fähigkeiten
- Konsistente Antwort-Qualität
- Erwarteter Score: 85-95/100

**Secondary:** Claude 3.5 Sonnet (falls verfügbar)
- Beste Accessibility-Kenntnisse
- Sehr detaillierte Erklärungen
- Erwarteter Score: 90-98/100

### Golden Standards generieren

```bash
# Einzelnes Asset
python scripts/generate_golden_standard.py \
    test_modules/test_assets/code_quality/asset_001_wcag_audit.yaml \
    --use-asset-config

# Alle Assets
python scripts/generate_golden_standard.py \
    test_modules/test_assets/code_quality/*.yaml \
    --use-asset-config
```

Golden Standards werden gespeichert unter:
```
golden_standards/
├── mistral/
│   ├── code_quality_001.json
│   ├── code_quality_002.json
│   └── ...
└── anthropic/
    └── ...
```

### Golden Standard Format

```json
{
  "asset_id": "code_quality_001",
  "model": "mistral-large-latest",
  "provider": "mistral",
  "generated_at": "2025-12-27T01:30:00Z",
  "response": "# WCAG Accessibility Audit\n\n## Critical Issues\n...",
  "score": {
    "total": 92.5,
    "error_detection": 43.0,
    "solution_quality": 28.0,
    "formatting": 14.0,
    "expertise": 9.5
  },
  "metadata": {
    "response_time": 8.3,
    "temperature": 0.1,
    "max_tokens": 4096
  }
}
```

---

## Quick Start

### 1. Setup

```bash
# Repository klonen
git clone <repository-url>
cd crucible-mark

# Ollama installieren (falls nicht vorhanden)
curl -fsSL https://ollama.com/install.sh | sh

# Modelle herunterladen
ollama pull mistral-nemo
ollama pull qwen2.5-coder:7b
```

### 2. Einzelnen Test ausführen

```bash
# Test mit einem Asset
python scripts/run_benchmark.py \
    --models ministral-3:8b \
    --assets test_modules/test_assets/code_quality/asset_001_wcag_audit.yaml \
    --runs 1
```

### 3. Vollständiger Benchmark

```bash
# Alle Code Quality Assets mit mehreren Runs
python scripts/run_benchmark.py \
    --models ministral-3:8b qwen2.5-coder:7b \
    --assets test_modules/test_assets/code_quality/*.yaml \
    --runs 3
```

### 4. Ergebnisse analysieren

Ergebnisse werden gespeichert unter `outputs/runs/<timestamp>/`:

```
outputs/runs/20251227_023335/
├── results.csv              # Zusammenfassung
├── ministral-3_8b/
│   ├── 001_wcag_audit.md   # LLM Response
│   ├── 001_wcag_audit.json # Scoring Details
│   └── ...
└── qwen2.5-coder_7b/
    └── ...
```

---

## Test-Daten (test_data Section)

Jedes Asset definiert in der `test_data` Section die Issues, die erkannt werden sollen:

```yaml
test_data:
  issues:
    - issue: "Fehlender alt-Text bei Bildern"
      category: "WCAG 1.1.1 Non-text Content"
      severity: "critical"
      wcag: "1.1.1"
      explanation: "Bilder ohne alt-Attribut sind für Screen Reader unsichtbar."
      keywords:
        - "alt text"
        - "screen reader"
        - "wcag 1.1.1"
```

Diese Daten werden verwendet für:
- **Automatisches Scoring**: Keyword-basierte Erkennung
- **Threshold-Validierung**: Mindestanforderungen pro Issue
- **Dokumentation**: Was sollte erkannt werden

---

## Best Practices

### Asset-Entwicklung

1. **Realistische Code-Beispiele**: Nutze echten Production-Code mit echten Problemen
2. **Klare Schweregrade**: Critical = Must-Fix, High = Should-Fix, Medium = Nice-to-Fix
3. **Messbare Keywords**: Eindeutige Begriffe für automatisches Scoring
4. **Ausgewogene Verteilung**: Mix aus verschiedenen Severity-Levels

### Benchmark-Durchführung

1. **Multiple Runs**: Mindestens 3 Runs pro Modell für CV-Berechnung
2. **Temperature 0.1**: Für konsistente Ergebnisse
3. **Golden Standards aktuell halten**: Bei Asset-Änderungen neu generieren
4. **Modell-Vergleiche**: Immer mehrere Modelle gleichzeitig testen

### Scoring-Interpretation

- **90-100**: Exzellent - Professional-Grade
- **80-89**: Sehr gut - Production-Ready
- **70-79**: Gut - Mit Minor Issues
- **60-69**: Akzeptabel - Noch ausbaufähig
- **< 60**: Ungenügend - Major Gaps

---

## Troubleshooting

### Niedriger Score trotz guter Antwort

**Problem**: LLM hat alle Issues erkannt, aber Score ist niedrig.

**Lösung**: 
- Prüfe Keywords in `test_data` - sind sie zu spezifisch?
- Schaue dir `scoring.threshold` an - ist 0.40 zu hoch?
- Aktiviere `--verbose` um zu sehen, welche Issues nicht erkannt wurden

### Golden Standard generiert Fehler

**Problem**: `No module named 'anthropic'` oder ähnlich.

**Lösung**:
- Anthropic/Mistral SDK installieren: `pip install anthropic mistralai`
- Oder nur lokale Modelle nutzen (Golden Standard optional)

### Inkonsistente Scores bei Multiple Runs

**Problem**: CV > 10% bei gleichen Tests.

**Lösung**:
- Temperature senken (0.1 oder niedriger)
- Seed-Parameter setzen (falls Ollama unterstützt)
- Mehr Runs durchführen (5-10) für stabilere Statistik

---

## Weiterführende Informationen

- **Projektstruktur**: Siehe `STRUCTURE.md`
- **Changelog**: Siehe `CHANGELOG.md`
- **Root Quick Start**: Siehe `../QUICKSTART.md`
