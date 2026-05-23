# Tool Use Calibration — Quick Start

**Status:** Reset complete, ready for execution  
**Date:** 2026-05-23

---

## What Was Done

✓ **Reset:** Old `tooluse_leaderboard.csv` → `_calibration_archive/` (reference preserved)  
✓ **Test Matrix:** 7-model cohort defined with roles & expectations (`CALIBRATION_TEST_MATRIX.md`)  
✓ **Log Structure:** Fillable template ready for results (`CALIBRATION_LOG.md`)

---

## Next: Execute Calibration

### Step 1: Run Test Cohort

```bash
cd /Users/kbeissert/_PROJEKTE/Entwicklung/cruciblemark

# Execute all 21 runs (7 models × 3 assets)
make benchmark-tooluse \
  MODELS="claude-haiku-4.5,claude-sonnet-4.6,gpt-5.4,gemini-3-1-pro-preview,NousResearch_Hermes-4-70B,codestral-latest,o3-mini" \
  FORCE=1
```

**Expected runtime:** ~2–4 hours (depends on MCP latency + model speed)

---

### Step 2: Generate Reports

```bash
# Build new leaderboard from calibration runs
make tooluse-leaderboard

# Generate per-model reports
make tooluse-report
```

---

### Step 3: Fill Calibration Log

Open `CALIBRATION_LOG.md` and populate:
- **Per-Asset Results** tables (p1/p2 scores, hallucination flags)
- **Statistics** (mean, std dev, min/max per asset)
- **Gap Analysis** (check success criteria)
- **Dimension Breakdown** (factuality/hallucination_risk/uncertainty_handling)
- **Rubric Assessment** (is discrimination working?)
- **Final Decision** (ACCEPT / ADJUST / REDESIGN)

---

### Step 4: Analyze & Decide

**Key Questions:**

1. **Is discrimination clear?**
   - Top tier (Haiku/Sonnet/GPT) vs. Middle (Hermes/Codestral) vs. Bottom (o3-mini)?
   - Expected gap: ≥15 points top-to-middle, ≥10 points middle-to-bottom

2. **Are hallucinations caught?**
   - tooluse003: o3-mini should fail (hallucination_flag=True)
   - tooluse001/002: all should pass (hallucination_flag=False)

3. **Are partial scores making sense?**
   - factuality should vary most
   - hallucination_risk should be tight at top
   - uncertainty_handling should show provider variation

4. **Do weights need tuning?**
   - If all dimensions score similarly: weights are balanced ✓
   - If one dimension dominates: consider reweighting
   - If no spread: rubric may be too loose/strict

---

## Files Reference

| File | Purpose |
|------|---------|
| `CALIBRATION_TEST_MATRIX.md` | Which 7 models, why, expected scores |
| `CALIBRATION_LOG.md` | Fill this in as results come in |
| `JUDGE_CHECKLIST.md` | How Judge scores each dimension (reference) |
| `SCHEMA_PRINCIPLES.md` | Don't let scoring guides sneak back into assets |
| `assets/tooluse00{1,2,3}.yaml` | SSoT for scoring (read-only during calibration) |

---

## Success Metrics

**Pass Criteria:**
- [ ] Top-tier gap ≥ 15 points
- [ ] Bottom-tier gap ≥ 10 points
- [ ] hallucination_flag works as hard constraint
- [ ] Parse-error rate < 5%
- [ ] No bimodal score distributions

**If all pass:** → Move to full 75-model production run  
**If some fail:** → Adjust weights, retest subset  
**If structure broken:** → Redesign rubric (escalate)

---

## What NOT to Change During Calibration

🔴 Do NOT:
- Modify golden_answers in asset YAMLs
- Add scoring guides to asset YAMLs (they stay in docs only)
- Change weights mid-calibration
- Run full 75-model set yet

✓ DO:
- Run the 7-model test cohort exactly as specified
- Document everything in CALIBRATION_LOG.md
- Compare results to success criteria
- Only then decide on weight adjustments

---

## Next Phase (Post-Calibration)

Once calibration data is good:

1. Document findings in `CALIBRATION_RESULTS.md`
2. If weights changed: update asset YAML `weights:` section
3. Run full 75-model benchmark with calibrated rubric
4. Archive calibration leaderboard as baseline
5. Publish final leaderboard

---

## Questions?

Check:
- `JUDGE_CHECKLIST.md` — How scoring works
- `SCORING_RUBRIC.md` — Dimension definitions
- `assets/tooluse00{1,2,3}.yaml` — Golden answers & criteria
