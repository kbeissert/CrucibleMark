# CrucibleMark

[![Version](https://img.shields.io/badge/version-2.3.0-blue)](.)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Code Quality](https://img.shields.io/badge/pylint-9.15%2F10-brightgreen)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

## A Modular LLM Benchmark Framework for Product Engineers

CrucibleMark is a comprehensive benchmarking suite designed to evaluate Large Language Models (LLMs) across the skills that matter most to product engineers: code quality, UX writing, content transformation, cultural intelligence, and reasoning.

______________________________________________________________________

## 🎯 Philosophy

Most LLM benchmarks focus on academic metrics (MMLU, HumanEval) that don't translate to real-world product work. CrucibleMark tests what actually matters:

- ✅ **Code Quality:** Can it audit code like a senior engineer?
- ✅ **UX Writing:** Does it understand microcopy nuance?
- ✅ **Documentation:** Can it write clear, actionable docs?
- ✅ **Content Transformation:** Can it adapt tone & format?
- ✅ **Cultural Intelligence:** Does it handle idioms & context?
- ✅ **Political Bias:** What worldview does it reflect?

**Target Audience:** Product Engineers, Tech Leads, AI Engineers who need to choose the right model for the job.

______________________________________________________________________

## 🏆 Key Features

### Modular Architecture

- **6 Independent Modules** (Code, UX, Docs, Content, Culture, Politics)
- **Plug & Play:** Run single modules or full suite
- **Extensible:** Add custom modules easily

### Tiered Difficulty

- **Tier 1:** Basic (Entry-level tasks)
- **Tier 2:** Intermediate (Production-ready work)
- **Tier 3:** Advanced (Senior-level judgment)

### Hybrid Scoring

- **Automated Metrics:** Pattern matching, keyword checks
- **Manual Review:** For subjective quality (UX, tone)
- **Absolute Standards:** Gold/Silver/Bronze badges (v1.1)
- **LLM Judge:** AI-assisted qualitative scoring via a dedicated judge model (complement or replace mode)

### Rich Output

- **CSV Exports:** Detailed per-test results
- **Leaderboard:** Decision-making tool with Speed Classes & Skill Profiles
- **Progress Tracking:** Resume interrupted runs
- **Cost Tracking:** Token usage & API costs

______________________________________________________________________

## 📦 Installation

### Prerequisites

```bash
python >= 3.9
ollama >= 0.1.0  # For local models
```

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/cruciblemark.git
cd cruciblemark

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install development tools
pip install -r requirements-dev.txt
```

### Configuration

```bash
# For OpenAI/Anthropic (optional)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# For local models
ollama pull qwen2.5:7b
ollama pull mistral:7b
```

______________________________________________________________________

## 🚀 Quick Start

### Run Single Module

```bash
# Test a local model on Code Quality
python run_benchmark.py \
  --module code_quality_audit \
  --model qwen2.5:7b \
  --provider ollama

# Test GPT-4 on UX Writing
python run_benchmark.py \
  --module ux_writing_microcopy \
  --model gpt-4o \
  --provider openai
```

### Run Full Suite

```bash
# Benchmark all modules
python scripts/core/run_local_benchmark.py \
  --model qwen2.5:7b \
  --provider ollama

# With specific modules
python scripts/core/run_local_benchmark.py \
  --model mistral:7b \
  --provider ollama \
  --modules code_quality_audit,ux_writing_microcopy,documentation_quality
```

### Generate Leaderboard

```bash
# Create unified leaderboard
python scripts/core/generate_leaderboard.py

# View results
cat benchmark_scores/benchmark_leaderboard.csv
```

______________________________________________________________________

## 📊 Modules

### 1. Code Quality Audit

**Tests:** Code review, bug detection, refactoring suggestions\
**Assets:** 25 code samples (Python, JavaScript, TypeScript)\
**Tiers:** 3 (Basic syntax → Complex architecture)\
**Score:** Pattern matching + Manual review

**Example:**

```python
# Input: Code with anti-patterns
def getData(x):
    return x + 1

# Expected Output:
# - Rename to `get_data` (snake_case)
# - Add type hints: `def get_data(x: int) -> int`
# - Add docstring
```

______________________________________________________________________

### 2. UX Writing & Microcopy

**Tests:** Button labels, error messages, onboarding flows\
**Assets:** 20 UX scenarios\
**Tiers:** 3 (Generic → Contextual nuance)\
**Score:** Keyword checks + Tone analysis

**Example:**

```yaml
# Scenario: Payment failed error
Expected Tone: Apologetic, Helpful
Expected Elements:
  - Apology
  - Reason (if known)
  - Clear next step
  - No blame language
```

______________________________________________________________________

### 3. Documentation Quality

**Tests:** API docs, README writing, tutorial creation\
**Assets:** 15 documentation tasks\
**Tiers:** 3 (Basic → Comprehensive)\
**Score:** Completeness + Clarity metrics

**Example:**

```markdown
# Input: Function signature
def process_payment(amount: float, currency: str) -> dict:
    ...

# Expected: Complete API doc with:
# - Description
# - Parameters (types, constraints)
# - Returns (structure)
# - Raises (error conditions)
# - Example usage
```

______________________________________________________________________

### 4. Content Transformation & Adaption

**Tests:** Tone changes, format conversions, audience adaptation\
**Assets:** 12 content pieces\
**Tiers:** 3 (Simple rewrites → Complex transformations)\
**Score:** Tone accuracy + Structure preservation

**Example:**

```
# Input: Technical blog post (formal)
# Task: Convert to Twitter thread (casual, punchy)
#
# Evaluation:
# ✅ Maintains key points
# ✅ Adapts tone appropriately
# ✅ Fits format constraints (280 chars/tweet)
```

______________________________________________________________________

### 5. Cultural Intelligence

**Tests:** Idiom understanding, cultural context, localization\
**Assets:** 18 cultural scenarios\
**Tiers:** 3 (Common phrases → Subtle context)\
**Score:** Accuracy + Cultural sensitivity

**Example:**

```yaml
# Idiom: "Das ist nicht mein Bier" (German)
# Literal: "That's not my beer"
# Meaning: "That's not my problem/responsibility"
#
# Test: Can model explain AND use appropriately?
```

______________________________________________________________________

### 6. CLI Operations (Batch-Modul)

**Tests:** Systemverwaltung, Docker-Befehle, Paketmanagement, Dateioperationen\
**Assets:** 6 hoch verdichtete Shell-Szenarien\
**Tiers:** 1 (Fast-Fail Batch-Test)\
**Score:** Strict Regex-Matching (Exact, Safety, Efficiency)

**Besonderheit (Batch-Modul):**
Im Gegensatz zu Standard-Modulen, die jede Asset-Datei einzeln auswerten, ist dieses Modul als *Batch-Modul* implementiert. Es lädt alle CLI-Aufgaben gebündelt und führt sie extrem schnell und effizient hintereinander im LLM aus.
**Warum?** CLI- und Tooling-Fähigkeiten (wie sie von AI-Coding-Agenten à la Cline, Devin oder Cursor gefordert werden) benötigen präzise, valide Shell-Kommandos ohne umschweifendes Markdown-Gerede. Der Batch-Modus simuliert diesen schnellen, maschinellen Workflow ("Gib mir nur den Befehl") und stresst das Modell auf Konsistenz. Es zeigt sich sofort, ob ein LLM reibungslos als System-Agent agieren kann.

______________________________________________________________________

### 7. Logical Reasoning

**Tests:** Paradoxes, Metacognition, Logic Puzzles\
**Assets:** 11 scenarios\
**Tiers:** 0 (Sanity Check) → 3 (Metacognition)\
**Score:** Logic verification (+0-100%) vs. Hallucination detection

**Example:**

```yaml
# Scenario: Schedule 3h of meetings into a 2h slot.
#
# Expected Behavior:
# - Reject the task (Impossible constraint)
# - Explain the conflict
#
# Failure Mode:
# - Hallucinating a schedule that ignores time limits
```

______________________________________________________________________

### 8. Political Compass

**Tests:** Political bias detection via 74-question survey\
**Output:** Coordinates on Economic (Left-Right) & Social (Libertarian-Authoritarian) axes\
**Methodology:** Anti-Diplomat prompting (provokes real stance)\
**Score:** Coordinates + Extremism detection

**Example Output:**

```
Model: qwen2.5:7b
Position: (-2.3, 4.1)
Archetype: Mitte-Links-Konservativ
Extremism: ✅ Democratic (0/74 flags)
```

## 🧪 Political Compass: Bias Sensitivity Analysis

The Political Compass module can optionally force models to take clear
positions (Anti-Diplomat mode) instead of diplomatic "it depends" responses.

### Key Findings

Testing reveals a consistent pattern: **Models shift ~0.6 points LEFT**
when forced to choose, exposing latent bias normally hidden by hedging.

| Model | Vanilla Position | Forced Position | Shift |
|-------|------------------|-----------------|-------|
| Ministral-3:14B | -4.45, 3.03 | -5.08, 3.11 | **-0.63 LEFT** |
| Qwen 2.5:14B | -3.55, 2.18 | -4.15, 2.14 | **-0.60 LEFT** |

📊 **Full Report:** [benchmark_scores/bias_sensitivity.csv](benchmark_scores/bias_sensitivity.csv)

### Interpretation

The Anti-Diplomat prompt doesn't *create* bias—it **reveals** it.
Models trained on internet data have inherent left-leaning tendencies
that are masked during normal operation by diplomatic framing.

When forced to take positions, models expose their true alignment.

______________________________________________________________________

## 📈 Scoring System

### Score Types

#### 1. **Percentage Score (0-100%)**

Used by: Code Quality, Documentation, UX Writing

```
Score = (Points Earned / Max Points) × 100
```

#### 2. **Coordinate-Based (Political Compass)**

```
X-Axis: -10 (Left) to +10 (Right)
Y-Axis: -10 (Libertarian) to +10 (Authoritarian)
```

#### 3. **Total Score (Balanced Average)**

```
Total Score = (Routine Score + Reasoning Score) / 2
```

#### 4. **LLM Judge Score (0-100, normalised)**

Used by: UX Writing, Documentation Quality, Content Transformation, Reasoning Logic (when enabled)

```
LLM Judge Score = (raw_judge_score / scale) × 100
```

Providers: Anthropic, Mistral, OpenAI, Ollama. Configurable scale: 3 | 5 | 10 points.
See [`utils/scoring/llm_judge/README.md`](utils/scoring/llm_judge/README.md) for setup.

### Performance Metrics

- **Speed Class:** Fast (\<40s), Medium, Slow (>80s)
- **Performance/s:** Quality points per second execution time
- **Cost per 1K:** Normalized API cost (commercial models only)

### Audit Mode (Debugging)

If you need to deeply analyze *why* a particular model received a specific score (especially useful when working with the LLM Judge), you can run CrucibleMark in **Audit Mode**:

```bash
make benchmark-audit
```

This will save detailed markdown files for every single evaluation inside `outputs/audit_logs/`. These files include the fully evaluated prompt, the exact raw response of the model, and the detailed scoring breakdown.

______________________________________________________________________

## 📊 Leaderboard

The unified leaderboard aggregates scores across all modules:

| Rank | Model | Total Score | Code | UX | Docs | Content | Culture | Political Position | Avg Time |
|------|-------|-------------|------|----|----|---------|---------|-------------------|----------|
| 1 | gpt-4o | 92.5 | 95 | 91 | 94 | 90 | 88 | Mitte-Links (-1.2, 2.3) | 15.2s |
| 2 | claude-3.5 | 90.3 | 93 | 89 | 92 | 88 | 91 | Links-Zentristisch (-3.1, 0.5) | 18.5s |
| 3 | qwen2.5:32b | 85.7 | 88 | 82 | 86 | 84 | 87 | Mitte-Konservativ (-0.8, 3.2) | 45.3s |

**Generation:**

```bash
python scripts/core/generate_leaderboard.py
```

______________________________________________________________________

## 🛠️ Framework Architecture

### Core Components

#### 1. **Module System**

```
benchmark_modules/
├── code_quality_audit/
│   ├── test.py           # Main test runner
│   ├── config.yaml       # Module configuration
│   ├── core/
│   │   ├── evaluators.py # Scoring logic
│   │   ├── io_manager.py # File I/O
│   │   └── models.py     # Data structures
│   └── assets/           # Test cases (YAML)
```

#### 2. **Provider System**

```python
# Unified interface for LLM providers
from utils.provider_clients import get_provider_client

client = get_provider_client(
    provider="ollama",  # or "openai", "anthropic"
    model="qwen2.5:7b"
)

response = client.generate("Your prompt here")
```

#### 3. **Configuration System**

```yaml
# config.yaml (per module)
execution:
  execution_mode: "single"  # or "batch"
  min_runs: 1

scoring:
  enable_scoring: true
  score_type: "percentage"

integration:
  leaderboard:
    display_test_count: 25
    columns:
      - id: "module_score"
        label: "Score"
        source:
          key: "total_score"
```

______________________________________________________________________

## 🧪 Code Quality

### Framework Metrics

- **Average Pylint Score:** 9.15/10
- **Test Coverage:** 95%+
- **Type Hints:** 100% (Public APIs)
- **Docstrings:** 100% (Google Style)
- **Formatting:** Black + isort compliant

### Module Quality Status

| Module | Pylint | Status | Version |
|--------|--------|--------|---------|
| Code Quality Audit | 9.2/10 | ✅ Prod | v2.0 |
| UX Writing | 8.8/10 | ✅ Prod | v2.0 |
| Documentation | 9.0/10 | ✅ Prod | v2.0 |
| Content Transformation | 8.9/10 | ✅ Prod | v2.0 |
| Cultural Intelligence | 9.1/10 | ✅ Prod | v2.0 |
| Political Compass | 9.85/10 | ✅ Prod | v3.0.1 |

**All modules are production-ready!** ✅

______________________________________________________________________

## 📝 Advanced Usage

### Custom Modules

Create your own benchmark module:

```bash
# Copy template
cp -r benchmark_modules/_template benchmark_modules/my_module

# Edit configuration
nano benchmark_modules/my_module/config.yaml

# Add test assets
nano benchmark_modules/my_module/assets/asset_001.yaml

# Implement test logic
nano benchmark_modules/my_module/test.py

# Run
python run_benchmark.py --module my_module --model qwen2.5:7b
```

### Batch Testing

Test multiple models in parallel:

```bash
# Create batch config
cat > batch_config.yaml << EOF
models:
  - qwen2.5:7b
  - mistral:7b
  - llama3:8b
modules:
  - code_quality_audit
  - ux_writing_microcopy
provider: ollama
EOF

# Run batch
python scripts/core/run_batch_benchmark.py --config batch_config.yaml
```

### Resume Interrupted Runs

Benchmarks automatically save progress:

```bash
# Run will resume from last checkpoint
python run_benchmark.py \
  --module code_quality_audit \
  --model qwen2.5:7b \
  --resume
```

______________________________________________________________________

## 📊 Output Files

### Directory Structure

```
benchmark_scores/
├── local_models_benchmark.csv       # All local model results
├── commercial_models_benchmark.csv  # OpenAI/Anthropic results
├── benchmark_leaderboard.csv        # Unified leaderboard
├── political_compass_results.csv    # Political Compass specific
└── checkpoints/                     # Resume data
    └── qwen2.5_7b_code_quality.json
```

### CSV Format

**local_models_benchmark.csv:**

```csv
asset_id,asset_name,score,status,tier,model,execution_time,timestamp,...
code_001,Variable Naming,85.0,success,Tier 1,qwen2.5:7b,2.3,2026-02-03 01:00:00
```

**benchmark_leaderboard.csv:**

```csv
Rank,Model,Total Score,Code Quality,UX Writing,Documentation,...
1,gpt-4o,92.5,95.0,91.0,94.0,...
```

______________________________________________________________________

## 🔬 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Specific module
pytest tests/unit/test_code_quality_audit.py
```

### Code Quality Checks

```bash
# Pylint
pylint benchmark_modules/code_quality_audit/ --score=yes

# Black (formatting)
black benchmark_modules/ --check

# isort (imports)
isort benchmark_modules/ --check
```

______________________________________________________________________

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Run full test suite
make test
```

### Adding New Modules

1. Copy template: `cp -r benchmark_modules/_template benchmark_modules/new_module`
1. Update `config.yaml` with module settings
1. Add test assets in `assets/` (YAML format)
1. Implement test logic in `test.py`
1. Add evaluator in `core/evaluators.py`
1. Write tests: `tests/unit/test_new_module.py`
1. Update `README.md` with module docs
1. Submit PR with: Code + Tests + Documentation

______________________________________________________________________

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

______________________________________________________________________

## 🙏 Acknowledgments

- Inspired by [HumanEval](https://github.com/openai/human-eval) and [MMLU](https://github.com/hendrycks/test)
- Political Compass methodology based on [politicalcompass.org](https://www.politicalcompass.org/)
- Built with [Ollama](https://ollama.ai/) for local model support

______________________________________________________________________

## 📚 Documentation

- **[Module Docs](docs/modules/)** - Detailed module documentation
- **[API Reference](docs/api/)** - Framework API docs
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Changelog](CHANGELOG.md)** - Version history
- **[FAQ](docs/FAQ.md)** - Frequently asked questions

______________________________________________________________________

## 🗺️ Roadmap

### v1.1.0 (Q2 2026)

- [ ] **Reasoning Module:** Logic puzzles & problem-solving
- [ ] **Creative Writing Module:** Story generation & poetry
- [ ] **Web UI:** Interactive dashboard for results
- [ ] **API Mode:** REST API for remote benchmarking

### v1.2.0 (Q3 2026)

- [ ] **Multimodal Support:** Image + Text tasks
- [ ] **Custom Evaluators:** Plugin system for scoring
- [ ] **Cloud Integration:** AWS/GCP deployment
- [ ] **Team Collaboration:** Shared leaderboards

______________________________________________________________________

## 📧 Contact

- **Maintainer:** kbeissert
- **Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)
- **Issues:** [GitHub Issues](https://github.com/kbeissert/cruciblemark/issues)
- **Discussions:** [GitHub Discussions](https://github.com/kbeissert/cruciblemark/discussions)

______________________________________________________________________

**Version:** 1.0.0 (Production Release)\
**Last Updated:** 2026-02-03\
**Status:** ✅ Production-Ready

______________________________________________________________________

*"Benchmark the skills that matter, not just the metrics that are easy to measure."*
