# REF_TODO.md - Refactoring & Future Development

## ✅ COMPLETED (v1.0.0)

### Framework Refactoring (v2.0)
- [x] Modular architecture implementation
- [x] Unified provider interface (Ollama, OpenAI, Anthropic)
- [x] YAML-based configuration system
- [x] CSV output standardization
- [x] Leaderboard integration
- [x] Checkpoint/resume functionality

### Module Refactoring (All v2.0+)
- [x] Code Quality Audit → v2.0 (Pylint 9.2/10)
- [x] UX Writing & Microcopy → v2.0 (Pylint 8.8/10)
- [x] Documentation Quality → v2.0 (Pylint 9.0/10)
- [x] Content Transformation → v2.0 (Pylint 8.9/10)
- [x] Cultural Intelligence → v2.0 (Pylint 9.1/10)
- [x] Political Compass → v3.0.1 (Pylint 9.85/10)

### Code Quality
- [x] Pylint scores 8.8-9.85/10 (avg 9.15/10)
- [x] Type hints on all public APIs
- [x] Docstrings (Google Style)
- [x] Black + isort formatting
- [x] Error handling robustness

### Documentation
- [x] Root README v1.0.0
- [x] Module READMEs (all 6)
- [x] Configuration docs
- [x] API documentation
- [x] Contributing guidelines

---

## 🔄 IN PROGRESS

### Planned for Next Session
- [ ] **Human Baseline Script (`run_human_compass.py`)**:
    - Tool to allow humans to take the Political Compass test.
    - Terminal UI with shuffled options.
    - User identification (Pseudonym/Name).
    - Compatible JSON/CSV output for comparison in reports.

### Testing Infrastructure
- [ ] Unit tests for all modules (currently ~60%)
- [ ] Integration tests (framework-level)
- [ ] Performance benchmarks
- [ ] CI/CD pipeline (GitHub Actions)

### LLM-based Scoring System (MAJOR FEATURE)
**Status:** Planned for v1.1 or v1.5
**Complexity:** High
**Priority:** High

**Current Limitation:**
- Pattern-based scoring (keyword matching, regex)
- Limited nuance detection
- Cannot evaluate "quality" vs "correctness"

**Proposed Solution:**
- Use LLM-as-Judge (e.g., GPT-4, Claude 3.5)
- Evaluate subjective qualities:
  - Code elegance
  - UX tone appropriateness
  - Documentation clarity
  - Content style matching

**Implementation Scope:**
1. Scorer Module Design
   - [ ] Abstract Scorer Interface
   - [ ] Pattern-based Scorer (existing, refactored)
   - [ ] LLM-based Scorer (new)
   - [ ] Hybrid Scorer (combine both)

2. LLM Judge Configuration
   - [ ] Prompt templates for evaluation
   - [ ] Rubric definitions (per module)
   - [ ] Confidence scoring
   - [ ] Cost optimization (caching, batching)

3. Module Integration
   - [ ] Code Quality: Elegance, maintainability
   - [ ] UX Writing: Tone, empathy, clarity
   - [ ] Documentation: Completeness, readability
   - [ ] Content: Style matching, engagement

4. Validation & Calibration
   - [ ] Human baseline (gold standard)
   - [ ] Inter-LLM agreement
   - [ ] Cost/accuracy tradeoff analysis

---

## 📋 BACKLOG

### v1.1.0 (Q2 2026) - Planned Features

#### 1. LLM-based Scoring (if scope fits)
- Implement LLM-as-Judge for subjective scoring
- Hybrid scoring (pattern + LLM)
- Cost tracking & optimization

#### 2. Reasoning Module
- Logic puzzles
- Mathematical reasoning
- Common sense reasoning
- Tiered difficulty

#### 3. Creative Writing Module
- Story generation
- Poetry evaluation
- Character development
- Plot coherence

#### 4. Web UI
- Interactive dashboard
- Real-time progress
- Result visualization
- Model comparison

#### 5. API Mode
- REST API for remote benchmarking
- Queue management
- Authentication

