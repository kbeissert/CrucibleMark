# REF_TODO.md - Refactoring & Future Development

## ✅ COMPLETED

### Audit & Meta-Review Generation (v3.1.0)
- [x] **Meta-Reviewer Anchoring:** Off-by-one Parsing Bugs behoben (via durchgängiger YAML ID-Anker).
- [x] **Anti-Halluzinations-Schutz (Grammar Restriktionen):** Meta-Review-Prompt um harten Passiv-Zwang ergänzt, um Anthropomorphisierung im Fazit zu verhindern. 
- [x] **Automatisierte Metadaten-Extraktion:** Regex-basiertes Herausfiltern von API-Limits, Endlosschleifen und Safety-Protokollen (Warnings) in den Audit-Logs für kontextsensitive Evaluierung.

### Architecture Hardening & Anti-Censorship (v3.0.0)
- [x] **3-Tier Refusal Framework:** Intelligentes Abfangen von Hard-/Soft-Refusals und API-Timeouts.
- [x] **Progressive Temperature Loop:** `while True`-Retry-Block im Execution-Layer mit schrittweisen Temperaturerhöhungen (0.1, 0.4, 0.7) als Safety-Bypass.
- [x] **Pydantic Schema Serialization:** Behebung von `AttributeError`-Abstürzen durch präzises `json.loads()` Parsing aus der rohen String-Response.
- [x] **Repository Consolidation:** Major Markdown-Updates, Entschlackung der Roadmap und Framework Bump auf 3.0.0.

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

### Refactoring & Stability (v2.6.2)
- [x] **God-Script Dismantling (Phase 3):** `provider_clients.py` safely split into modular packages in `utils/providers/` utilizing the Facade pattern.
- [x] **Namespace Collision Resolution:** Extracted module-specific `ResultManager` logic to decouple strictly from global systems.
- [x] **Magic Numbers Centralization:** Safely extracted endpoints and limits (like Ollamas default port 11434) to unified `constants.py`.
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

**Last Updated:** 2026-03-18 **Version:** 3.0.0 (Safety Shift & Refusal Loop) **Next Milestone:** Agentic Workflow & Web-UI
