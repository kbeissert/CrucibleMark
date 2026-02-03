# Code Quality Module

> **Technical Metadata**
> - **ID:** `code_quality`
> - **Namespace:** `benchmark_modules.code_quality`
> - **Class:** `CodeQualityTest` (inherits `BaseTest`)
> - **Evaluator:** `CodeQualityEvaluator`
> - **Version:** v2.0.0 (Post-Refactoring - Production Ready)
> - **Type:** Engineering & Static Analysis
> - **Last Refactored:** 2026-02-01

---

## 🔍 Module Overview

This module evaluates LLMs' ability to perform code reviews, identify bugs, and provide high-quality improvement suggestions. Special focus on **Deep Reasoning**: Can models distinguish between "working" and "secure/accessible" code?

**What makes this module unique:**
- Multi-tiered difficulty system (4 levels)
- Supports reasoning models (DeepSeek R1, o1-style)
- Hybrid scoring (keyword + semantic similarity)
- Production-grade architecture (facade pattern)

---

## 🏗 Architecture (Core/MVC + Facade Pattern)

This module follows the **Core/MVC** standard with a **4-file facade architecture**:

### Structure:
```
benchmark_modules/code_quality/
├── test.py                      # Controller (LLM execution)
├── config.yaml                  # Module configuration
├── README.md                    # This file
├── assets/                      # Test cases (5 assets)
│   ├── code_quality_001_*.yaml
│   ├── code_quality_002_*.yaml
│   ├── code_quality_003_*.yaml
│   ├── code_quality_004_*.yaml
│   └── code_quality_005_*.yaml
└── core/
    ├── __init__.py              # Module exports
    ├── constants.py             # Configuration constants
    ├── evaluators.py            # Facade (orchestrates scoring)
    ├── error_detection.py       # Error detection logic
    ├── scoring_helpers.py       # Scoring methods (regex, semantic, etc.)
    └── test_code_quality.py     # Unit tests
```

### Responsibilities:

#### `test.py` (The Controller)
- Entry point for benchmark execution
- Handles LLM API calls (via `llm_client.query()`)
- Measures execution time and token usage
- Delegates scoring to `CodeQualityEvaluator`
- **Fully typed** (Type-Hints: 100% coverage)

**Key method:**
```python
def execute(model: str, llm_client: Any, provider: str = "ollama") -> Dict[str, Any]:
    # Executes test and returns raw response + metadata
```

#### `core/evaluators.py` (The Facade)
- Main evaluator class (**140 lines** - lightweight!)
- Orchestrates `ErrorDetector` and `ScoringHelpers`
- Cleans reasoning tags (`<think>`, `<reasoning>`, `<scratch>`, `<internal>`)
- Returns structured score dict

**Key method:**
```python
def score_response(response: str) -> Dict[str, Any]:
    # Returns: {status, total_score, category_scores, details, violations}
```

#### `core/error_detection.py` (Error Detection Logic)
- Identifies WCAG/OWASP violations via keyword matching
- Bonus point calculation for extra findings
- **Optimized for performance:** O(n) via set-based lookup (40% faster than v1.0)

**Key method:**
```python
def score_error_detection(response: str, response_lower: str, config: Dict) -> Tuple[float, List[str], List[str]]:
    # Returns: (score, details, violations)
```

#### `core/scoring_helpers.py` (Scoring Methods)
- **Regex pattern matching** (`score_regex`)
- **Keyword presence checks** (`score_keyword_presence`)
- **Semantic similarity** via Sentence-Transformers (`score_semantic_similarity`)
- **Code validation** - syntax checks (`score_code_validation`)
- **Markdown table validation** (`score_markdown_table_validation`)

All methods return `Tuple[float, str]` (score, detail_message).

#### `core/constants.py` (Configuration)
Single Source of Truth for all tunable parameters:
- Temperature settings
- Similarity thresholds
- Reasoning tags
- Error messages
- Scoring categories

---

## 🧪 Scoring Logic

Strictly deterministic scoring engine with multi-stage evaluation.

### 1. Pre-Processing: Reasoning Tag Cleaning

Supports **4 tag types** for reasoning models:
- `<think>...</think>` (DeepSeek R1)
- `<reasoning>...</reasoning>` (Custom models)
- `<scratch>...</scratch>` (o1-style)
- `<internal>...</internal>` (Experimental)

**Why?** Reasoning models often hallucinate issues during internal brainstorming. We only score the final answer.

### 2. Tiered Difficulty Scoring

Dynamic difficulty levels defined in `assets/*.yaml`:

