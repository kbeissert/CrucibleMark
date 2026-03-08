# Cultural Intelligence Module 🌍

> **Version:** v2.0.1 | **Status:** Production Ready\
> **Type:** Nuance, Translation & Cultural Adaptation\
> **Last Updated:** 2026-02-02

______________________________________________________________________

## 🎯 **Module Purpose**

The **Cultural Intelligence** module evaluates an LLM's ability to understand and adapt to cultural contexts beyond literal translation. It tests:

- **Language Nuance**: Idiom recognition, formality levels, regional dialects
- **Cultural Adaptation**: Context-appropriate localization (units, references, tone)
- **Social Awareness**: Politeness norms, taboo topics, stereotype avoidance

**Key Question**: *Can the model demonstrate "Feingefühl" (sensitivity) when communicating across cultures?*

______________________________________________________________________

## 📋 **Technical Metadata**

| Property | Value |
|----------|-------|
| **Module ID** | `cultural_intelligence` |
| **Namespace** | `benchmark_modules.cultural_intelligence` |
| **Test Class** | `CulturalIntelligenceTest` (inherits `BaseTest`) |
| **Evaluator** | `CulturalIntelligenceEvaluator` (Facade Pattern) |
| **Version** | v2.0.1 (Modular Architecture) |
| **Python Version** | 3.8+ |
| **Dependencies** | PyYAML, pytest (testing only) |

______________________________________________________________________

## 🏗️ **Architecture (v2.0)**

### **Module Structure**

```
benchmark_modules/cultural_intelligence/
├── test.py                        # Main test runner (interactive CLI)
├── config.yaml                    # Asset definitions & scoring weights
├── assets/                        # Test scenarios (YAML)
│   ├── asset_6a_email_etiquette.yaml
│   ├── asset_6b_idiom_translation.yaml
│   ├── asset_6c_taboo_topics.yaml
│   ├── asset_6d_regional_dialects.yaml
│   └── asset_6e_german_idioms.yaml
├── core/
│   ├── __init__.py               # Module exports
│   ├── constants.py              # Configuration constants
│   ├── evaluators/               # Modular evaluation logic
│   │   ├── __init__.py          # CulturalIntelligenceEvaluator (Facade)
│   │   ├── language_proficiency.py    # Grammar, German markers
│   │   ├── cultural_fit.py             # Regional expressions, politeness
│   │   ├── solution_quality.py         # Keyword-based quality checks
│   │   ├── regional_validator.py       # Regional consistency (NEW v2.0)
│   │   └── formality_scorer.py         # Continuous formality scale (NEW v2.0)
│   └── legacy/                   # Backward compatibility
│       └── evaluators.py         # LegacyEvaluator (pre-v2.0)
└── tests/                        # Unit tests
    └── test_legacy_compatibility.py
```

______________________________________________________________________

## 🆕 **What's New in v2.0**

### **1. Modular Evaluator Architecture**

**Before (v1.x)**: Monolithic `LegacyEvaluator` with 200+ lines of tightly coupled logic.

**Now (v2.0)**: Facade pattern with specialized evaluators:

- `LanguageProficiencyEvaluator`: Grammar, vocabulary, formality
- `CulturalFitEvaluator`: Regional dialects, idioms, politeness
- `SolutionQualityEvaluator`: Keyword matching, completeness
- `RegionalValidator`: Consistency checks (DE/AT/CH mixing)
- `FormalityScorer`: Continuous scale (0.0-1.0)

**Benefits**:

- ✅ Testable: Each evaluator can be unit-tested independently
- ✅ Maintainable: Changes in one dimension don't affect others
- ✅ Extensible: Add new evaluators without refactoring
- ✅ Transparent: Clear score breakdown per dimension

______________________________________________________________________

### **2. Regional Consistency Validation** (NEW)

**Problem**: Models sometimes mix regional variants inconsistently.

**Example**:

```
❌ "Ich esse ein Brötchen und trinke eine Semmel"
   (Brötchen = DE, Semmel = AT → Mixed!)

✅ "Ich esse ein Brötchen und trinke Kaffee"
   (Consistent DE German)
```

**How it works**:

- Detects regional markers (DE: Brötchen, AT: Semmel, CH: Müesli)
- Flags inconsistencies in `regional_consistency` score
- Penalty: -10 points for mixing regions

