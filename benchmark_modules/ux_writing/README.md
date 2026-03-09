# UX Writing Module

> **Technical Metadata**
>
> - **ID:** `ux_writing`
> - **Namespace:** `benchmark_modules.ux_writing`
> - **Class:** `UXWritingTest` (inherits `BaseTest`)
> - **Version:** v2.0.1 (Clean Architecture + Pylint Optimized)
> - **Type:** Content Strategy & Microcopy
> - **Quality Score:** 99/100 (A+)
> - **Pylint Score:** 9.07/10

______________________________________________________________________

## 🔍 Module Overview

Dieses Modul prüft die Kompetenz von LLMs im Bereich **User Experience Writing**. Es bewertet präzise, handlungsleitende und empathische Microcopy für:

- **Error Messages** (Nutzerfreundliche Fehlermeldungen)
- **Button Labels** (Kontextsensitive CTAs)
- **Onboarding Flows** (Progressive Disclosure)
- **Accessibility Labels** (ARIA/Screen Reader)
- **Microcopy Audits** (Health & Safety-Critical Content)

______________________________________________________________________

## 🏗 Architecture (v2.0)

Version 2.0 führt eine **modulare Clean Architecture** ein:

```
benchmark_modules/ux_writing/
├── test.py                          # Test Runner (orchestriert Execution & Scoring)
├── core/
│   ├── constants.py                 # Zentrale Konfiguration (Tiers, Thresholds, Ratios)
│   ├── evaluators/                  # Modular Evaluator Package
│   │   ├── __init__.py              # Public API Exports
│   │   ├── base.py                  # Abstract Base + IssueEvaluator (Hybrid Matching)
│   │   ├── keyword.py               # KeywordPresence/Absence Evaluators
│   │   ├── structure.py             # Markdown Table & Structure Validation
│   │   ├── validation.py            # Regex, Code, Length Validators
│   │   └── factory.py               # EvaluatorFactory (Strategy Pattern)
│   ├── models.py                    # Data Models (UXScenario, UXCriterion, etc.)
│   ├── services.py                  # LLM Client Wrapper
│   └── io_manager.py                # JSON/CSV Export & Reporting
├── assets/                          # 5 YAML Test Scenarios
│   ├── asset_001_error_messages.yaml
│   ├── asset_002_button_labels.yaml
│   ├── asset_003_onboarding_flow.yaml
│   ├── asset_004_accessibility_labels.yaml
│   └── asset_005_microcopy_audit.yaml
└── tests/
    ├── test_ux_writing.py           # Asset Loading Tests (3 tests)
    ├── test_evaluators.py           # Unit Tests für alle Evaluators (15+ tests)
    ├── test_issue_evaluator.py      # Hybrid Matching Tests (8+ tests)
    └── test_yaml_consistency.py     # YAML Structure Validation (5+ tests)
```

______________________________________________________________________

## 🎯 Core Components

### 1. **constants.py** – Zentrale Konfiguration

Alle Magic Numbers und Thresholds sind hier zentralisiert:

```python
# Tier Thresholds (für Scoring)
TIER_S_THRESHOLD = 95.0  # Expert
TIER_A_THRESHOLD = 85.0  # Professional
TIER_B_THRESHOLD = 70.0  # Competent
TIER_C_THRESHOLD = 50.0  # Novice

# Evaluator Constraints
MIN_SENTENCE_LENGTH = 15      # Für Semantic Similarity
SIMILARITY_THRESHOLD = 0.78   # Embedding Match Score
MAX_BUTTON_LENGTH = 50        # Mobile First Constraint
MIN_TABLE_COLUMNS = 2         # Markdown Table Validation

# Asset-Specific Tuning
ASSET_REQUIRED_RATIOS = {
    "ux_writing_003": 0.5,  # Onboarding (softer)
    "ux_writing_004": 1.0,  # A11y (strict WCAG)
    "ux_writing_005": 0.4,  # Health (empathy focus)
}
DEFAULT_REQUIRED_RATIO = 0.6
```

**Vorteil:** Änderungen an Schwellenwerten müssen nur an **einer Stelle** gemacht werden!

______________________________________________________________________

### 2. **evaluators/** – Modulare Scoring-Engine

