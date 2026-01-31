# CrucibleMark Framework: System Architecture Documentation
**Version:** 0.5.0-beta  
**Document Type:** Technical Architecture Overview  
**Last Updated:** 2026-01-31  
**Status:** Pre-Release Consolidation Phase

---

## Executive Summary

CrucibleMark is a **modular LLM benchmarking framework** designed for product engineers, UX writers, and system architects. Unlike generic academic benchmarks (MMLU, HumanEval), it evaluates models on **production-relevant capabilities**: code quality audits, UX microcopy, technical documentation, reasoning under constraints, and cultural intelligence.

The system follows a **plugin-based architecture** where benchmark modules are decoupled from the core framework through configuration contracts. This document maps the current implementation state at the conceptual level, serving as a foundation for detailed technical specifications.

---

## System Architecture Layers

### Layer 1: Framework Core
The invariant orchestration engine that coordinates benchmark execution across all modules.

#### Components
- **Benchmark Orchestrator** (`crucible_mark.py` / `make benchmark`)
  - Entry point for all benchmark runs
  - Reads `benchmark_config.yaml` to determine active modules
  - Manages execution flow (sequential/parallel)
  - Handles model provider abstraction (Ollama, OpenAI, Mistral API)
  - Implements rate limiting and retry logic

- **Configuration Management**
  - `benchmark_config.yaml`: Master registry of active modules
  - `config_local.yaml`: Environment-specific paths and API keys
  - `.env`: Sensitive credentials (API tokens, endpoints)
  - Config parser validates module metadata and dependency graphs

- **Model Provider Abstraction**
  - Unified interface for local (Ollama) and commercial (OpenAI, Mistral) models
  - Provider-specific adapters handle authentication, token limits, streaming
  - Model registry with ping tests (`make list-models`)

#### Key Characteristics
- **Technology-agnostic**: Modules don't know if they're testing Ollama or GPT-4
- **Stateless**: Each benchmark run is independent (no cross-run state pollution)
- **Reproducible**: Fixed seeds + deterministic prompts ensure comparability

---

### Layer 2: Benchmark Modules
Self-contained test suites that implement domain-specific evaluation logic.

#### Module Anatomy
Each module follows a standardized directory structure:

```
benchmark_modules/
├── {module_id}/
│   ├── README.md              # Human-readable documentation
│   ├── module_meta.json       # Machine-readable contract (see below)
│   ├── assets/                # Test fixtures (code samples, prompts, golden standards)
│   │   ├── {asset_id}_input.{ext}
│   │   └── {asset_id}_golden.{ext}
│   ├── prompts/               # Structured prompt templates
│   │   └── {tier}_template.txt
│   ├── scoring/               # Evaluation logic
│   │   ├── regex_patterns.py  # Pattern-based scoring (current)
│   │   └── llm_scorer.py      # LLM-based scoring (planned)
│   └── runner.py              # Module execution entry point
```

#### Module Contract (`module_meta.json`)
Defines how the framework should integrate the module:

```json
{
  "module_id": "code_quality",
  "display_name": "Code Quality Audit",
  "leaderboard_columns": [
    {"id": "code_quality_score", "label": "Code Quality", "weight": 1.0}
  ],
  "contributes_to": {
    "routine_score": true,    // Affects "Daily Driver" badge
    "reasoning_score": false
  },
  "tier_system": "tiered_difficulty",  // or "binary", "continuous"
  "output_schema": {
    "total_score": "float",
    "execution_time": "float",
    "tier_breakdown": "dict"
  }
}
```

**Critical Invariant:** The framework **never hardcodes module names**. All module discovery happens via config parsing.

#### Currently Implemented Modules