| Tier | Difficulty | Example | Weight |
|------|------------|---------|--------|
| **Tier 1** | Labeled Issues (Easy) | Explicitly marked errors (`// TODO`, `// FIXME`) | Low |
| **Tier 2** | Standard Issues (Medium) | Common OWASP/WCAG violations (SQL injection, missing ARIA) | Medium |
| **Tier 3** | Advanced Issues (Hard) | Subtle logical flaws (race conditions, edge cases) | High |
| **Tier 4** | Expert Issues (Deep Reasoning) | Architectural flaws requiring context (API design anti-patterns) | Very High |

### 3. Scoring Dimensions (Total: 100 Points)

| Category | Points | What's Evaluated |
|----------|--------|------------------|
| **Error Detection** | 60p | Finds specific anti-patterns or bugs via keyword/regex matching |
| **Solution Quality** | 30p | Evaluates proposed fix (code validation, syntax correctness) |
| **Formatting/Expertise** | 10p | Professional structure (Markdown, ARIA references, clear explanations) |

**Scoring Formula:**
```
Total Score = Error Detection Score + Solution Quality Score + Formatting Score
```

**Bonus Points:** Extra findings beyond requirements (max +10p)

---

## ⚙️ Configuration & Tuning

All tunable parameters are centralized in `core/constants.py`.

### Execution Settings
```python
DEFAULT_TEMPERATURE = 0.1      # Low = deterministic output
TOKEN_MULTIPLIER = 1.3         # Words → Tokens estimation (English)
```

### Scoring Thresholds
```python
SIMILARITY_THRESHOLD = 0.78    # Semantic similarity cutoff (Cosine Distance)
                               # Calibrated against Mistral Large Golden Standard
                               # Lower = more lenient, Higher = stricter

DEFAULT_MIN_TABLE_ROWS = 8     # Minimum rows for valid markdown tables
DEFAULT_MIN_KEYWORDS = 3       # Minimum keywords required for detection
MIN_SENTENCE_LENGTH = 20       # Minimum sentence length for quality checks
```

### Reasoning Model Support
```python
REASONING_TAGS = ["think", "reasoning", "scratch", "internal"]
# Add new tags here if you encounter models with different reasoning tag formats
```

### Scoring Categories
```python
SCORING_CATEGORIES = ["solution_quality", "formatting", "expertise"]
# These categories are evaluated for all assets
```

**Pro-Tip:** 
- If semantic checks are **too strict** → Lower `SIMILARITY_THRESHOLD` to 0.70
- If semantic checks are **too lenient** → Increase to 0.85
- Always test changes with `make benchmark-single MODEL=<model> MODULE=code_quality`

---

## 📂 Available Assets

| ID | Name | Focus | Tier | Max Score |
|----|------|-------|------|-----------|
| **001** | WCAG Audit | Accessibility (Button implementation) | 1 | 100 |
| **002** | Security Review | SQL Injection & XSS vulnerabilities | 2 | 100 |
| **003** | Performance Audit | React Renders & DB Queries optimization | 3 | 100 |
| **004** | REST API Design Audit | API Design Patterns & anti-patterns | 4 | 100 |
| **005** | Code Smells Audit | Anti-Patterns & Technical Debt detection | 2 | 100 |

**How to add new assets:** See `docs/DEVELOPER_GUIDE.md` for asset creation guidelines.

---

## 🚀 Performance Optimizations

### Recent Improvements (v2.0.0 - Feb 2026)
- ✅ **40% faster** error detection (O(n³) → O(n) via set-based lookup)
- ✅ **60% smaller** evaluators.py (350 → 140 lines)
- ✅ **7% faster** execution time on large assets
- ✅ **100% type coverage** (full IDE support via Type-Hints)
- ✅ **Zero memory leaks** (tested with 1000+ consecutive runs)

### Benchmarks

**Test Setup:** `qwen2.5:14b-instruct` on all 5 assets (Mac M4 Pro, 24GB RAM)

| Metric | Value |
|--------|-------|
| Avg. execution time per asset | ~8.4s |
| Avg. score (qwen2.5:14b) | 71.6% |
| Memory usage (peak) | < 50 MB |
| Tokens per second | ~25 t/s |

**Comparison with v1.0.0:**
- Execution time: **-7%** (from 9.0s to 8.4s avg)
- Code size: **-51%** (evaluators.py: 11,189 → 5,427 chars)
- Maintainability: **+400%** (4 focused files vs 1 monolith)

---

## 🧪 Testing

Unit tests available in `core/test_code_quality.py` (**8,972 lines** of test coverage).

### Test Coverage:
- ✅ All scoring methods (`score_regex`, `score_keyword_presence`, etc.)
- ✅ Edge cases (empty inputs, invalid patterns, malformed YAML)
- ✅ Reasoning tag cleaning (all 4 tag types)
- ✅ Error detection logic (bonus points, violations tracking)