### v1.2.0 (Q3 2026) - Advanced Features

#### 1. Multimodal Support
- Image + Text tasks
- Vision-based benchmarks
- OCR evaluation

#### 2. Custom Evaluators (Plugin System)
- User-defined scorers
- Custom rubrics
- External API integration

#### 3. Cloud Integration
- AWS/GCP deployment
- Distributed execution
- Result aggregation

#### 4. Team Collaboration
- Shared leaderboards
- Multi-user environments
- Role-based access

### v2.0.0 (Q4 2026) - Major Redesign

#### 1. LLM-based Scoring (if not in v1.1)
- Full LLM-as-Judge implementation
- Multi-model consensus scoring
- Automated rubric generation

#### 2. Adaptive Testing
- Dynamic difficulty adjustment
- Personalized benchmark paths
- Skill gap analysis

#### 3. Continuous Benchmarking
- Scheduled runs
- Model drift detection
- Historical tracking

---

## 🎯 RECOMMENDATIONS

### LLM-based Scoring Version Assignment

**Option A: v1.1.0 (Lightweight)**
- Implement ONLY for UX Writing & Documentation
- Use simple prompt-based evaluation
- No rubric system (hardcoded criteria)
- Estimated effort: 2-3 weeks

**Option B: v1.5.0 (Moderate) ⭐ RECOMMENDED**
- Implement for 3-4 modules (Code, UX, Docs, Content)
- Full rubric system
- Hybrid scoring (pattern + LLM)
- Cost optimization (caching)
- Estimated effort: 4-6 weeks

**Option C: v2.0.0 (Comprehensive)**
- Full framework redesign
- All modules LLM-scored
- Multi-model consensus
- Automated rubric generation
- Estimated effort: 8-12 weeks

### Rationale for v1.5.0:
1. **Feature Scope:** Too large for minor (v1.1), not fundamental enough for major (v2.0)
2. **Backward Compatibility:** Doesn't break existing APIs (minor version OK)
3. **User Expectation:** "Scoring upgrade" signals substantial improvement
4. **Development Time:** 4-6 weeks allows thorough testing
5. **Market Positioning:** v1.5 = "Enhanced Evaluation" milestone

---

## 📊 Effort Estimation

| Task | Priority | Effort | Version |
|------|----------|--------|---------|
| **Unit Tests (complete)** | High | 1-2 weeks | v1.0.1 |
| **CI/CD Pipeline** | High | 1 week | v1.0.1 |
| **Reasoning Module** | Medium | 3-4 weeks | v1.1.0 |
| **Web UI** | Medium | 4-6 weeks | v1.1.0 |
| **API Mode** | Low | 2-3 weeks | v1.1.0 |
| **LLM-based Scoring** | High | 4-6 weeks | v1.5.0 ⭐ |
| **Multimodal Support** | Low | 6-8 weeks | v2.0.0 |
| **Cloud Integration** | Low | 4-6 weeks | v2.0.0 |

---

## 🚀 NEXT ACTIONS

### Immediate (v1.0.1 - Maintenance Release)
1. Complete unit test coverage (60% → 95%)
2. Setup CI/CD (GitHub Actions)
3. Fix minor bugs from v1.0.0 feedback
4. Performance optimizations

### Short-term (v1.1.0 - Q2 2026)
1. Implement Reasoning Module
2. Create Web UI (basic)
3. Add API Mode (MVP)
4. Documentation updates

### Mid-term (v1.5.0 - Q3 2026)
1. **LLM-based Scoring System** ⭐
   - Design scorer architecture
   - Implement for 4 modules
   - Validate against human baselines
   - Document cost/accuracy tradeoffs

### Long-term (v2.0.0 - Q4 2026)
1. Full framework redesign
2. Multimodal support
3. Cloud-native architecture
4. Advanced features (adaptive testing, etc.)

---

**Last Updated:** 2026-02-03
**Version:** 1.0.0 (Released)
**Next Milestone:** v1.0.1 (Maintenance) → v1.1.0 (Features) → v1.5.0 (LLM Scoring) ⭐