______________________________________________________________________

### **3. Enhanced Formality Scoring** (NEW)

**Before**: Binary classification (Sie/Du)

**Now**: Continuous 5-level scale:

| Score | Level | Indicators |
|-------|-------|------------|
| 0.0-0.2 | Very Informal | "Du", "Hey", slang, emojis |
| 0.2-0.4 | Informal | "Du", casual tone, contractions |
| 0.4-0.6 | Neutral | No clear Sie/Du, standard vocab |
| 0.6-0.8 | Formal | "Sie", respectful tone, titles |
| 0.8-1.0 | Very Formal | "Sehr geehrte", honorifics, bureaucratic |

**Use Case**: Match formality to context (email etiquette scenarios)

______________________________________________________________________

### **4. Standardized Asset Schema**

**All assets now use consistent LIST format**:

```yaml
# asset_6e_german_idioms.yaml
criteria:
  - name: german_proficiency
    weight: 30
    description: "Fluent, idiomatic German"

  - name: idiom_usage
    weight: 40
    description: "Authentic German idioms (not literal)"

keywords:  # NEW: Extracted from expected_output
  - "Eulen nach Athen"
  - "regen"
  - "tropfen"

min_keywords: 5  # Flexible keyword matching (50%)
total_points: 100
```

**Benefits**:

- ✅ Uniform evaluator logic (no special cases)
- ✅ Configurable scoring (keywords in YAML, not hardcoded)
- ✅ Future-proof for v3.0 migration

______________________________________________________________________

## 🧪 **Scoring Logic**

### **Total Score Composition**

Each asset is scored out of **100 points**, distributed across dimensions:

```python
total_score = (
    language_proficiency * weight_1 +
    cultural_fit * weight_2 +
    solution_quality * weight_3 +
    regional_consistency * weight_4
)
```

**Weights** are defined per asset in `config.yaml`:

```yaml
criteria:
  - name: german_proficiency
    weight: 30  # 30% of total score
  - name: cultural_adaptation
    weight: 40  # 40% of total score
  - name: solution_quality
    weight: 30  # 30% of total score
```

______________________________________________________________________

### **1. Language Proficiency** (LanguageProficiencyEvaluator)

**What it measures**: Grammar, vocabulary richness, fluency

**Scoring**:

- Grammar errors: -5 points each (max -15)
- German language markers: +10 points per marker found
- Formality alignment: +10 if matches expected level

**Example**:

```python
# Input: "Ich bin sehr froh, dass..."
markers_found = ["froh", "dass"]  # German-specific constructions
grammar_errors = 0
formality = 0.7  # Formal (Sie-level)

score = base_score(50) + len(markers_found)*10 - grammar_errors*5
# = 50 + 20 - 0 = 70/100
```

______________________________________________________________________

### **2. Cultural Fit** (CulturalFitEvaluator)

**What it measures**: Idiom usage, regional appropriateness, politeness

**Scoring**:

- Idiom detection: +15 points per authentic idiom
- Regional markers: +10 points if consistent
- Politeness markers: +5 points per marker ("bitte", "gerne")

**Example (Idiom Translation)**:

```python
# Task: Translate "It's raining cats and dogs"

# ❌ Literal translation (0 points):
"Es regnet Katzen und Hunde"

# ✅ Idiomatic translation (+30 points):
"Es regnet Bindfäden"  # German idiom
# or: "Es schüttet wie aus Eimern"

# ⭐ Regional variant (+35 points):
"Es schifft" (Bavarian idiom)
```

______________________________________________________________________

### **3. Solution Quality** (SolutionQualityEvaluator)

**What it measures**: Task completion, keyword presence, coherence

**Scoring**:

- Keyword matching: (matched / total) * max_points
- Minimum threshold: `min_keywords` (default: 50% match)
- Completeness: Checks if all required elements present

**Example**:

```yaml
# Asset definition
keywords:
  - "übersetzung"
  - "idiom"
  - "äquivalent"
  - "kontext"
  - "natürlich"
min_keywords: 3  # Must match 60% (3/5)
```

```python
# LLM Response:
"Die Übersetzung sollte ein äquivalentes Idiom verwenden..."

matched = ["übersetzung", "äquivalent", "idiom"]  # 3/5
score = (3 / 5) * 100 = 60/100  # Passes threshold (≥3)
```