| Module ID | Domain | Tier System | Scoring Method |
|-----------|--------|-------------|----------------|
| `code_quality` | Static analysis (WCAG, security, performance) | 4-tier difficulty | Regex + keyword matching |
| `ux_writing` | Microcopy, accessibility labels, CTAs | 4-tier difficulty | Regex + semantic similarity |
| `documentation_quality` | README, API docs, changelogs | 4-tier difficulty | Hybrid (structure + content) |
| `content_transformation` | Format/tone adaptation | 2-tier (technical vs. creative) | Template conformance |
| `reasoning_logic` | Logic puzzles, deadlock detection | 2-tier (operational vs. deep) | Exact match + pattern recognition |
| `political_compass` | Ideological bias detection | Single-run | Coordinate-based scoring |

---

### Layer 3: Scoring & Evaluation Subsystem
Converts raw model outputs into comparable metrics.

#### Current State: Regex-Based Scoring
- **Mechanism:** Each module defines keyword/pattern lists that match expected outputs
- **Strengths:** Fast, deterministic, no API dependencies
- **Weaknesses:** Brittle across model output formats (e.g., GPT uses lists, Llama uses paragraphs)

**Critical Pain Point (Trigger for Dual-Scorer Plan):**  
When testing `qwen2.5:32b` vs `mistral-large`, identical logical answers get different scores because output formatting differs. Example:

```
Qwen:   "Error 1: Missing alt attribute (line 42)"
Mistral: "1. Accessibility issue: alt attribute missing at line 42"
```

Regex `r"Missing alt"` matches Qwen but not Mistral → False negative.

#### Planned State: Dual-Tier Scoring
**Tier 1 (Structural Validator):**  
- LLM-based pattern recognition (e.g., Claude Haiku, GPT-4o-mini)
- Validates **semantic intent** regardless of formatting
- Example: "Did the model identify the missing `alt` attribute?" → Yes/No

**Tier 2 (Deep Evaluator):**  
- Specialized reasoning model (Phi-3, DeepSeek-R1)
- Evaluates **quality of explanation** and **reasoning depth**
- Example: "Did the model explain *why* missing `alt` violates WCAG 2.2?"

**Hybrid Score Formula:**
```
Final Score = (Tier1_Accuracy * 0.6) + (Tier2_Quality * 0.4)
```

---

### Layer 4: Results Aggregation & Leaderboard Generation
Transforms per-module scores into comparative rankings.

#### Data Flow

1. **Benchmark Execution** → Generates per-model CSV files:
   ```
   results/
   ├── {model_name}/
   │   ├── code_quality_results.csv
   │   ├── ux_writing_results.csv
   │   └── reasoning_results.csv
   ```

2. **Score Aggregator** (`scripts/generate_leaderboard.py`):
   - Reads `benchmark_config.yaml` to identify active modules
   - Merges per-module CSVs into unified dataset
   - Calculates meta-scores:
     - **Routine Score** = Weighted avg of modules where `contributes_to.routine_score == true`
     - **Reasoning Score** = Weighted avg of modules where `contributes_to.reasoning_score == true`
   - Assigns badges based on thresholds:
     - 👑 God Mode: Routine >85% AND Reasoning >80%
     - 🏎️ Daily Driver: Routine >80%
     - 🧠 Deep Thinker: Reasoning >80%

3. **Leaderboard CSV** (`benchmark_leaderboard.csv`):
   - Dynamic column generation based on active modules
   - One row per model with:
     - Total Score (0-100)
     - Per-module scores
     - Execution time
     - Badge
     - Political compass coordinates (if `political_compass` module active)

#### Configuration-Driven Column Mapping
**Current Challenge (Unverified):**  
The leaderboard generator must dynamically build columns based on `benchmark_config.yaml`. If a module is commented out, its column should disappear.

**Expected Behavior (To Be Tested in Phase 1):**
```yaml
# benchmark_config.yaml
active_modules:
  - code_quality     # → Adds "Code Quality" column
  # - ux_writing     # → No "UX Writing" column
  - reasoning_logic  # → Adds "Reasoning" column
```

→ Leaderboard should have exactly 2 module columns (Code Quality + Reasoning).

---

