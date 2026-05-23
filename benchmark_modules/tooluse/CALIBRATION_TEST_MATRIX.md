# Tool Use Benchmark — Calibration Test Matrix v3.10.0

**Date:** 2026-05-23  
**Purpose:** Validate golden standards and P2 scoring rubric  
**Status:** Ready for execution

---

## Test Cohort (7 Models)

| # | Model ID | Display Name | Role | Provider | Size Class | Reason |
|---|----------|--------------|------|----------|------------|--------|
| 1 | claude-haiku-4.5 | Claude Haiku 4.5 | Judge Anchor (Strict) | Anthropic | Edge | Enforces standards rigorously; baseline for "correct" behavior |
| 2 | claude-sonnet-4.6 | Claude Sonnet 4.6 | Strong Baseline | Anthropic | Desktop | High capability, moderate softness; primary reference |
| 3 | gpt-5.4 | GPT-5.4 | Commercial High-Performer | OpenAI | Frontier | Peak commercial model; should be top tier |
| 4 | gemini-3-1-pro-preview | Gemini 3.1 Pro Preview | Provider Contrast | Google | Desktop | Alternative high-performer; shows provider variation |
| 5 | NousResearch_Hermes-4-70B | Hermes 4 70B | Open-Weights Anchor | Nous Research | Desktop | Local/sovereign deployment; strong open alternative |
| 6 | codestral-latest | Codestral | Production-Grade Anchor | Mistral | Desktop | Practical production model; bridges academic/commercial |
| 7 | o3-mini | o3-mini | Intentional Weak Anchor | OpenAI | Edge | Lower capability; validates rubric discrimination at bottom |

---

## Asset Coverage

All 7 models run all 3 assets:

```
Assets × Models = 21 test runs
```

| Asset | Purpose | Judge Target |
|-------|---------|--------------|
| tooluse001 | EU License Research (Web Search) | Factuality (sources), no hallucination |
| tooluse002 | HTTP Fetch & Extract (List Models) | Accuracy (3+ real models), no invention |
| tooluse003 | 404 Error Handling | Hallucination immunity, proper failure mode |

---

## Scoring Expectations

### Haiku 4.5 (Judge Anchor)
- **Target P2:** 75–95 (strict, high accuracy expected)
- **hallucination_flag:** False for all runs
- **Rationale:** Sets the standard for what "correct" looks like

### Sonnet 4.6 (Strong Baseline)
- **Target P2:** 80–100 (should exceed Haiku in some dimensions)
- **hallucination_flag:** False for tooluse001/002; watch closely for tooluse003
- **Rationale:** Strong enough to validate high-end discrimination

### GPT-5.4 (Commercial High-Performer)
- **Target P2:** 85–100 (peak performance expected)
- **hallucination_flag:** False for all
- **Rationale:** Should show top-tier separation from middle

### Gemini 3.1 Pro (Provider Contrast)
- **Target P2:** 75–95 (comparable to Sonnet, some variation)
- **hallucination_flag:** False for most
- **Rationale:** Tests whether rubric is provider-agnostic

### Hermes 4 70B (Open-Weights)
- **Target P2:** 65–85 (solid, but noticeably below Sonnet)
- **hallucination_flag:** Possible for tooluse003 (weaker error handling)
- **Rationale:** Local alternative; should show real capability gap without being catastrophic

### Codestral (Production)
- **Target P2:** 65–80 (practical, not top-tier)
- **hallucination_flag:** Possible for complex tasks
- **Rationale:** Real-world production model; shows practical lower bound

### o3-mini (Intentional Weak)
- **Target P2:** 40–70 (noticeably worse, validates bottom separation)
- **hallucination_flag:** Likely for tooluse003 (poor error handling expected)
- **Rationale:** Ensures rubric can distinguish weak from strong

---

## Measurement Schedule

```
Phase 1: Execute all 21 runs (sequence: all assets per model)
Phase 2: Collect & aggregate scores
Phase 3: Analyze distributions (per asset, per model group, gaps)
Phase 4: Validate hallucination_flag accuracy
Phase 5: Document calibration results & recommend weight adjustments
```

---

## Success Criteria

### Minimum Viable Discrimination:
- **Top-tier gap (Haiku/Sonnet/GPT-5.4 vs. Hermes/Codestral):** ≥ 15 points P2
- **Bottom gap (Codestral/Hermes vs. o3-mini):** ≥ 10 points P2
- **hallucination_flag sensitivity:** ≥ 90% accuracy on tooluse003

### Distribution Stability:
- **No bimodal or multimodal distributions** (suggests rubric is too loose/strict in specific dimensions)
- **Parse-error rate < 5%** (cleanup from v3.9 should hold)
- **Retry rate stable** (tool_call_attempts median ≤ 1.5)

### Validation:
- **Golden answer alignment:** Top models show ≥ 80% match on all 3 assets
- **Uncertainty handling:** Top models admit limits clearly, weak models speculate
- **Factuality spread:** Hermes/Codestral show ≥ 20-point gap on factuality vs. o3-mini

---

## Output Location

All results stored in:
```
/Users/kbeissert/_PROJEKTE/Entwicklung/cruciblemark/benchmark_scores/
  ├── tooluse_leaderboard.csv (fresh, calibration v3.10.0)
  ├── reports/
  │   ├── tooluse_calibration_20260523.md (summary)
  │   ├── tooluse_001_calibration_scores.json (per-model P2 breakdown)
  │   ├── tooluse_002_calibration_scores.json
  │   └── tooluse_003_calibration_scores.json
  └── _calibration_archive/
      └── tooluse_leaderboard_pre_calibration_v3100.csv (reference)
```

---

## Running the Calibration

```bash
# Execute all 7 models across all 3 assets
make benchmark-tooluse MODELS="claude-haiku-4.5,claude-sonnet-4.6,gpt-5.4,gemini-3-1-pro-preview,NousResearch_Hermes-4-70B,codestral-latest,o3-mini" FORCE=1

# Generate leaderboard & reports
make tooluse-leaderboard
make tooluse-report
```

---

## Next Steps

1. ✓ Baseline archived
2. → Execute test cohort runs
3. → Analyze P2 distributions
4. → Validate hallucination_flag
5. → Fine-tune weights (if needed)
6. → Document calibration results in `CALIBRATION_RESULTS.md`
