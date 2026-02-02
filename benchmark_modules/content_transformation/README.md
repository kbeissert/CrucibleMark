# Content Transformation Module

> **Technical Metadata**
> - **ID:** `content_transformation`
> - **Namespace:** `benchmark_modules.content_transformation`
> - **Class:** `ContentTransformationTest` (inherits `BaseTest`)
> - **Evaluator:** `ContentTransformationEvaluator` (Facade Pattern)
> - **Version:** v2.0.0 (Clean Architecture - Modular Evaluators)
> - **Type:** Creative Writing & Content Adaptation
> - **Pylint Score:** 9.63/10

---

## 🔍 Module Overview

This module tests LLMs' ability to **transform content across different formats, tones, and structures** while preserving core information. It evaluates creative adaptation skills essential for:

- **Marketing:** Landing pages, email campaigns, social media
- **Technical Writing:** Glossary simplification, documentation
- **Professional Communication:** Tone shifts (formal ↔ casual)
- **Content Repurposing:** Blog → Thread, Video scripts

Unlike pure accuracy tests, this module measures **style consistency**, **format compliance**, and **audience-appropriate tone**.

---

## 🏗 Architecture (Core/MVC v2.0)

```
benchmark_modules/content_transformation/
├── core/
│   ├── evaluators/
│   │   ├── __init__.py              # ContentTransformationEvaluator (Facade)
│   │   ├── tiered_scoring.py        # Error Detection (Tiered Difficulty)
│   │   ├── semantic_matcher.py      # Keyword + Semantic Similarity
│   │   ├── content_quality.py       # Solution Quality Scoring
│   │   ├── format_validator.py      # Format Checks (NEW in v2.0)
│   │   └── tone_evaluator.py        # Tone/Formality Detection (NEW in v2.0)
│   ├── constants.py                  # SEMANTIC_THRESHOLDS, FORMAT_SCHEMAS
│   └── __init__.py
├── assets/
│   ├── landing_page.yaml
│   ├── twitter_thread.yaml
│   ├── glossar_simplification.yaml
│   ├── video_script.yaml
│   ├── email_newsletter.yaml
│   └── sarcasm_shield.yaml
├── tests/
│   ├── __init__.py
│   └── test_evaluators.py           # Integration Tests (6 test cases)
├── test.py                           # Module Runner (Controller)
├── config.yaml                       # Module Configuration
└── README.md                         # This file
```

### Architecture Highlights

- **Facade Pattern:** `ContentTransformationEvaluator` orchestrates specialized sub-evaluators
- **Single Responsibility:** Each evaluator handles one concern (scoring, validation, tone)
- **Modular Design:** Easy to extend with new validators (e.g., `SEOEvaluator`, `ReadabilityEvaluator`)
- **Backward Compatible:** Maintains same interface as v1.0 (old code archived)

---

## 🧪 Scoring Logic

The module uses a **multi-dimensional scoring system** with configurable weights:

### 1. Error Detection (70 points)

Tiered difficulty system via `TieredScoringEngine`:

| Tier | Difficulty | Threshold | Example |
|------|------------|-----------|---------|
| **Labeled** | Easy | 40% keyword match | Explicitly marked issues (e.g., TODO) |
| **Standard** | Medium | 40% keyword match | Common violations (grammar, consistency) |
| **Advanced** | Hard | 35% keyword match | Subtle flaws (tone mismatch, missing CTA) |
| **Expert** | Deep Reasoning | 20% keyword match + 55% semantic | Complex errors (brand voice, cultural sensitivity) |

**Key Features:**
- **Hybrid Matching:** Exact keywords + semantic similarity fallback
- **Tier-Specific Thresholds:** Expert tier requires stricter validation (prevents false positives)
- **Think-Tag Cleaning:** Removes `<think>...</think>` blocks from reasoning models (DeepSeek R1)

### 2. Solution Quality (30 points)

Evaluated by `ContentQualityEvaluator`:

- **Creativity:** Engaging language, storytelling elements
- **Format Compliance:** Correct structure (e.g., 1/5 thread numbering)
- **Actionability:** Clear CTAs, next steps
- **Professionalism:** Absence of slang/profanity (for formal content)

### 3. Format Validation (NEW in v2.0)

Asset-specific structure checks via `FormatValidator`:

| Asset Type | Validation Rules |
|------------|------------------|
| **Twitter Thread** | Sequential numbering (1/5, 2/5), max 280 chars per tweet |
| **JSON Export** | Valid syntax, required keys, schema compliance |
| **Landing Page** | Headline, subheadline, CTA presence |
| **Video Script** | Spoken style markers (short sentences, questions) |

**Example:**
```python
is_valid, violations = FormatValidator.validate_twitter_thread(response, min_tweets=5)
# Returns: (False, ['Missing tweet numbers: [2, 4]'])
```

### 4. Tone Evaluation (NEW in v2.0)

Measures stylistic consistency via `ToneEvaluator`:

- **Formality Score:** 0.0 (casual) to 1.0 (formal)
  - Detects formal markers: "hereby", "pursuant", "notwithstanding"
  - Detects casual markers: "gonna", "wanna", "cool", "!"

- **Professionalism Score:** 0.0 (unprofessional) to 1.0 (professional)
  - Penalizes slang: "lol", "wtf", "stupid"
  - Rewards professional language: "please", "thank you", "regarding"

- **Spoken Style Detection:** For video scripts/podcasts
  - Fillers: "um", "like", "you know"
  - Direct address: "you", "we"
  - Questions and contractions

**Example:**
```python
formality = ToneEvaluator.measure_formality("Hey! This is gonna be awesome.")
# Returns: 0.35 (casual)

professionalism = ToneEvaluator.measure_professionalism("lol whatever")
# Returns: 0.2 (unprofessional)
```

---

## ⚙️ Configuration

All tunable parameters are centralized in `core/constants.py`:

### Semantic Thresholds

```python
SEMANTIC_THRESHOLDS = {
    "labeled": 0.45,   # Generous (for compatibility)
    "standard": 0.45,
    "advanced": 0.50,  # Medium strictness
    "expert": 0.55     # Strict (prevents false positives)
}
```

**Use Case:** Adjust if models consistently fail semantic checks or get false positives.

### Format Schemas

```python
FORMAT_SCHEMAS = {
    "twitter_thread": {
        "pattern": r"^\d+/\d+",
        "min_tweets": 3,
        "max_chars_per_tweet": 280
    },
    "landing_page": {
        "required_sections": ["headline", "subheadline", "cta"],
        "max_headline_chars": 60
    }
}
```

**Use Case:** Add new format types or adjust validation rules per asset.

### Scoring Weights

```python
DEFAULT_WEIGHTS = {
    "error_detection": 0.70,  # 70% of total score
    "solution_quality": 0.30  # 30% of total score
}
```

**Override per asset** in `config.yaml`:
```yaml
benchmarks:
  - id: "content_transformation_003"
    name: "Legal Glossary Simplification"
    score_contribution:
      routine: 0.7
      reasoning: 0.3  # More weight on reasoning for complex tasks
```

---

## 📂 Available Assets

| ID | Name | Tier | Format | Key Challenge |
|----|------|------|--------|---------------|
| **001** | Landing Page Hero | 1 | Marketing Copy | Conversion-focused writing |
| **002** | Twitter Thread | 1 | Social Media | Sequential numbering, 280-char limit |
| **003** | Legal Glossary Simplification | 2 | Technical → Layman | Simplification without losing accuracy |
| **004** | Video Script Tutorial | 2 | Written → Spoken | Conversational tone, pacing |
| **005** | Email Newsletter | 1 | Corporate → Engaging | Tone shift (formal → friendly) |
| **006** | Sarcasm Shield | 2 | Defensive Writing | Professionalism under pressure |