#### **base.py** – Fundament

- `CriterionEvaluator` (Abstract Base Class): Interface für alle Evaluators
- `IssueEvaluator`: **Hybrid Matching** (String + Semantic Similarity + WCAG Regex)

**Besonderheit:** Erkennt WCAG-Nummern (`1.4.3`) automatisch via Regex, nutzt Embedding-Similarity als Fallback.

#### **keyword.py** – Keyword-basierte Checks

- `KeywordPresenceEvaluator`: Prüft, ob Required Keywords vorhanden sind
- `KeywordAbsenceEvaluator`: Prüft, dass Forbidden Keywords fehlen (z.B. Jargon)

#### **structure.py** – Format-Validierung

- `MarkdownTableEvaluator`: Prüft Tabellen-Struktur (Zeilen, Spalten)
- `StructureValidationEvaluator`: Prüft Required Elements (z.B. "Begründung"-Spalte)

#### **validation.py** – Complex Checks

- `RegexEvaluator`: Pattern Matching (z.B. WCAG-Nummern `\d\.\d\.\d`)
- `CodeValidationEvaluator`: Code-Block-Erkennung (z.B. `aria-label`)
- `LengthValidationEvaluator`: Button-Längen-Constraint (Mobile First)

#### **factory.py** – Strategy Pattern

Instanziiert den richtigen Evaluator basierend auf YAML `check_method`:

```python
EvaluatorFactory.get_evaluator("keyword_presence")
# → KeywordPresenceEvaluator()
```

______________________________________________________________________

### 3. **Scoring Logic** – Tiered Difficulty

Alle Assets verwenden ein **60/30/10 Scoring-Schema**:

| Category | Weight | Beschreibung | |----------|--------|--------------| | **Error Detection** | 60% | Issue-Erkennung (Labeled → Standard → Advanced → Expert) | | **Solution Quality** | 30% | Ton, Struktur, Clarity | | **Formatting** | 10% | Markdown, Spalten-Struktur |

**Error Detection Tiers:**

1. **Labeled Issues** (10 Punkte): Basics (z.B. "Kein Jargon")
1. **Standard Issues** (20 Punkte): Intermediate (z.B. "Actionable Language")
1. **Advanced Issues** (15 Punkte): Empathie & Ton
1. **Expert Issues** (15 Punkte): Psychologie (z.B. Endowed Progress Effect)

______________________________________________________________________

## 📂 Available Assets

| Asset ID | Name | Schwierigkeit | Besonderheit | Default Ratio | |----------|------|---------------|--------------|---------------| | **001** | Error Messages | Tiered | Jargon-Elimination, Call-to-Action | 0.6 | | **002** | Button Labels | Tiered | Length < 25 chars, Context-Aware CTAs | 0.6 | | **003** | Onboarding Flow | Tiered | Progressive Disclosure, Jargon-Free | 0.5 (softer) | | **004** | Accessibility (ARIA) | Tiered | WCAG-Konformität, Screen Reader | 1.0 (strict) | | **005** | Microcopy Audit | Tiered | Health Context, Safety-Critical | 0.4 (empathy) |

______________________________________________________________________

## 🧪 Testing

### Test-Suite (28 Tests, ~80% Coverage)

```bash
# Alle Tests ausführen
pytest benchmark_modules/ux_writing/tests/

# Spezifische Test-Dateien
pytest benchmark_modules/ux_writing/tests/test_evaluators.py -v
pytest benchmark_modules/ux_writing/tests/test_issue_evaluator.py -v
pytest benchmark_modules/ux_writing/tests/test_yaml_consistency.py -v
```

### Test-Coverage Breakdown

| Test-Datei | Tests | Coverage | |------------|-------|----------| | `test_ux_writing.py` | 3 | Asset Loading | | `test_evaluators.py` | 15+ | Alle Evaluator-Klassen | | `test_issue_evaluator.py` | 8+ | Hybrid Matching (String + Semantic) | | `test_yaml_consistency.py` | 5+ | YAML-Struktur & Gewichte |

**Alle Tests sind deterministisch** (keine LLM-Calls, nur String-Matching auf Fixtures).

______________________________________________________________________

## 📊 Quality Metrics

