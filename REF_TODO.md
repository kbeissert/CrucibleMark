# REF_TODO.md - Refactoring & Future Development

## ✅ COMPLETED

### Version 1.1+ Core Architecture
- [x] **Leaderboard Overhaul (v1.1)** (Absolute Scoring, Speed Profiles)
- [x] **Reasoning Module Implementation**
- [x] **System Probes & Warnungen**
- [x] **Global Cascading Token Fallback & Error Handling** ("Fast Fail")
- [x] **Golden Standard Consolidierung** (Asset YAML as SSOT)

### LLM-Based Scoring System (v1.5 Milestone Reached)
- [x] Abstract Scorer Interface / Provider Abstraction
- [x] Native Pipeline Integration & Phase 1-3 implementation
- [x] Hybrid Scoring System (weighting Regex + Judge Scores, Fallback-Weights)
- [x] Rubric & Prompt Configuration (`benchmark_config.yaml`)
- [x] Module Rollout (Code Quality, UX Writing, Docs, Content)

### Refactoring & Stability (v2.6.1)
- [x] **LLM Token Loop Hallucination Fallback:** API-Trimming logic implemented in `llm_client.py` and warnings documented in `AUDIT_AND_METAREVIEW.md`
- [x] **Documentation Restructuring:** README.md updated to rigorously match `benchmark_config.yaml` categories, obsolete scripts fully removed.

### Module Refactoring & Features
- [x] Political Compass Decoupling (Metrics logic isolated from scoring)
- [x] Alpha-Randomization in Multiple Choice Modules (prevent label-bias)
- [x] Human Baseline Script (`run_human_compass.py`)
- [x] Code Quality Audit → v2.0.1 (Fixed Import)
- [x] UX Writing & Microcopy → v2.0
- [x] Documentation Quality → v2.0
- [x] Content Transformation → v2.0.1 (Fixed Logic)
- [x] Cultural Intelligence → v2.0

______________________________________________________________________

## 🔄 IN PROGRESS

### Planned for Next Session
- [ ] **LLM Judge: Native JSON Output**: Refactoring `judge_parser.py` and Prompts
- [ ] **LLM Judge: Batch-Mode (Phase 3.5)**: Optimize token consumption by bunching requests
- [ ] **Volldurchlauf aller lokalen Modelle**: Generierung eines echten finalen Leaderboards (43/43)
- [ ] **Re-run Reasoning Logic**: Verfälschte 0-Punkte für lokale Modelle bereinigen.
- [ ] **Stabilitätsanalyse `gpt-oss`**: Vorheriger Absturzkandidat prüfen.

### Testing Infrastructure
- [ ] Unit tests for all modules (currently ~60%)
- [ ] Integration tests (framework-level)
- [ ] Performance benchmarks
- [ ] CI/CD pipeline (GitHub Actions)

______________________________________________________________________

## 📋 BACKLOG

### Q3 / Q4 2026

#### 1. Creative Writing Module
- Story generation
- Poetry evaluation
- Character development
- Plot coherence

#### 2. Web UI
- Interactive dashboard
- Real-time progress
- Result visualization
- Model comparison

#### 3. API Mode
- REST API for remote benchmarking
- Queue management
- Authentication

#### 4. Cost vs. Accuracy Analysis
- Meta-analysis of the Judge-Cost / Token ratios across models
- Tuning System Prompts to reduce overhead (without sacrificing consensus)

### v2.0.0 (Cloud & Redesign)

#### 1. Multimodal Support
- Image + Text tasks
- Vision-based benchmarks
- OCR evaluation

#### 2. Advanced Feature Set
- Custom Plugin Evaluator System
- Adaptive Testing (Dynamic Difficulty)
- Scheduled Continuous Benchmarking & Alerting

______________________________________________________________________

## 📊 Effort Estimation (Next Pipeline)

| Task | Priority | Effort | Status |
|------|----------|--------|---------|
| **LLM Judge JSON Batching** | High | 1 week | In Progress |
| **Volldurchlauf Leaderboard** | High | 1 week | Pending |
| **Unit Tests & CI/CD** | Med | 2-3 weeks | Pending |
| **Web UI / Analytics Dash.** | Low | 4-6 weeks | Backlog |
| **Multimodal Support** | Low | 6-8 weeks | Backlog |

______________________________________________________________________

**Last Updated:** 2026-03-16 **Version:** 2.6.1 (Stability & Context) **Next Milestone:** v2.7 (Judge Batching & Final Leaderboard)