### Asset Details

**Asset 001: Landing Page Hero Section**
- **Input:** Product description (technical)
- **Expected Output:** Headline (<60 chars), subheadline, CTA
- **Scoring:** Format validation (headline/CTA presence) + conversion keywords

**Asset 002: Twitter Thread Adaptation**
- **Input:** Long-form blog post
- **Expected Output:** 5-tweet thread (1/5, 2/5, etc.)
- **Scoring:** Thread structure validation + engagement metrics

**Asset 003: Legal Glossary Simplification**
- **Input:** Legal jargon (e.g., "notwithstanding")
- **Expected Output:** Plain English explanation
- **Scoring:** Readability + accuracy preservation

**Asset 006: Sarcasm Shield (Incident Report)**
- **Input:** Frustrated customer complaint (unprofessional tone)
- **Expected Output:** Professional incident report
- **Scoring:** Professionalism score (must be > 0.8), absence of slang

---

## 🚀 Usage Examples

### Run Single Asset

```bash
cd benchmark_modules/content_transformation
python test.py
# Interactive mode: Select model and asset
```

### Programmatic Usage

```python
from benchmark_modules.content_transformation.test import ContentTransformationTest
from utils.llm_client import LLMClient

# Initialize
client = LLMClient()
test = ContentTransformationTest('content_transformation_002')  # Twitter Thread

# Execute
result = test.execute('qwen2.5-coder:7b', client)

# Check score
print(f"Total Score: {result['total_score']}/100")
print(f"Formality: {result['metadata'].get('formality_score', 'N/A')}")
```

### Custom Validation

```python
from benchmark_modules.content_transformation.core.evaluators import (
    FormatValidator,
    ToneEvaluator
)

# Validate Twitter thread
response = "1/3 First tweet\n2/3 Second\n3/3 Final"
is_valid, violations = FormatValidator.validate_twitter_thread(response, min_tweets=3)

# Measure tone
formality = ToneEvaluator.measure_formality(response)
professionalism = ToneEvaluator.measure_professionalism(response)
```

---

## 🧪 Testing

### Run Integration Tests

```bash
# All evaluator tests
pytest benchmark_modules/content_transformation/tests/test_evaluators.py -v

# Quick validation (no pytest required)
python benchmark_modules/content_transformation/tests/test_evaluators.py
```

**Test Coverage:**
- [x] FormatValidator: Twitter threads, JSON, landing pages
- [x] ToneEvaluator: Formality, professionalism, spoken style
- [x] TieredScoringEngine: Labeled → Expert tiers
- [x] SemanticMatcher: Keyword + semantic fallback
- [x] ContentQualityEvaluator: Solution quality scoring
- [x] Integration: Full pipeline (6 test cases)

**Current Status:** 6/6 tests passing ✅

---

## 📊 Performance & Quality Metrics

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| **LOC (evaluators.py)** | 400+ | ~50 (facade) | -87% |
| **Files** | 1 monolithic | 6 specialized | +500% modularity |
| **Pylint Score** | 7.5/10 | 9.63/10 | +28% |
| **Test Coverage** | 0% | 80% | +80% |
| **Maintainability** | Low | High | ✅ |
| **Format Validation** | ❌ None | ✅ 3 validators | NEW |
| **Tone Detection** | ❌ None | ✅ 3 metrics | NEW |

---

## 🔄 Migration Guide (v1.0 → v2.0)

### Breaking Changes

**None!** v2.0 maintains full backward compatibility via facade pattern.

### What Changed

1. **Internal Architecture:**
   - Old: `evaluators.py` (400 LOC monolith)
   - New: 6 specialized files in `core/evaluators/`

2. **New Features:**
   - `FormatValidator`: Structure checks (threads, JSON, landing pages)
   - `ToneEvaluator`: Formality/professionalism detection

3. **Configuration:**
   - Hardcoded thresholds → `constants.py`
   - Asset-specific schemas added

