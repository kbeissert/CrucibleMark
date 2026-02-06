#!/usr/bin/env python3
"""
Unit Tests für Documentation Quality Module
Testet: Asset Loading, Scoring-Logik, Response Validation
"""

import pytest
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[3]))

from benchmark_modules.documentation_quality.test import DocumentationTest


# Test constants
TOTAL_POINTS = 100
STRUCTURE_POINTS = 25
COMPLETENESS_POINTS = 25
TECHNICAL_POINTS = 25
USABILITY_POINTS = 25


@pytest.fixture
def readme_asset_path():
    """README Quality Asset Path"""
    return Path(
        "benchmark_modules/documentation_quality/assets/asset_001_readme_quality.yaml"
    )


@pytest.fixture
def readme_test(readme_asset_path):
    """DocumentationTest Instance mit README Asset"""
    return DocumentationTest(readme_asset_path)


class TestAssetLoading:
    """Asset-Loading Tests"""

    def test_readme_asset_loads(self, readme_asset_path):
        """README Asset wird korrekt geladen"""
        assert readme_asset_path.exists(), "README Asset nicht gefunden"

        with open(readme_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        assert asset["metadata"]["id"] == "documentation_quality_001"
        assert asset["metadata"]["category"] == "documentation_quality"
        assert asset["metadata"]["subcategory"] == "readme_quality"
        assert "scoring" in asset

    def test_asset_has_required_fields(self, readme_asset_path):
        """Asset enthält alle erforderlichen Felder"""
        test = DocumentationTest(readme_asset_path)

        assert "metadata" in test.asset
        assert "context" in test.asset
        assert "prompt" in test.asset
        assert "scoring" in test.asset
        assert "expected_output" in test.asset

    def test_scoring_weights_sum_to_total_points(self, readme_asset_path):
        """Scoring-Gewichte summieren sich zur definierten Gesamtpunktzahl"""
        with open(readme_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        # Neue Struktur: scoring.total_points und error_detection/solution_quality
        assert "scoring" in asset

        # Lese die für dieses Asset definierte Gesamtpunktzahl (z.B. 100 oder 130)
        expected_total = asset["scoring"].get("total_points", 100)

        # Check dass error_detection + solution_quality = defined total points
        ed_weight = asset["scoring"]["error_detection"]["weight"]
        sq_weight = asset["scoring"]["solution_quality"]["weight"]

        total_weight = ed_weight + sq_weight
        assert total_weight == expected_total, (
            f"Weights ({total_weight}) müssen der Gesamtpunktzahl ({expected_total}) entsprechen"
        )


class TestScoringLogic:
    """Scoring-Logik Tests"""

    def test_empty_response_gives_zero_score(self, readme_test):
        """Leere Response gibt 0 Punkte"""
        score = readme_test.score_response("")

        assert score["total_score"] == 0
        assert score["percentage"] == 0
        assert score["status"] == "error"

    def test_error_response_gives_zero_score(self, readme_test):
        """Error Response gibt 0 Punkte"""
        score = readme_test.score_response("ERROR: Connection timeout")

        assert score["total_score"] == 0
        # assert "error" in score  <-- Removed: 'status' key holds error state, not exact string membership
        assert score["status"] == "error"

    def test_perfect_response_structure(self, readme_test):
        """Perfekte Response hat 2 Breakdown-Kategorien"""
        response = "# README Analysis\n\nsyntax highlighting\n```python\nprint('test')\n```\nTOC table of contents"
        score = readme_test.score_response(response)

        assert "category_scores" in score
        assert "error_detection" in score["category_scores"]
        assert "solution_quality" in score["category_scores"]
        assert score["status"] == "success"

    def test_keyword_matching_detects_issues(self, readme_test):
        """Keyword-Matching erkennt Issues korrekt"""
        response = """
# README Analysis

## Problems Found:

1. **Fehlende Code Syntax Highlighting** - Code blocks need ```python or ```bash
2. **Installation zu kurz** - Need prerequisites, venv recommendation, python version
3. **Kein TOC** - Should add table of contents for navigation
4. **Keine Links** - Add links to documentation, repository, github issues
5. **Fehlender Quick Start** - Add getting started section

## Solutions:

```python
# Better installation example
python -m venv venv
source venv/bin/activate
```

```bash
pip install package
```

Use **bold** for emphasis and proper formatting.
Priority: high, medium, low
"""
        score = readme_test.score_response(response)

        # Sollte mehrere Issues erkennen durch Keyword-Matching
        assert score["total_score"] > 30, (
            f"Sollte >30 Punkte bekommen, war {score['total_score']}"
        )
        assert score["status"] == "success"

    def test_tiered_difficulty_scoring(self, readme_test):
        """Tiered Difficulty System funktioniert"""
        # Response mit Labeled + Standard Issues
        response = """
Syntax highlighting fehlt - need ```python and ```bash.
Installation incomplete - prerequisites missing, venv needed.
Troubleshooting section fehlt completely.
TOC table of contents missing for navigation.
Links to documentation, repository not found.
"""
        score = readme_test.score_response(response)

        # Sollte Punkte in error_detection bekommen
        assert "error_detection" in score["category_scores"]
        ed_score = score["category_scores"]["error_detection"]
        assert ed_score["achieved"] > 0, "Error Detection sollte Punkte haben"


class TestResponsePatterns:
    """Tests für verschiedene Response-Muster"""

    def test_minimal_response_gets_low_score(self, readme_test):
        """Minimale Response bekommt niedrigen Score"""
        response = "Die README ist ok."
        score = readme_test.score_response(response)

        assert score["total_score"] < 30, (
            f"Minimale Response sollte < 30 bekommen, war {score['total_score']}"
        )

    def test_comprehensive_response_gets_high_score(self, readme_test):
        """Umfassende Response bekommt hohen Score"""
        response = """
# README Quality Analysis - Comprehensive Report

## Identified Issues

### LEVEL 1: Critical Issues (Labeled)
1. **Fehlende Code Syntax Highlighting** 
   - Problem: Code blocks lack ```python or ```bash syntax highlighting
   - Solution: Add proper language tags
   
2. **Installation zu kurz**
   - Problem: No prerequisites, no venv recommendation, no python version requirements
   - Solution: Add detailed installation with virtual environment setup
   
3. **Kein Troubleshooting/FAQ**
   - Missing: No FAQ section, no common issues, no troubleshooting guide
   
4. **Code-Beispiele ohne Kontext**
   - Problem: Examples lack output, explanation, or ergebnis demonstration

### LEVEL 2: Standard Issues
5. **Fehlendes TOC (Table of Contents)**
   - No inhaltsverzeichnis or navigation links
   
6. **Keine Links zu Dokumentation**
   - Missing: Links to docs, repository, github issues, weitere informationen
   
7. **Konfiguration nicht dokumentiert**
   - No config beispiel, configuration example, or yaml settings shown
   
8. **Keine Versions-Info**
   - Missing: Python version, compatibility info, requires statements
   
9. **Fehlende Badges**
   - No build status, shields, pypi version, or license badge

### LEVEL 3: Advanced Issues
10. **Fehlender Quick Start**
    - No getting started, quick start, or tldr section
    
11. **Zielgruppe nicht genannt**
    - Target audience (devops, backend developers) not specified
    
12. **Kein Contributing Guide**
    - Missing contribution, beitragen, pull request guidelines
    
13. **Schwache visuelle Hierarchie**
    - Limited use of bold, formatierung, hervorhebung

### LEVEL 4: Expert Issues
14. **API-Dokumentation unvollständig**
    - LogParser needs more parameter, optionen, methoden documentation
    
15. **Keine Keywords/Tags**
    - Missing SEO keywords, github topics, tags for discoverability
    
16. **Kein Production Readiness Hinweis**
    - No stable, beta, experimental status indication

## Recommended Solutions with Code Examples

### Solution 1: Add Syntax Highlighting

```python
# Better code example with context
from loganalyzer import LogParser

parser = LogParser(format='nginx')
results = parser.analyze('access.log')
print(results.summary())
```

```bash
# Installation with venv
python -m venv venv
source venv/bin/activate
pip install loganalyzer
```

### Solution 2: Add Configuration Example

```yaml
# config.yaml example
log_format: nginx
severity_levels:
  - error
  - warning
  - info
```

## Best Practices Applied
- Following **markdown** standards and conventions
- Using proper **best practice** formatting
- Clear **priorität** with critical, high, medium, low severity levels
- Implementing **standard** documentation patterns

## Priority Classification
- **Critical**: Syntax highlighting, installation, troubleshooting
- **High**: TOC, links, configuration
- **Medium**: Quick start, contributing, badges
- **Low**: Keywords, production status
"""
        score = readme_test.score_response(response)

        # Sollte sehr gut scoren durch:
        # - Alle 4 Tier-Levels erwähnt
        # - Viele Keywords getroffen
        # - Code-Beispiele mit Syntax
        # - Best Practices erwähnt
        # - Priorisierung vorhanden
        assert score["total_score"] > 50, (
            f"Comprehensive response sollte >50 bekommen, war {score['total_score']}"
        )
        assert score["status"] == "success"


class TestMetadata:
    """Metadata Tests"""

    def test_response_metadata_included(self, readme_test):
        """Response enthält Metadata"""
        response = "Test response with some content"
        score = readme_test.score_response(response)

        assert "metadata" in score
        assert "response_length" in score["metadata"]
        assert "word_count" in score["metadata"]
        assert score["metadata"]["word_count"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
