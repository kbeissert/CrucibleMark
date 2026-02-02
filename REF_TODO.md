# 📝 CrucibleMark Roadmap & TODO

**Version:** 0.9.5-beta → 1.0.0  
**Datum:** 1. Februar 2026  
**Fokus:** LLM-Judge-Scorer + Module-Hygiene

---

## 🎯 Current Sprint: Path to v1.0.0

**Ziel:** Production-Ready Release mit LLM-as-a-Judge Scoring  
**Timeline:** Q1 2026 (geschätzt: 4-6 Wochen)  
**Blocker:** LLM-Judge-Implementierung & Validation

---

## 🔥 Priority 1: LLM-as-a-Judge Scorer (Critical for v1.0)

**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 Wochen  
**Owner:** Core Team

### Anforderungen

- [ ] **Design-Phase (3-5 Tage)**:
  - [ ] Hybrid-Scorer-Architektur definieren (LLM-Judge + Current Scorer)
  - [ ] Prompt-Engineering für Judge-Modell (Mistral Large vs. GPT-4o vs. Claude)
  - [ ] Scoring-Schema: `data.llm_judge` in Structured Result Objects
  - [ ] Fallback-Strategy: Was passiert bei Judge-Timeout/Failure?

- [ ] **Implementation (1-2 Wochen)**:
  - [ ] `utils/llm_judge.py` erstellen (Judge-Client)
  - [ ] Integration in `evaluators.py` (pro Modul)
  - [ ] Parallel-Scoring: Current Scorer + LLM-Judge (Vergleich)
  - [ ] CSV-Export erweitern: `llm_judge_score`, `hybrid_score` Spalten

- [ ] **Validation (3-5 Tage)**:
  - [ ] Baseline-Messung: Golden Standard (Mistral Large) mit LLM-Judge
  - [ ] Korrelations-Analyse: Current Scorer vs. LLM-Judge (erwarte r > 0.85)
  - [ ] Edge-Case-Testing: Modelle mit <30% Score (Dolphin, Phi4)
  - [ ] Cost-Analysis: Token-Verbrauch für Judge (Budget-Impact)

- [ ] **Documentation (2-3 Tage)**:
  - [ ] USER_GUIDE: "Understanding LLM-Judge Scores"
  - [ ] ARCHITECTURE: Hybrid-Scorer-Methodology
  - [ ] DATA_FORMAT: Neue Spalten erklären
  - [ ] Changelog: v1.0.0 Release Notes

---

## 🛠 Priority 2: Module Refactoring (Code Hygiene)

**Status:** 🟡 Planned  
**Estimated Effort:** 1-2 Wochen (parallel zu LLM-Judge)  
**Owner:** Core Team

### Module-by-Module Cleanup

| Modul | Status | Estimated Time | Tasks |
|-------|--------|----------------|-------|
| `code_quality` | 🟡 Planned | 2-3h | Ruff-Check, PyLint auf 9.0+, Utility-Konsolidierung |
| `ux_writing` | 🟡 Planned | 2-3h | Scorer-Logik Review, Test-Coverage |
| `documentation_quality` | 🟡 Planned | 2-3h | Asset-Erweiterung (aktuell nur 5 Assets) |
| `content_transformation` | 🟡 Planned | 2-3h | Beta → v1.0 (Scorer-Validierung) |
| `cultural_intelligence` | 🟡 Planned | 2-3h | Asset-Diversität, **Negative Keywords** (v2.1 Feature für Idiom-Tests) |
| `reasoning_logic` | 🟡 Planned | 3-4h | RCI-Optimierung, Metacognition-Erweiterung |
| `political_compass` | ✅ Complete | - | v3.0 bereits Production-Ready |

### Allgemeine Tasks (alle Module)