### Migrating Custom Code

If you extended `evaluators.py` in v1.0:

```python
# Old import (still works via facade)
from benchmark_modules.content_transformation.core.evaluators import ContentTransformationEvaluator

# New import (direct access to sub-evaluators)
from benchmark_modules.content_transformation.core.evaluators import (
    FormatValidator,
    ToneEvaluator,
    SemanticMatcher
)
```

### Old Code Archive

v1.0 code is preserved in `backups/content_transformation_evaluators_v1.py`.

---

## 🛠 Development

### Adding New Evaluators

1. Create new file in `core/evaluators/`:
   ```python
   # seo_evaluator.py
   class SEOEvaluator:
       @staticmethod
       def check_meta_description(response: str) -> dict:
           # Implementation
           pass
   ```

2. Export in `core/evaluators/__init__.py`:
   ```python
   from .seo_evaluator import SEOEvaluator
   __all__ = [..., "SEOEvaluator"]
   ```

3. Integrate in facade:
   ```python
   # In ContentTransformationEvaluator.score_response()
   seo_score = SEOEvaluator.check_meta_description(response)
   ```

### Code Quality Standards

- **Pylint:** Maintain score ≥ 9.0
- **Docstrings:** All public methods must have docstrings
- **Type Hints:** Use `typing` module for complex signatures
- **Tests:** Add test cases to `tests/test_evaluators.py`

---

## 🐛 Troubleshooting

### Issue: Semantic Similarity Always Fails

**Symptom:** Expert tier always scores 0, even for correct answers.

**Solution:** Lower `SEMANTIC_THRESHOLDS["expert"]` in `constants.py`:
```python
SEMANTIC_THRESHOLDS = {
    "expert": 0.50  # Was 0.55
}
```

### Issue: Format Validation Too Strict

**Symptom:** Twitter threads fail even when structure looks correct.

**Solution:** Check pattern in `FORMAT_SCHEMAS`:
```python
FORMAT_SCHEMAS = {
    "twitter_thread": {
        "pattern": r"\d+[/:]\d+"  # Allow "1:5" or "1/5"
    }
}
```

### Issue: Professionalism Score Too Low

**Symptom:** Professional text scores 0.3 (expected > 0.5).

**Solution:** Check if text contains slang words in `ToneEvaluator.CASUAL_WORDS`. Adjust penalty in `measure_professionalism()`.

---

## 📚 References

- **UX Writing Module:** Similar architecture (reference implementation)
- **Code Quality Module:** Tiered scoring pattern
- **Semantic Similarity:** `utils/similarity.py` (sentence-transformers)
- **Base Test:** `benchmark_modules/base_test.py` (parent class)

---

## 📝 Changelog

### v2.0.0 (2026-02-02)

**Features:**
- ✨ Added `FormatValidator` for structure checks (threads, JSON, landing pages)
- ✨ Added `ToneEvaluator` for formality/professionalism detection
- ✨ Modular evaluator architecture (6 specialized files)
- ✨ Integration test suite (6 test cases)

**Improvements:**
- 🚀 Pylint score: 7.5 → 9.63 (+28%)
- 🚀 Reduced monolithic evaluator: 400 LOC → 50 LOC facade (-87%)
- 🚀 Test coverage: 0% → 80%

**Fixes:**
- 🐛 Semantic threshold consistency (Expert tier validation)
- 🐛 Think-tag cleaning for reasoning models (DeepSeek R1)
- 🐛 Professionalism scoring too lenient (adjusted penalties)

**Breaking Changes:**
- None (backward compatible via facade)

### v1.0.0 (2025-12-29)

- Initial release
- Basic error detection (tiered difficulty)
- Solution quality scoring
- 6 test assets (landing page, thread, glossary, video, newsletter, sarcasm)

---

**Version:** 2.0.0  
**Author:** CrucibleMark Framework  
**License:** MIT  
**Last Updated:** 2026-02-02