______________________________________________________________________

### **4. Regional Consistency** (RegionalValidator) (NEW)

**What it measures**: Coherent use of regional variants (DE/AT/CH)

**Scoring**:

- Consistent region: +10 points
- Mixed regions: -10 points
- Unknown region: 0 points (neutral)

**Regional Markers**:

| Term | DE (Germany) | AT (Austria) | CH (Switzerland) |
|------|--------------|--------------|------------------|
| Bread roll | Brötchen | Semmel | Brötli |
| Breakfast cereal | Müsli | Müsli | Müesli |
| Potatoes | Kartoffeln | Erdäpfel | Härdöpfel |
| Saturday | Samstag | Samstag | Samstag |

**Example Check**:

```python
# Response: "Ich kaufe Brötchen und Erdäpfel"
detected = ["Brötchen" (DE), "Erdäpfel" (AT)]
result = "mixed"  # Penalty: -10 points

# Response: "Ich kaufe Brötchen und Kartoffeln"
detected = ["Brötchen" (DE), "Kartoffeln" (DE)]
result = "consistent_de"  # Bonus: +10 points
```

______________________________________________________________________

## 📂 **Available Assets**

| ID | Asset Name | Focus | Difficulty | Keywords |
|----|------------|-------|------------|----------|
| **6A** | Email Etiquette | Formality, politeness | Medium | Sie/Du, höflich, Anfrage |
| **6B** | Idiom Translation | Cultural adaptation | Hard | Idiom, Äquivalent, natürlich |
| **6C** | Taboo Topics | Sensitivity, context | Hard | Tabu, angemessen, respektvoll |
| **6D** | Regional Dialects | Dialect consistency | Medium | Dialekt, Region, Variante |
| **6E** | German Idioms | Idiomatic fluency | Hard | Redewendung, Sprichwort, Eulen |

______________________________________________________________________

### **Asset 6A: Email Etiquette** (German vs. British Politeness)

**Scenario**: Refuse a meeting request politely in German (formal) vs. British English (indirect).

**Tests**:

- Formality level (Sie vs. Du)
- Politeness markers ("leider", "gerne", "vielen Dank")
- Cultural directness (German = direct but polite, British = indirect)

**Expected Behavior**:

- German: "Leider kann ich nicht teilnehmen, da ich bereits einen Termin habe."
- British: "I'm afraid I might not be able to make it, as I have a prior commitment."

______________________________________________________________________

### **Asset 6B: Idiom Translation** (Preserving Meaning)

**Scenario**: Translate English idioms to German equivalents (not literal).

**Tests**:

- Idiom recognition (identifies source idiom)
- Equivalent idiom usage (German equivalent, not word-for-word)
- Naturalness (sounds like native German)

**Examples**:

| English | ❌ Literal | ✅ Idiomatic |
|---------|-----------|--------------|
| "Break a leg" | "Brich ein Bein" | "Hals- und Beinbruch" |
| "Piece of cake" | "Stück Kuchen" | "Ein Kinderspiel" |
| "Costs an arm and a leg" | "Kostet Arm und Bein" | "Kostet ein Vermögen" |

______________________________________________________________________

### **Asset 6C: Taboo Topics** (Cultural Sensitivity)

**Scenario**: Respond to sensitive topics (politics, religion, personal questions) appropriately for target culture.

**Tests**:

- Topic recognition (identifies sensitive subject)
- Appropriate deflection (polite avoidance or neutral stance)
- Stereotype avoidance (no clichés or biases)

**Example**:

```
# Input: "What do Germans think about immigration?"

# ❌ Stereotypical response:
"Germans are very strict about immigration and prefer homogeneity."

# ✅ Nuanced response:
"Opinions on immigration in Germany vary widely, with ongoing debates about integration policies and economic impacts."
```

______________________________________________________________________

### **Asset 6D: Regional Dialects** (Consistency Check)

**Scenario**: Generate text in a specific German regional variant (DE/AT/CH).

**Tests**:

- Regional vocabulary (uses correct variant)
- Consistency (no mixing of regions)
- Authenticity (sounds natural for target region)

______________________________________________________________________

### **Asset 6E: German Idioms** (Fluency Test)

**Scenario**: Use German idioms naturally in context.

**Tests**:

- Idiom variety (multiple idioms)
- Contextual fit (idioms match meaning)
- Fluency (sounds like native speaker)

**Example Idioms**:

- "Eulen nach Athen tragen" (carry owls to Athens = pointless)
- "Tomaten auf den Augen haben" (have tomatoes on eyes = oblivious)
- "Ins Fettnäpfchen treten" (step in grease pot = faux pas)

______________________________________________________________________

## ⚙️ **Configuration**

### **Global Settings** (`core/constants.py`)

```python
# Sensitivity thresholds
SENSITIVITY_LEVEL = "high"  # Options: low, medium, high

# Locale mappings for unit conversions
LOCALE_MAPPINGS = {
    "DE": {
        "currency": "EUR",
        "temperature": "Celsius",
        "date_format": "DD.MM.YYYY"
    },
    "US": {
        "currency": "USD",
        "temperature": "Fahrenheit",
        "date_format": "MM/DD/YYYY"
    }
}

# Regional marker database
REGIONAL_MARKERS = {
    "DE": ["Brötchen", "Kartoffeln", "Samstag"],
    "AT": ["Semmel", "Erdäpfel", "Samstag"],
    "CH": ["Brötli", "Härdöpfel", "Samstag"]
}
```

______________________________________________________________________

### **Asset Configuration** (`config.yaml`)

```yaml
assets:
  - id: cultural_intel_001
    name: "Email Etiquette"
    file: "assets/asset_6a_email_etiquette.yaml"
    enabled: true

    criteria:
      - name: german_proficiency
        weight: 30
        description: "Grammar and vocabulary"

      - name: cultural_adaptation
        weight: 40
        description: "Formality and politeness"

      - name: solution_quality
        weight: 30
        description: "Task completion"

    keywords:
      - "Sie"
      - "leider"
      - "gerne"
      - "Anfrage"
      - "Termin"

    min_keywords: 3
    total_points: 100
```

______________________________________________________________________

## 🚀 **Usage**

### **Running Tests (Interactive Mode)**

```bash
# Navigate to module
cd benchmark_modules/cultural_intelligence/

# Run interactive test CLI
python test.py

# Select asset from menu:
# [1] Asset 6A: Email Etiquette
# [2] Asset 6B: Idiom Translation
# [3] Asset 6C: Taboo Topics
# [4] Asset 6D: Regional Dialects
# [5] Asset 6E: German Idioms
# [6] Run All Assets
```

______________________________________________________________________

### **Running Tests (Programmatic)**

```python
from benchmark_modules.cultural_intelligence.test import CulturalIntelligenceTest

# Initialize test
test = CulturalIntelligenceTest()

# Load asset
asset = test.load_asset("cultural_intel_001")

# Generate LLM response
prompt = asset["prompt"]
response = your_llm_client.generate(prompt)

# Evaluate response
score, breakdown = test.evaluate(
    response=response,
    asset=asset,
    use_legacy=False  # Use v2.0 modular evaluators
)

print(f"Total Score: {score}/100")
print(f"Breakdown: {breakdown}")
```

**Output**:

```python
{
    "total_score": 82,
    "breakdown": {
        "german_proficiency": 28,  # out of 30
        "cultural_adaptation": 35,  # out of 40
        "solution_quality": 25,     # out of 30
        "regional_consistency": 10  # bonus
    },
    "details": {
        "formality_level": "formal (0.75)",
        "regional_variant": "consistent_de",
        "keywords_matched": ["Sie", "leider", "gerne", "Anfrage"],
        "idioms_detected": []
    }
}
```

______________________________________________________________________

## 🧪 **Testing & Validation**

### **Unit Tests**

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_legacy_compatibility.py -v

# Check coverage
pytest --cov=core --cov-report=html
```

______________________________________________________________________

### **Regression Tests**

**Purpose**: Ensure v2.0 modular evaluators produce scores ±5% of legacy scores.

```python
# tests/test_legacy_compatibility.py
def test_evaluator_parity():
    """Verify v2.0 scores match legacy within tolerance."""

    legacy_score = legacy_evaluator.evaluate(response, asset)
    modern_score = modern_evaluator.evaluate(response, asset)

    assert abs(legacy_score - modern_score) <= 5  # ±5% tolerance