### Layer 5: Backup & Cache Management
Prevents data loss and manages storage overhead.

#### Backup System (`scripts/backup_results.py`)
**Trigger:** After each full benchmark cycle  
**Actions:**
1. Compress all CSVs (results, leaderboards, cache) → `backups/{timestamp}.tar.gz`
2. Move compressed archive to `backups/` directory
3. Prune cache files:
   - Keep only **last run** per model (delete older cache entries)
   - Rationale: Cache files enable incremental benchmarks (resume from last asset)

#### Cache Logic
Each module maintains a cache of completed assets:
```
results/{model_name}/_cache/
└── {module_id}_cache.json
```

**Purpose:** If a benchmark crashes mid-run, next execution skips already-tested assets.

**Risk (Untested):**  
If `benchmark_config.yaml` removes a module mid-campaign, orphaned cache files may accumulate. Backup script should detect and clean these.

---

## Cross-Cutting Concerns

### Modular Extensibility Contract
**Question:** Can a developer add a new module without modifying framework code?  
**Answer (Intended Design):** Yes, via this workflow:

1. Create `benchmark_modules/new_module/` with required files
2. Add `new_module` to `benchmark_config.yaml`
3. Framework auto-discovers module via config parser
4. Leaderboard generator reads `module_meta.json` to create column

**Verification Gap:** This has never been tested in isolation (Phase 1 goal).

---

### Reproducibility Guarantees
- **Deterministic Prompts:** All templates use fixed seeds
- **Rate Limit Handling:** Exponential backoff prevents API-side variations
- **Golden Standards:** Reference outputs (`_golden.json`) anchor scoring

**Known Non-Determinism:**  
Commercial models (GPT-4, Mistral) have server-side temperature. Even with `temperature=0.1`, consecutive runs may differ by ±2%.

---

### Provider-Specific Quirks
| Provider | Authentication | Token Limit | Streaming | Retry Logic |
|----------|---------------|-------------|-----------|-------------|
| Ollama   | None (localhost) | Model-dependent (8K-128K) | Yes | N/A (local) |
| OpenAI   | Bearer token | 128K (GPT-4) | Yes | 429 → exponential backoff |
| Mistral  | API key | 32K | No | 500 → retry 3x |

---

## Data Schemas

### Benchmark Results CSV
```csv
asset_id, model, tier, total_score, execution_time, error_detection, solution_quality, timestamp
code_quality_001, qwen2.5:32b, Tier 1, 85.0, 12.4, 60.0/60, 25.0/30, 2026-01-31T10:00:00
```

### Leaderboard CSV
```csv
Rank, Model, Total Score, Routine Score, Reasoning Score, Badge, Code Quality, UX Writing, Reasoning
1, mistral-medium-latest, 82.88, 83.68, 77.92, 🏎️, 85.2, 88.6, 77.94
```

### Module Metadata JSON
```json
{
  "module_id": "reasoning_logic",
  "leaderboard_columns": [
    {"id": "reasoning_score", "label": "Logical Reasoning", "weight": 2.0}
  ],
  "contributes_to": {
    "routine_score": false,
    "reasoning_score": true
  }
}
```

---

## Known Technical Debt

### Category: Untested Assumptions
1. **Single-Module Isolation:** Does the framework work if only 1 module is active?
2. **Column Pruning:** Does leaderboard correctly omit deactivated modules?
3. **Cache Orphans:** Are cache files cleaned when modules are removed?

### Category: Code Smells
1. **Duplicated Config Parsing:** Multiple scripts (`generate_leaderboard.py`, `backup_results.py`) re-parse `benchmark_config.yaml`
2. **Hardcoded Paths:** Some scripts reference `results/` instead of reading from `config_local.yaml`
3. **Inconsistent Error Handling:** Ollama failures crash the script; API failures retry