- [ ] **Ruff-Check**: Alle Module 0 Errors
- [ ] **PyLint-Target**: Score > 9.0/10 pro Modul
- [ ] **Utility-Konsolidierung**: Kleine Helper in `core/utils.py` mergen
- [ ] **Test-Coverage**: Unit-Tests für Scorer (Ziel: >70%)
- [ ] **README-Updates**: Modul-READMEs mit neuesten Assets & Beispielen

---

## 📚 Priority 3: Documentation Polish

**Status:** 🟡 Planned  
**Estimated Effort:** 3-5 Tage  
**Owner:** Core Team

### User-Facing Documentation

- [ ] **USER_GUIDE.md**:
  - [ ] Tutorial-Section: "Your First Benchmark in 5 Minutes"
  - [ ] Checkpoint-System besser erklären (Resume nach Crash)
  - [ ] Troubleshooting: Häufige Fehler & Lösungen
  - [ ] LLM-Judge-Metriken Interpretation

- [ ] **DATA_FORMAT.md**:
  - [ ] Neue Spalten: `llm_judge_score`, `hybrid_score`, `confidence`
  - [ ] Beispiel-CSV mit Annotationen
  - [ ] Badge-Logik mathematisch erklärt (aktuell zu abstrakt)

- [ ] **BENCHMARK_SCENARIOS.md**:
  - [ ] Asset-Beispiele pro Modul (mit Expected Output)
  - [ ] "Was testet dieser Benchmark?" für Nicht-Techniker
  - [ ] Vergleichstabelle: CrucibleMark vs. MMLU/HumanEval

### Developer Documentation

- [ ] **ARCHITECTURE.md**:
  - [ ] Leaderboard-Package Architektur (neue `scripts/leaderboard/`)
  - [ ] Dependency-Graph (welches Modul nutzt welches Utility)
  - [ ] Design-Patterns (Package-by-Feature, Single Responsibility)
  - [ ] Refactoring-Learnings (für zukünftige Contributors)

- [ ] **ADDING_MODULES.md**:
  - [ ] Best Practices aus Module-Refactoring
  - [ ] Scorer-Template (Keyword + Semantic + LLM-Judge)
  - [ ] Testing-Strategie (Unit-Tests, Integration-Tests)
  - [ ] Checklist: "Is my module Production-Ready?"

---

## ✅ Completed (v0.9.5 - Feb 2026)

**Framework Hardening:**
- [x] **Leaderboard Refactoring**: Modulare Package-Architektur (1384 → 250 Zeilen)
- [x] **Code Quality**: PyLint 9.1/10, Ruff 100% clean
- [x] **Duplicate Code Elimination**: -48 Zeilen Duplikation
- [x] **Zero Regressions**: Functional Validation (11 Reasoning-Tests)

**Scoring & Methodology:**
- [x] **Granular Scoring**: Asset-Level Contributions (Routine/Reasoning Split)
- [x] **Reasoning v2.3**: Tier Weighting, Anti-Ceiling, Debug Mode
- [x] **Golden Standard Hygiene**: Trial-and-Commit Strategie
- [x] **Performance Ratio**: Normalisierung für faire Vergleichbarkeit

**Operations:**
- [x] **Cost & Token Tracking**: Real-time Calculation
- [x] **Logging System**: "Silent Console / Noisy Logfile"
- [x] **Backup Workflow**: `make backup` mit Auto-Cleanup
- [x] **Smart Rate Limit Handling**: Automatic Pause & Backoff

**Module (Production-Ready):**
- [x] Code Quality (v1.0.0)
- [x] UX Writing (v1.0.0)
- [x] Documentation Quality (v1.0.0)
- [x] Content Transformation (v0.9.0-beta)
- [x] Reasoning Logic (v2.3.0)
- [x] Political Compass (v3.0.0)
- [x] Cultural Intelligence (v1.0.0)

---

## 🔮 Future Roadmap (Post v1.0)

**Status:** 🔵 Planned (Low Priority)  
**Timeline:** Q2/Q3 2026

### Features

