# Documentation Quality

> Bewertet, ob ein LLM technische Dokumentation schreiben kann — vollständig,
> strukturiert und für Entwickler tatsächlich nützlich. Das Modul prüft fünf
> Dokumentationsaufgaben: README-Erstellung, API-Referenzen, Komponenten-Docs,
> Setup-Guides und Changelogs.

**Modul-ID:** `documentation_quality` | **Klasse:** `DocumentationTest` | **Version:** 2.0.0
**Assets:** 5 | **Sprache:** Deutsch | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

Technische Dokumentation unterscheidet sich von anderen Schreibaufgaben durch
ihr Vollständigkeitsgebot: Fehlende Parameter, falsche Code-Beispiele oder eine
fehlende Troubleshooting-Section sind in der Praxis echte Nutzungs-Blocker.
Das Modul testet, ob Modelle nicht nur schreiben können, sondern auch wissen,
*was* dokumentiert werden muss — ohne dass jeder Abschnitt in der Aufgabe
explizit eingefordert wird.

Jedes Asset verwendet **Tiered Difficulty**: Vom offensichtlich Fehlenden bis zu
subtilen Best-Practice-Verstößen (z. B. keine Quick-Start-Sektion, keine
Zielgruppenangabe, fehlende API-Keywords für Discoverability).

---

## Scoring-Methodik

Standard-Fallback: `regex: 0.10 / judge: 0.90`.

| Dimension | Gewicht | Beschreibung |
|---|---|---|
| **Fehler-Erkennung** | 70 % | Identifiziert das Modell, was fehlt oder falsch ist? Gestaffelt von offensichtlich bis Expert-Level |
| **Lösungsqualität** | 30 % | Vollständigkeit, Korrektheit, Klarheit der geschriebenen Abschnitte |

Struktur-Validierung: Dokumenttyp-spezifische Schemata (`DOC_TYPE_SCHEMAS`) prüfen
Heading-Hierarchie, Code-Block-Anzahl und Pflicht-Sections.
Asset 004 (Setup Guide) bewertet zusätzlich die Lesbarkeit nach Flesch-Kincaid
(Mindest-Score: 60).

Score-Contribution: `routine: 1.0 / reasoning: 0.0` (alle Assets).

---

## Test Assets

### `documentation_quality_001` — README Quality
```
Typ:       README-Analyse und -Verbesserung
Kontext:   Technical Writer für ein Open-Source Python-CLI-Projekt.
           Junior Developer hat eine erste README erstellt, die wichtige
           Elemente vermissen lässt.
Tiered Difficulty Breakdown:
  Level 1 (25 Pkt. – Easy):   Fehlende Syntax-Highlighting, zu kurze Installation
  Level 2 (30 Pkt. – Medium): Kein Table of Contents, keine Links, keine Versions-Info
  Level 3 (25 Pkt. – Hard):   Fehlender Quick Start, keine Zielgruppenangabe, kein Contributing
  Level 4 (20 Pkt. – Expert): API-Docs verlinkt, Keywords für SEO/Discoverability,
                               Production-Status kommuniziert
Scoring:   Issue Detection (4 Level) + Solution Quality (Code-Beispiele, Priorisierung)
```

---

### `documentation_quality_002` — REST API Documentation
```
Typ:       API-Endpoint dokumentieren
Kontext:   Technical Writer, Flask-API für SaaS-Produkt.
Input:     Flask-Endpunkt mit Parametern, Response-Schema und Authentifizierung.
Anforderungen:
  - Alle Parameter typisiert und beschrieben (keine Halluzinationen)
  - Response-Schema dokumentiert (inkl. Fehler-Codes)
  - Mindestens ein Beispiel-Request (curl oder HTTP)
Scoring:   Parameter-Vollständigkeit per Regex + Qualität per Judge
```

---

### `documentation_quality_003` — Component Props Documentation
```
Typ:       React/Vue-Komponente vollständig dokumentieren
Input:     Komponenten-Code mit Props, aber fehlender Dokumentation
Anforderungen:
  - Props-Tabelle: Name | Type | Default | Required | Beschreibung
  - Format-Compliance (Markdown-Tabelle) wird bewertet
  - Alle Props müssen in Tabelle erscheinen
Scoring:   Tabellen-Format per Regex + Vollständigkeit per Judge
```

---

### `documentation_quality_004` — Setup Guide & Troubleshooting
```
Typ:       Komplexen Installations-Flow dokumentieren (Docker + Dependencies)
Kontext:   Technical Writer, SaaS-Onboarding für DevOps-Teams.
Anforderungen:
  - Prerequisites → Steps → Troubleshooting Struktur
  - Troubleshooting enthält Fehler-Codes und Lösungen
  - Jeder Schritt num eriert und atomar
  - Lesbarkeit nach Flesch-Kincaid > 60 (Setup Guides müssen lesbar sein!)
Scoring:   Struktur per DOC_TYPE_SCHEMAS + Flesch-Kincaid automatisch berechnet
```

---

### `documentation_quality_005` — Changelog Release Notes
```
Typ:       Git-Commit-Log → strukturiertes Changelog
Kontext:   Technical Writer, SaaS "TaskFlow" released alle 2 Wochen.
           Git-Commits sind für Endnutzer unbrauchbar
           ("refactor: extract auth middleware", "fix: update regex pattern").
Input:     Rohes Git-Commit-Log (ca. 20 Commits, gemischt tech/product)
Anforderungen:
  - Keep-a-Changelog-Standard: Added / Changed / Fixed / Removed
  - Semantic Versioning (v1.2.3-Format)
  - Nutzerorientierte Sprache (kein Commit-Hash-Stil)
  - Breaking Changes explizit markiert
Scoring:   Strukturelle Sections per Regex + Tonalität per Judge
```

---

## Technischer Aufbau

Sub-Evaluatoren in `core/evaluators/`:

| Klasse / Datei | Aufgabe |
|---|---|
| `TieredScoringEngine` (`tiered_scoring.py`) | Fehlerklassifikation + Hybrid-Matching |
| `StructureValidator` (`structure_validator.py`) | Prüfung gegen `DOC_TYPE_SCHEMAS` |
| `ReadabilityScorer` (`readability_scorer.py`) | Flesch-Kincaid-Berechnung |
| `CompletenessChecker` (`completeness_checker.py`) | Fuzzy-Matching: "Installing" ≈ "Installation" |
| `SemanticMatcher` (`semantic_matcher.py`) | Sentence-Transformer-Fallback |
| `SolutionQualityEvaluator` (`solution_quality.py`) | Code-Blöcke, Best-Practices, Klarheit |

---

## Konfiguration

```python
# core/constants.py (Auszug)
DOC_TYPE_SCHEMAS = {
    "readme_quality":  ["Installation", "Usage", "Examples"],
    "api_docs":        ["Endpoint", "Parameters", "Response", "Example"],
    "setup_guide":     ["Prerequisites", "Steps", "Troubleshooting"],
    "changelog":       ["Added", "Changed", "Fixed", "Removed"],
}

ASSET_SPECIFIC_CONFIG = {
    "documentation_quality_004": {
        "readability_min_score": 60,    # Flesch-Kincaid Mindest-Score
        "semantic_threshold": 0.75,
    }
}
```