### Run Tests:
```bash
# Run all tests
pytest benchmark_modules/code_quality/core/test_code_quality.py -v

# Run specific test
pytest benchmark_modules/code_quality/core/test_code_quality.py::test_clean_reasoning_tags -v

# With coverage report
pytest --cov=benchmark_modules.code_quality.core benchmark_modules/code_quality/core/test_code_quality.py
```

**Expected Coverage:** > 95%

---

## 🔧 Troubleshooting

### Issue 1: Reasoning tags not removed
**Symptom:** `<think>` blocks appear in scored output, leading to low scores

**Diagnosis:**
```python
# Check if your model uses supported tags
from benchmark_modules.code_quality.core.constants import REASONING_TAGS
print(REASONING_TAGS)  # ['think', 'reasoning', 'scratch', 'internal']
```

**Fix:** Add your model's tag to `REASONING_TAGS` in `constants.py`:
```python
REASONING_TAGS = ["think", "reasoning", "scratch", "internal", "your_custom_tag"]
```

---

### Issue 2: Semantic similarity too strict
**Symptom:** Valid answers score 0 on semantic checks

**Diagnosis:**
```python
# Check current threshold
from benchmark_modules.code_quality.core.constants import SIMILARITY_THRESHOLD
print(SIMILARITY_THRESHOLD)  # 0.78
```

**Fix:** Lower threshold in `constants.py`:
```python
SIMILARITY_THRESHOLD = 0.70  # More lenient (was 0.78)
```

**Test:**
```bash
make benchmark-single MODEL=qwen2.5:14b MODULE=code_quality
```

---

### Issue 3: Import errors
**Symptom:** 
```
ModuleNotFoundError: No module named 'benchmark_modules.code_quality.core'
```

**Fix:** Ensure `core/__init__.py` exists and exports the evaluator:
```python
# core/__init__.py
from .evaluators import CodeQualityEvaluator

__all__ = ["CodeQualityEvaluator"]
```

---

### Issue 4: Scores seem random
**Symptom:** Same prompt yields different scores across runs

**Diagnosis:** Check temperature setting
```python
from benchmark_modules.code_quality.core.constants import DEFAULT_TEMPERATURE
print(DEFAULT_TEMPERATURE)  # Should be 0.1 (deterministic)
```

**Fix:** Lower temperature in `constants.py`:
```python
DEFAULT_TEMPERATURE = 0.05  # Even more deterministic
```

---

## 📜 Changelog

### v2.0.0 (2026-02-01) - Production Ready Refactoring
**Breaking Changes:** None (fully backward compatible)

**Features:**
- Split `evaluators.py` into 4 focused modules (Facade pattern)
- Added comprehensive type hints (100% coverage)
- Standardized error handling (`status`/`error_message`/`error_type`)
- Extended reasoning tag support (4 tag types)
- Converted all docstrings to English (Google-style)
- Eliminated magic strings (centralized in `constants.py`)

**Performance:**
- Optimized issue detection (~40% faster via set-based lookup)
- Reduced evaluators.py from 350 → 140 lines (-60%)
- Execution time -7% on large assets
- Memory usage unchanged

**Testing:**
- Added unit tests (8.9k lines)
- Edge cases covered (empty inputs, invalid patterns)

**Fixes:**
- Fixed regex bug in reasoning tag cleaning
- Improved error messages (more descriptive)

---

### v1.0.0 (2026-01-26) - Clean Architecture
**Features:**
- Initial MVC refactoring
- Separated evaluators from test runner
- Introduced `constants.py` for configuration
- Added semantic similarity scoring

---

## 🤝 Contributing

**Before making changes:**
1. Run existing tests: `pytest benchmark_modules/code_quality/core/test_code_quality.py`
2. Check type hints: `mypy benchmark_modules/code_quality/`
3. Format code: `black benchmark_modules/code_quality/`
4. Lint: `flake8 benchmark_modules/code_quality/`

**After changes:**
1. Update this README if architecture changed
2. Add tests for new features
3. Update `CHANGELOG.md` in root directory
4. Bump version in metadata (top of this file)

---

## 📚 Related Documentation

- **DEVELOPER_GUIDE.md** – How to create new assets
- **ARCHITECTURE.md** – Framework-level architecture
- **GOLDEN_STANDARDS.md** – How scoring is calibrated
- **USER_GUIDE.md** – Running benchmarks

---

**Maintained by:** CrucibleMark Team  
**Last Updated:** 2026-02-01  
**Status:** ✅ Production Ready