- [ ] **Reporting Dashboard**:
  - [ ] Streamlit/Dash-basiertes Web-UI
  - [ ] Live-Visualisierung der Benchmark-Runs
  - [ ] Vergleichs-Charts (Model A vs. Model B)
  - [ ] Estimated Effort: 2-3 Wochen

- [ ] **HuggingFace Leaderboard Integration**:
  - [ ] Auto-Upload der Ergebnisse
  - [ ] Public Leaderboard (opt-in)
  - [ ] Community-Benchmarks (andere nutzen CrucibleMark)
  - [ ] Estimated Effort: 1-2 Wochen

- [ ] **Custom Model Support**:
  - [ ] GGUF-Files ohne Ollama (direkter llama.cpp-Call)
  - [ ] vLLM-Integration (schnellere Inference)
  - [ ] Custom API-Endpoints (self-hosted LLMs)
  - [ ] Estimated Effort: 2 Wochen

- [ ] **Web Frontend**:
  - [ ] CSV-basierte Reports & Charts
  - [ ] No-Code Benchmark-Configuration
  - [ ] Ersetzt Python-CLI für Non-Developers
  - [ ] Estimated Effort: 4-6 Wochen

### Quality & Optimization

- [ ] **Leaderboard Weight Classes**:
  - [ ] Trennung: Lightweight (<20B) vs. Heavyweight (>70B)
  - [ ] Faire Bewertung für kleine Modelle
  - [ ] Separate Badges pro Weight Class
  - [ ] Estimated Effort: 1 Woche

- [ ] **Calibration Phase**:
  - [ ] Fine-Tuning aller Module für konsistente Ergebnisse
  - [ ] Scorer-Threshold-Optimization (Grid-Search)
  - [ ] Baseline-Messung über 100+ Modelle
  - [ ] Estimated Effort: 2-3 Wochen

- [ ] **Test-Coverage**:
  - [ ] Unit-Tests für Scorer & Evaluators (Ziel: >80%)
  - [ ] Integration-Tests für Benchmark-Runner
  - [ ] CI/CD-Pipeline (GitHub Actions)
  - [ ] Estimated Effort: 2 Wochen

---

## 📅 Milestone Timeline (Estimated)

| Milestone | Target Date | Status | Deliverables |
|-----------|-------------|--------|--------------|
| **v0.9.5** | ✅ Feb 1, 2026 | Complete | Framework Refactoring, Code Quality 9.1/10 |
| **v0.9.6** | Feb 15, 2026 | 🟡 Planned | Module Refactoring (all >9.0 PyLint) |
| **v0.9.7** | Feb 28, 2026 | 🟡 Planned | LLM-Judge MVP (Code Quality + Reasoning) |
| **v0.9.8** | Mar 7, 2026 | 🟡 Planned | LLM-Judge (all modules), Documentation Polish |
| **v1.0.0-rc1** | Mar 14, 2026 | 🔵 Future | Release Candidate (Full Testing) |
| **v1.0.0** | Mar 21, 2026 | 🔵 Future | **Production Release** 🎉 |

---

## 🤝 Contribution Guidelines

**Wenn du beitragen willst, priorisiere:**

1. **High Impact**: LLM-Judge-Scorer (P1)
2. **Quick Wins**: Module PyLint auf 9.0+ (P2, 2-3h pro Modul)
3. **Documentation**: USER_GUIDE Tutorial-Section (P3, 1 Tag)

**Vermeide aktuell:**
- Neue Features (Fokus auf v1.0-Stabilität)
- Breaking Changes (keine API-Änderungen vor v1.0)
- Experimentelle Scorer (nach v1.0)

---

## 📞 Questions?

- **Technische Fragen**: Siehe `docs/ARCHITECTURE.md`
- **Modul-Ideen**: Siehe `docs/ADDING_MODULES.md`
- **Bugs**: GitHub Issues (wenn Public) oder Logs (`logs/crucible.log`)

---

**Next Review:** Nach v0.9.6 (Module Refactoring Complete)  
**Last Updated:** 1. Februar 2026