### Category: Missing Features
1. **No Rollback Mechanism:** If a backup is corrupt, no way to restore previous state
2. **No Incremental Leaderboard:** Must re-run all models to update leaderboard
3. **No Diff Reports:** Can't compare two benchmark runs (e.g., "Did Qwen improve after fine-tuning?")

---

## Proposed Consolidation Roadmap

### Phase 1: Framework Validation (Current Focus)
**Goal:** Verify the modular contract works as intended.

**Tasks:**
1. Test single-module execution (comment out all but one module in config)
2. Verify leaderboard generates only active module columns
3. Confirm backup script handles orphaned cache files
4. Document discovered edge cases

**Success Criteria:**
- Framework runs with 1-6 modules without code changes
- Leaderboard CSV matches active module count
- Backup archives contain expected files

---

### Phase 2: Code Hygiene
**Goal:** Eliminate duplication and standardize patterns.

**Tasks:**
1. Centralize config parsing into `core/config_manager.py`
2. Replace hardcoded paths with config lookups
3. Merge fragmented utility scripts (CSV writers, logger setup)
4. Add type hints and docstrings

**Success Criteria:**
- Config parsing logic exists in ONE place
- No script reads `.yaml` directly
- `mypy --strict` passes

---

### Phase 3: Documentation Freeze
**Goal:** Create contracts for future development.

**Deliverables:**
1. `ARCHITECTURE.md`: Detailed design patterns
2. `ADDING_MODULES.md`: Step-by-step guide for contributors
3. `MODULE_CONTRACT_SPEC.md`: JSON schema for `module_meta.json`

**Success Criteria:**
- A developer can add a module using only documentation (no codebase inspection)

---

### Phase 4: Dual-Scorer Integration (Post-Consolidation)
**Goal:** Replace regex scoring with LLM-based evaluation.

**Design:**
- New `scoring/llm_tier1_validator.py` module
- Backwards-compatible: Old modules keep regex until migrated
- Config flag: `"scoring_method": "regex" | "llm_tier1" | "hybrid"`

---

## Appendix: Module-Specific Implementation Notes

### `code_quality` Module
- **Assets:** Deliberately flawed code snippets (WCAG violations, SQL injection risks)
- **Tier Breakdown:**
  - Tier 1 (Labeled): Errors marked with comments
  - Tier 2 (Standard): Obvious issues (missing `alt`, hardcoded secrets)
  - Tier 3 (Advanced): Subtle bugs (race conditions, memory leaks)
  - Tier 4 (Expert): Architectural flaws (N+1 queries, deadlocks)

### `reasoning_logic` Module
- **Unique Constraint:** Tier 2 assets have **no correct answer** (e.g., scheduling paradox)
- **Scoring:** Models get points for *identifying* impossibility, not solving

### `political_compass` Module
- **Output:** X/Y coordinates + extremism warning
- **Non-Competitive:** Doesn't contribute to Routine/Reasoning scores
- **Purpose:** Detect ideological drift in fine-tuned models

---

## Glossary

| Term | Definition |
|------|------------|
| **Routine Score** | Aggregate performance on standard tasks (code linting, typo detection) |
| **Reasoning Score** | Aggregate performance on complex logic (deadlock detection, constraint solving) |
| **Golden Standard** | Reference output used to calculate semantic similarity scores |
| **Tier System** | Difficulty classification (e.g., Tier 1 = Junior-level, Tier 4 = Expert-level) |
| **Module Contract** | JSON schema defining framework-module interface |
| **Badge** | Gamified classification (God Mode, Daily Driver, Deep Thinker, Needs Tuning) |

---

## Document Maintenance

This document represents the **conceptual architecture** as of January 2026. It intentionally omits implementation details (class names, function signatures) to focus on system design.

**Update Triggers:**
- New module added → Update Layer 2 table
- Scoring system changed → Update Layer 3
- Config schema modified → Update module contract spec

**Contact:**  
For clarifications or proposed amendments, refer to `PROJECT_STATUS.md` or raise an issue in the repository.

---

**End of Document**