```

______________________________________________________________________

### **Manual Testing Checklist**

- [ ] Asset 6A: Formality detection (Sie vs. Du)
- [ ] Asset 6B: Idiom translation (not literal)
- [ ] Asset 6C: Taboo handling (no stereotypes)
- [ ] Asset 6D: Regional consistency (no mixing)
- [ ] Asset 6E: German fluency (native-like)
- [ ] Score breakdown visible (per criterion)
- [ ] Legacy compatibility (±5% tolerance)

______________________________________________________________________

## 📊 **Performance Benchmarks**

### **Expected Scores by Model Tier**

| Model Tier | Expected Score | Strengths | Weaknesses |
|------------|---------------|-----------|------------|
| **Tier 1** (GPT-4, Claude Opus) | 85-95 | Excellent cultural nuance | Rare regional mixing |
| **Tier 2** (Mistral Large, Gemma 27B) | 70-85 | Good idioms, formality | Some literal translations |
| **Tier 3** (Qwen 14B, Llama 70B) | 60-75 | Decent grammar | Struggles with idioms |
| **Tier 4** (Small models \<10B) | 40-60 | Basic translation | Literal, no nuance |

______________________________________________________________________

### **Evaluation Speed**

- **Single asset**: ~2-5 seconds (depends on LLM API latency)
- **Full suite (5 assets)**: ~15-30 seconds
- **Bottleneck**: LLM generation time (95%), evaluation logic (5%)

______________________________________________________________________

## 🐛 **Known Issues & Limitations**

### **1. Subjectivity in Cultural Scoring**

**Issue**: Cultural "correctness" is subjective and context-dependent.

**Mitigation**: Use keyword proxies and sentiment analysis (not perfect, but consistent).

______________________________________________________________________

### **2. Regional Marker Database Incomplete**

**Issue**: Current database covers ~30 common terms (DE/AT/CH).

**Future Work**: Expand to 100+ terms, add pronunciation markers.

______________________________________________________________________

### **3. No Native Speaker Validation**

**Issue**: Scores are computed algorithmically, not validated by native speakers.

**Recommendation**: Use scores as relative ranking, not absolute quality.

______________________________________________________________________

## 🔄 **Migration Guide (v1.x → v2.0)**

### **Breaking Changes**

1. **Evaluator Import**: `LegacyEvaluator` moved to `core/legacy/`
1. **Asset Schema**: All assets now use LIST format (no DICT criteria)
1. **Score Breakdown**: Returns dict with per-criterion scores (not just total)

______________________________________________________________________

### **Backward Compatibility**

**Legacy evaluator still available**:

```python
from benchmark_modules.cultural_intelligence.core.legacy.evaluators import LegacyEvaluator

# Use old evaluator
legacy_evaluator = LegacyEvaluator()
score = legacy_evaluator.evaluate(response, asset)
```

**Modern evaluator (recommended)**:

```python
from benchmark_modules.cultural_intelligence.core.evaluators import CulturalIntelligenceEvaluator

# Use new modular evaluator
modern_evaluator = CulturalIntelligenceEvaluator()
score, breakdown = modern_evaluator.evaluate(response, asset)
```

______________________________________________________________________

### **Migration Steps**

1. **Update imports**: Replace `evaluators.py` → `core.evaluators`
1. **Update asset schemas**: Convert DICT criteria → LIST
1. **Update test code**: Handle score breakdown dict (not just int)
1. **Run regression tests**: Verify scores match legacy (±5%)
1. **Remove legacy code**: After validation, delete `core/legacy/`

______________________________________________________________________

## 🛠️ **Development**

### **Adding New Assets**

1. Create YAML file in `assets/`
1. Define prompt, expected output, criteria
1. Add keywords and weights
1. Register in `config.yaml`
1. Test with multiple models

**Template**:

```yaml
# assets/asset_6f_swiss_german.yaml
id: cultural_intel_006
name: "Swiss German Localization"
prompt: |
  Translate the following to Swiss German:
  "I'm going to the bakery to buy bread rolls for breakfast."

expected_output: |
  I gang zur Bäckerei, zum Brötli für s'Zmorge z'kaufe.

criteria:
  - name: swiss_german_proficiency
    weight: 40
    description: "Authentic Swiss German"

  - name: regional_consistency
    weight: 30
    description: "No mixing with Standard German"

  - name: solution_quality
    weight: 30
    description: "Complete translation"