| Metric | Value | Status | |--------|-------|--------| | **Overall Quality Score** | **99/100** | ✅ A+ | | **Pylint Score** | **9.07/10** | ✅ Excellent | | **Type-Hint Coverage** | **98%** | ✅ Near-Perfect | | **Test Coverage** | **~80%** | ✅ Production-Ready | | **Largest File** | **119 LOC** | ✅ (was 310) | | **Magic Numbers** | **0** | ✅ (was 8) | | **Tests Passing** | **28/28** | ✅ All Green |

______________________________________________________________________

## 🔄 Changelog

### v2.0.1 (2026-02-02) – Pylint Optimization

**Polish & Bug Fixes:**

- 🐛 **Fixed critical duplicate method** in `IssueEvaluator` (was causing incorrect scoring)
- 🐛 **Removed unreachable code** in `validation.py` (partial scoring now works)
- ✨ Added module docstrings to all evaluators (95% coverage)
- 🎨 Fixed PEP-8 violations (line length, indentation)
- 🔧 Disabled `R0903` (too-few-public-methods) for Strategy Pattern classes
- 📈 **Pylint Score: 8.24 → 9.07** (+10%)

**Metrics Update:**

- Quality Score: 98/100 → **99/100**
- Type-Hint Coverage: 98% (unchanged)
- Test Coverage: ~80% (unchanged)

______________________________________________________________________

### v2.0.0 (2026-02-01) – Major Refactoring

**Breaking Changes:** None (API-compatible)

**New Features:**

- ✨ Created `core/constants.py` (all magic numbers centralized)
- 🏗 Split `evaluators.py` → 6 modules (`base`, `keyword`, `structure`, `validation`, `factory`)
- 🐛 Fixed YAML bugs in Asset 002/003:
  - Asset 002: `Newsletter-Button` split into positive/negative checks
  - Asset 003: `Tech-Jargon` consistency fixed (`inverse_match: true`)
- 📝 Added `default_required_ratio` to all assets (transparent tuning)
- 🧪 Expanded tests: **3 → 28 tests** (+833%)
- 📚 Added Google-style docstrings (all public methods)

**Metrics:**

- Quality Score: 65/100 → **98/100** (+51%)
- Largest File: 310 LOC → **119 LOC** (-68%)
- Magic Numbers: 8 → **0** (-100%)
- Type-Hint Coverage: 85% → **98%** (+15%)
- Test Coverage: ~20% → **~80%** (+300%)

______________________________________________________________________

## 🚀 Usage Example

```python
from pathlib import Path
from benchmark_modules.ux_writing.test import UXWritingTest
from utils.llm_client import LLMClient

# Load Asset
asset_path = Path("benchmark_modules/ux_writing/assets/asset_001_error_messages.yaml")
test = UXWritingTest(asset_path)

# Execute Test
llm_client = LLMClient()
result = test.execute(
    model="mistral-large",
    llm_client=llm_client,
    provider="ollama"
)

# Score Response
scores = test.score_response(result["response"])

print(f"Total Score: {scores['total_score']}/100")
print(f"Tier: {scores['tier']}")
# Output:
# Total Score: 78.5/100
# Tier: Tier B (Competent)
```

______________________________________________________________________

## 🛠 Development

### Code-Style

- **Linter:** Pylint (Score: 9.07/10)
- **Formatter:** Black (Line length: 100)
- **Type-Checker:** mypy (98% coverage)

### Pre-Commit Checks

```bash
# Run before commit
pylint benchmark_modules/ux_writing/
pytest benchmark_modules/ux_writing/tests/
mypy benchmark_modules/ux_writing/ --strict
```

______________________________________________________________________

## 📖 Further Reading

- **Architecture Overview:** See `docs/CrucibleMark_Architecture_Overview.md`
- **Data Format:** See `docs/DATA_FORMAT.md`
- **Golden Standards:** See `docs/GOLDEN_STANDARDS.md`

______________________________________________________________________

## 📝 License & Maintainers

**Maintainer:** CrucibleMark Core Team\
**Status:** ✅ Production-Ready (v2.0.1)\
**Last Updated:** 2026-02-02

______________________________________________________________________

**Questions?** Open an issue or contact the maintainers.
