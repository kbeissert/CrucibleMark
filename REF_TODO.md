# REF_TODO.md – Refactoring & Future Development

## ✅ COMPLETED

### Fallbacks & Provider SSOT (v3.2.0)
- [x] **Dynamic Provider SSOT:** Hardgecodete Kategorie-Definitionen in CLI und Leaderboard entfernt; zentral über `benchmark_config.yaml` (`utils/model_utils.py`) dynamisiert.
- [x] **Open-Weights Cloud API Support:** Dedizierte Cloud-Infrastruktur für Open-Weights Modelle (z. B. via Groq) eingerichtet.
- [x] **Local Cloud Removal:** Legacy-Kategorie "Local Cloud" im gesamten System (Scores, Meta-Reviews, DataFrames) sauber mit `Cloud (Open-Weights)` fusioniert.

### Audit & Meta-Review Generation (v3.1.0)
- [x] **Meta-Reviewer Anchoring:** Off-by-one Parsing Bugs behoben (via durchgängiger YAML ID-Anker).
- [x] **Anti-Halluzinations-Schutz (Grammar Restriktionen):** Meta-Review-Prompt um harten Passiv-Zwang ergänzt, um Anthropomorphisierung im Fazit zu verhindern.
- [x] **Automatisierte Metadaten-Extraktion:** Regex-basiertes Herausfiltern von API-Limits, Endlosschleifen und Safety-Protokollen (Warnings) in den Audit-Logs für kontextsensitive Evaluierung.

### Architecture Hardening & Anti-Censorship (v3.0.0)
- [x] **3-Tier Refusal Framework:** Intelligentes Abfangen von Hard- und Soft-Refusals und API-Timeouts.
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
- [x] Abstract Scorer Interface und Provider Abstraction
- [x] Native Pipeline Integration & Phase 1–3 implementation
- [x] Hybrid Scoring System (Gewichtung Regex- und Judge-Scores, Fallback-Weights)
- [x] Rubric & Prompt Configuration (`benchmark_config.yaml`)
- [x] Module Rollout (Code Quality, UX Writing, Docs, Content)

### Refactoring & Stability (v2.6.2)
- [x] **God-Script Dismantling (Phase 3):** `provider_clients.py` sauber in modulare Pakete unter `utils/providers/` aufgeteilt – Facade Pattern.
- [x] **Namespace Collision Resolution:** Modulspezifische `ResultManager`-Logik extrahiert, strikte Entkopplung von globalen Systemen hergestellt.
- [x] **Magic Numbers Centralization:** Endpunkte und Limits (z. B. Ollamas Default-Port 11434) in `constants.py` zentralisiert.
- [x] **LLM Token Loop Hallucination Fallback:** API-Trimming-Logik in `llm_client.py` implementiert und in `AUDIT_AND_METAREVIEW.md` dokumentiert.
- [x] **Documentation Restructuring:** README.md rigoros an `benchmark_config.yaml`-Kategorien angeglichen, veraltete Scripts vollständig entfernt.

### Module Refactoring & Features
- [x] Political Compass Decoupling (Metrics-Logik von Scoring isoliert)
- [x] Alpha-Randomization in Multiple Choice Modules (Label-Bias vermieden)
- [x] Human Baseline Script (`run_human_compass.py`)
- [x] Code Quality Audit → v2.0.1 (Fixed Import)
- [x] UX Writing & Microcopy → v2.0
- [x] Documentation Quality → v2.0
- [x] Content Transformation → v2.0.1 (Fixed Logic)
- [x] Cultural Intelligence → v2.0

______________________________________________________________________

## 🔄 IN PROGRESS

### Planned for Next Session
- [ ] **LLM Judge: Batch-Mode (Phase 3.5)**: Token-Verbrauch durch gebündelte Requests reduzieren.
- [ ] **Volldurchlauf aller lokalen Modelle**: Generierung eines echten finalen Leaderboards (43/43).
- [ ] **Re-run Reasoning Logic**: Verfälschte 0-Punkte für lokale Modelle bereinigen.
- [ ] **Stabilitätsanalyse `gpt-oss`**: Vorherigen Absturzkandidat prüfen.

### Testing Infrastructure
- [ ] Unit tests für alle Module (aktuell ca. 60%)
- [ ] Integration tests (Framework-Ebene)
- [ ] Performance Benchmarks
- [ ] CI/CD Pipeline (GitHub Actions)

______________________________________________________________________

## 📋 BACKLOG

### Q3 und Q4 2026

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
- Meta-Analyse der Judge-Cost- und Token-Verhältnisse über Modelle hinweg
- System-Prompts tunen, um Overhead zu reduzieren (ohne Konsensqualität zu opfern)

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
| **Unit Tests & CI/CD** | Med | 2–3 weeks | Pending |
| **Web UI / Analytics Dash.** | Low | 4–6 weeks | Backlog |
| **Multimodal Support** | Low | 6–8 weeks | Backlog |

______________________________________________________________________

**Last Updated:** 2026-03-28 **Version:** 3.2.0 (Strict SSOT & Full Provider Refactoring) **Next Milestone:** Agentic Workflow & Web-UI