keywords:
  - "Brötli"
  - "Zmorge"
  - "gang"
  - "zum"
  - "kaufe"

min_keywords: 3
total_points: 100
```

______________________________________________________________________

### **Adding New Evaluators**

1. Create evaluator in `core/evaluators/`
1. Inherit from base class (if exists)
1. Implement `evaluate(response, asset)` method
1. Register in Facade (`__init__.py`)
1. Add unit tests

**Example**:

```python
# core/evaluators/dialect_authenticator.py

class DialectAuthenticator:
    """Validates dialect authenticity (e.g., Bavarian, Swiss)."""

    DIALECT_MARKERS = {
        "bavarian": ["Griaß di", "Servus", "Oachkatzlschwoaf"],
        "swiss": ["Grüezi", "Merci vilmal", "Chuchichäschtli"]
    }

    def evaluate(self, response: str, expected_dialect: str) -> float:
        markers = self.DIALECT_MARKERS.get(expected_dialect, [])
        found = [m for m in markers if m.lower() in response.lower()]
        return (len(found) / len(markers)) * 100 if markers else 0
```

______________________________________________________________________

## 📝 **Changelog**

### **v2.0.1** (2026-02-02)

- **Fixed**: Asset 6E schema (DICT → LIST format)
- **Added**: `total_points` field to all assets
- **Improved**: Keyword extraction (configurable in YAML)
- **Updated**: README with comprehensive documentation

### **v2.0.0** (2026-02-01)

- **Major Refactor**: Modular evaluator architecture (Facade pattern)
- **Added**: Regional consistency validation
- **Added**: Continuous formality scoring (5-level scale)
- **Added**: Regression tests (legacy compatibility)
- **Improved**: Code maintainability (split 200-line file into 5 modules)

### **v1.0.0** (2025-12-15)

- Initial release with monolithic evaluator
- 3 assets: Email Etiquette, Idiom Translation, Taboo Check

______________________________________________________________________

## ⚠️ **Known Issues & Limitations**

### **Special Case: Asset 6E (German Idioms)**

**Status:** Uses `LegacyEvaluator` instead of v2.0 modular architecture.

**Why?**
Asset 6E requires **negative keyword checking**: verifying that English idioms are **removed** (not just translated).

**Example:**

```
❌ BAD: "The game plan went south" → "Der game plan ging schief"
         (English "game plan" still present!)

✅ GOOD: "The game plan went south" → "Der Plan ging schief"
         (English removed, German equivalent used)
```

The v2.0 `SolutionQualityEvaluator` currently only checks for **positive keywords** (German equivalents present), but lacks support for **negative keywords** (English removed).

**Impact:**

- ✅ **Stricter quality control** (catches literal translations)
- ✅ **Higher accuracy** (penalizes mixed-language responses)
- ⚠️ **Architectural inconsistency** (one asset uses different evaluator)

**Future Roadmap (v2.1):**

- Create specialized `IdiomReplacementEvaluator`
- Migrate Asset 6E to new evaluator
- Deprecate `LegacyEvaluator` (remove in v3.0)

**Configuration:**
The YAML schema is V2-compatible (uses Dict format), but scoring logic remains in `core/legacy/evaluators.py`. This is intentional.

______________________________________________________________________

## 📚 **References**

- **Hofstede's Cultural Dimensions**: https://www.hofstede-insights.com/
- **German Language Variants**: https://www.atlas-alltagssprache.de/
- **Politeness Theory (Brown & Levinson)**: https://doi.org/10.1017/CBO9780511813085

______________________________________________________________________

## 🤝 **Contributing**

Contributions welcome! Areas for improvement:

- [ ] Expand regional marker database (100+ terms)
- [ ] Add more languages (French, Spanish, Japanese)
- [ ] Implement sentiment analysis for politeness detection
- [ ] Add native speaker validation (human eval dataset)
- [ ] Create visual score reports (charts, heatmaps)

**Contact**: Open an issue or submit a PR on GitHub.

______________________________________________________________________

## 📄 **License**

This module is part of the **CrucibleMark** benchmark framework.\
License: MIT (see root LICENSE file)

______________________________________________________________________

**Version**: v2.0.1\
**Last Updated**: 2026-02-02\
**Maintainer**: CrucibleMark Development Team
