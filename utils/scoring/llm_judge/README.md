# LLM Judge

> **Technical Metadata**
>
> - **Namespace:** `utils.scoring.llm_judge`
> - **Type:** Alternative / Complementary Scorer
> - **Version:** v1.0.0
> - **Applicable Modules:** `ux_writing`, `documentation_quality`, `content_transformation`, `reasoning_logic`

---

## What It Is

The **LLM Judge** is a self-contained scoring extension for CrucibleMark. It replaces or complements the existing Hybrid Scorer (Keyword/Regex + Semantic Similarity) for benchmark modules where qualitative assessment is more reliable than rule-based matching.

A judge model (e.g. Claude Haiku, Mistral Small, or a local Ollama model) receives the original task prompt, the model's response, and a golden standard. It reasons step-by-step — following Chain-of-Thought principles — and returns a structured score with reasoning. The score is added to the benchmark result without changing the existing scoring pipeline.

> **💡 Tip: Debugging with Audit Mode**  
> If you want to see exactly how the LLM Judge arrived at its score, including its full CoT reasoning, run the benchmarker with `make benchmark-audit`. See the [Audit Mode documentation](../../../docs/USER_GUIDE.md#3-audit-mode-log-protokoll) for details.

---

## Architecture Overview

```
utils/scoring/llm_judge/
├── __init__.py               Public API: JudgeRunner, LLMJudgeConfig, JudgeResult
├── judge_runner.py           Orchestrator: wires provider → prompt → parse → result
├── judge_prompt_builder.py   Builds system + user prompts (CoT, rubric injection)
├── judge_parser.py           Parses raw LLM output → typed JudgeResult dataclass
├── judge_config.py           Pydantic config model (all defaults live here)
├── config.example.yaml       Documented example configuration
├── providers/
│   ├── __init__.py           Exposes LLMJudgeProvider, JudgeProviderResponse
│   ├── base_provider.py      Abstract base class: LLMJudgeProvider
│   ├── anthropic_provider.py Anthropic API (claude-haiku-4-5 default)
│   ├── mistral_provider.py   Mistral AI API (mistral-small-latest default)
│   ├── openai_provider.py    OpenAI API (gpt-4o-mini default)
│   └── ollama_provider.py    Local models via Ollama REST API
└── tests/
    ├── test_judge_parser.py  Unit tests (happy path, edge cases, word scores, …)
    └── test_judge_integration.py  Integration tests with mocked provider
```

---

## Configuration Guide

Copy `config.example.yaml` to your config directory and adjust as needed. Load it with:

```python
import yaml
from utils.scoring.llm_judge import JudgeRunner, LLMJudgeConfig

raw = yaml.safe_load(open("path/to/config.yaml"))
config = LLMJudgeConfig.from_dict(raw)
runner = JudgeRunner(config)
```

### Key Reference

| Key | Type | Default | Description |
|---|---|---|---|
| `llm_judge.enabled` | bool | `true` | Master switch. Set `false` to bypass the judge. |
| `llm_judge.mode` | str | `complement` | `complement` – both scorers run, judge score stored in `data["llm_judge"]`. `replace` – judge replaces hybrid scorer for applicable modules. |
| `llm_judge.provider.name` | str | `anthropic` | Provider: `anthropic` \| `mistral` \| `ollama` \| `openai` |
| `llm_judge.provider.model` | str | `claude-haiku-4-5` | Model ID / tag. |
| `llm_judge.provider.temperature` | float | `0.1` | Low temperature → deterministic scores. |
| `llm_judge.provider.max_tokens` | int | `1024` | Max tokens in the judge response. |
| `llm_judge.provider.timeout_seconds` | int | `30` | HTTP timeout. |
| `llm_judge.provider.base_url` | str | `null` | Ollama only: `http://localhost:11434` |
| `llm_judge.scoring.scale` | int | `5` | Point scale: `3`, `5`, or `10`. |
| `llm_judge.scoring.require_reasoning` | bool | `true` | Judge must emit `REASONING:` before `SCORE:`. |
| `llm_judge.scoring.fail_on_parse_error` | bool | `false` | Raise on parse failure instead of returning `score=None`. |
| `llm_judge.applicable_modules` | list | see below | Module IDs where the judge is activated. |

Default `applicable_modules`: `ux_writing`, `documentation_quality`, `content_transformation`, `reasoning_logic`.
`code_quality` is intentionally excluded: rule-based scoring is more reliable for structured code evaluation.

---

## Provider Setup

### Anthropic

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

Install: `pip install anthropic`

### Mistral

```bash
# .env
MISTRAL_API_KEY=...
```

Install: `pip install mistralai`

### OpenAI

```bash
# .env
OPENAI_API_KEY=sk-...
```

Install: `pip install openai`

### Ollama (local)

1. Install and start Ollama: `ollama serve`
2. Pull your model: `ollama pull llama3.2`
3. Set in config:

```yaml
llm_judge:
  provider:
    name: "ollama"
    model: "llama3.2"
    base_url: "http://localhost:11434"
```

No API key required. Run `make judge-health` to verify connectivity.

---

## Scoring Scale Explained

### 5-Point Scale (default)

| Score | Label | Meaning |
|---|---|---|
| 5 | Excellent | Fully meets requirements; matches or surpasses the golden standard. |
| 4 | Good | Mostly meets requirements with minor omissions. |
| 3 | Adequate | Partially meets requirements; important elements missing or vague. |
| 2 | Poor | Attempts the task but misses most key requirements. |
| 1 | Unacceptable | Does not address the task or is entirely off-topic. |

### 3-Point Scale

| Score | Meaning |
|---|---|
| 3 | Good – meets requirements with minor gaps. |
| 2 | Adequate – some key aspects missing. |
| 1 | Poor – largely fails to meet requirements. |

### 10-Point Scale

Scores 1–10 with a half-point granularity between each adjacent level. See `judge_prompt_builder.py` for per-level definitions.

---

## Usage in a Module Evaluator

```python
from utils.scoring.llm_judge import JudgeRunner, LLMJudgeConfig

# Load config (once per evaluator instance)
config = LLMJudgeConfig.from_dict(yaml.safe_load(open("my_config.yaml")))
runner = JudgeRunner(config)

# Complement mode: store judge result alongside existing scores
judge_data = runner.build_result_dict(
    task_prompt=asset["prompt"],
    model_response=response,
    golden_standard=asset.get("golden_standard", ""),
    module_id="ux_writing",
)
# Attach to BenchmarkResult.data
result.data["llm_judge"] = judge_data
# Flat column for leaderboard aggregation
result.data["llm_judge_score"] = judge_data["score_normalised"]
```

The flat `llm_judge_score` column (0–100) is automatically picked up by the leaderboard generator and displayed as **LLM Judge Score**.

---

## How to Add a New Provider

1. Create `utils/scoring/llm_judge/providers/myprovider_provider.py`.
2. Inherit from `LLMJudgeProvider` (ABC) and implement both abstract methods:

```python
from .base_provider import LLMJudgeProvider, JudgeProviderResponse

class MyProvider(LLMJudgeProvider):
    PROVIDER_NAME = "myprovider"

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        # Call your API here
        ...

    def health_check(self) -> bool:
        # Verify connectivity
        ...
```

3. Register the new provider in `judge_runner._build_provider()`:

```python
if prov_cfg.name == "myprovider":
    from .providers.myprovider_provider import MyProvider
    return MyProvider(**kwargs)
```

4. Add `"myprovider"` to the `ProviderName` literal type in `judge_config.py`.
5. Add API key handling to `.env.example`.

---

## Health Check

```bash
# Check all providers
make judge-health

# Check a single provider
make judge-health PROVIDER=anthropic
```

---

## Known Limitations

- **Judge bias**: LLM judges may exhibit self-preference bias (favouring responses from the same model family) and verbosity bias (preferring longer responses). Use a different provider family than the model under test where possible.
- **Cost per run**: Each judged asset incurs one additional LLM API call. At ~500 tokens per evaluation, claude-haiku-4-5 costs roughly $0.0005 per asset.
- **Latency impact**: Each judge call adds 1–5 s latency per asset in complement mode. For batch runs with many assets, consider Ollama for zero-cost local judging.
- **Parse failure rate**: Adversarial or very short model responses may confuse the judge into emitting a non-standard format. `fail_on_parse_error: false` (default) returns `score=None` with a logged warning rather than aborting the run.
- **Scale calibration**: Different judge models may use the scoring scale differently. Always compare judge scores across models using the same judge and scale.
