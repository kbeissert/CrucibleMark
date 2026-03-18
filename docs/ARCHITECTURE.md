# CrucibleMark: System Architecture

**Zielgruppe:** Engineers, die den Framework-Core verstehen oder erweitern wollen.

**Was Sie hier finden:**

- Layer-basierte Architektur (Core → Modules → Scoring → Data)
- MVC-Pattern & Design-Prinzipien
- Provider-Abstraktion (Ollama, OpenAI, Mistral)
- Datenfluss & Observability
- Known Technical Debt & Roadmap

> **Siehe auch:** DEVELOPER_GUIDE.md (für Modul-Entwicklung)

______________________________________________________________________

## 🏗️ Architektur-Übersicht

CrucibleMark folgt einer **Plugin-basierten Architektur**, bei der Benchmark-Module vom Core-Framework durch Konfigurations-Contracts entkoppelt sind.

### Design-Prinzipien

1. **Config-First:** Alle Module werden via `benchmark_config.yaml` entdeckt (kein Hardcoding)
1. **Provider-Agnostisch:** Module wissen nicht, ob sie Ollama oder GPT-4 testen
1. **Stateless Runs:** Jeder Benchmark ist unabhängig (keine Cross-Run-Pollution)
1. **Reproducibility:** Fixe Seeds + deterministische Prompts

______________________________________________________________________

## 🎯 Layer-Architektur

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Framework Core (Orchestration)            │
│ - Benchmark Runner (run_benchmark.py)              │
│ - Config Manager (benchmark_config.yaml)           │
│ - Provider Abstraction (Ollama, OpenAI, Mistral)   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: Benchmark Modules (Plugins)                │
│ - Module Discovery (via config.yaml)               │
│ - Test Execution (test.py = Controller)            │
│ - Asset Loading (YAML schemas)                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: Scoring Engine                             │
│ - Evaluators (core/evaluators.py)                  │
│ - Hybrid Scoring (Keyword + Semantic)              │
│ - Golden Standard Comparison                        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Layer 4: Data Persistence                           │
│ - CSV Writer (append-only logs)                    │
│ - Leaderboard Generator (aggregation)              │
│ - Backup System (snapshot + prune)                 │
└─────────────────────────────────────────────────────┘
```

______________________________________________________________________

## 🎮 Layer 1: Framework Core

### Benchmark Orchestrator

**Einstiegspunkt:** `make benchmark` → `scripts/core/run_local_benchmark.py`

**Dual-Runner Strategy:** CrucibleMark trennt strikt zwischen lokalen und kommerziellen Laufzeitumgebungen, um faire Ergebnisse fÃ¼r jeden Kontext zu liefern.

1. **Local Runner (`scripts/core/run_local_benchmark.py`):**

   - **Ziel:** "User Experience Simulation" (Wie fühlte es sich an, lokal zu arbeiten?)
   - **Komponente:** `AdaptivePauseCalculator` (`utils/adaptive_pause.py`)
   - **Logik:** Pausiert zwischen Tests basierend auf Modellgröße (RAM Footprint), Output-Länge (Context Overhead) und voriger Ausführungszeit.
   - **Modes:** `PRODUCTION` (15-30s Pausen für max. Stabilität) vs `DEV` (5-10s Pausen für schnelle Iteration).

1. **Commercial Runner (`scripts/core/run_commercial_benchmark.py`):**

   - **Ziel:** "Throughput & Reliability" (API-Stress-Test)
   - **Komponente:** `RateLimiter` (`utils/rate_limiter.py`)
   - **Logik:** Respektiert Provider-Limitate (RPM), aber nutzt ansonsten minimale Pausen für maximalen Throughput.

**Verantwortlichkeiten (Shared Framework):**

- Config-Parsing
- Modul-Discovery (nur aktive Module laden)
- Execution-Flow
- Provider-Abstraktion

**Key Invariant:** Der Orchestrator kennt **keine Modul-Namen**. Alles läuft über Config-Discovery.

______________________________________________________________________

### Provider-Abstraktion

**Unified Interface:**

```python
class LLMClient:
    def generate(self, model: str, prompt: str, **kwargs) -> str:
        pass

    def is_accessible(self) -> bool:
        pass
```

**Provider-Spezifische Quirks:**

| Provider | Auth | Token Limit | Streaming | Retry Logic | |----------|------|-------------|-----------|-------------| | Ollama | None (localhost) | Model-dependent (8K-128K) | ✅ Yes | N/A (local) | | OpenAI | Bearer token | 128K (GPT-4) | ✅ Yes | 429 → Exponential Backoff | | Mistral | API key | 32K | ❌ No | 500 → Retry 3x | | Anthropic | API key | 200K | ✅ Yes | 429 → Exponential Backoff | | Google | API key | 1M - 2M | ❌ No | SDK Handled |

**Globaler Token-Fallback-Wrapper:**
Das Framework implementiert einen robusten Architekturansatz zur Bewältigung harter Output-Token-Limits, der zentral im `BaseProviderClient` über die Funktion `_execute_with_token_fallback` gesteuert wird.
1. **Zentrale Kaskade:** Die Systemkonfiguration (`benchmark_config.yaml`) definiert eine globale Fallback-Kaskade (z.B. `[8192, 4096, 2048, 1024]`).
2. **Dynamische Reduzierung:** Schlägt eine API-Anfrage wegen Limitüberschreitungen fehl, fängt der Wrapper die Exception ab (durch provider-spezifische Error-Keywords wie `"max_tokens"`) und probiert das nächstkleinere Limit transparent erneut.
3. **Fast-Fail für Budget:** Bei Budget- oder Quota-Fehlern (`"402 payment required"`, `"insufficient_quota"`) greift ein *Fast-Fail*-Mechanismus ein, der sofort blockiert und teure Retrys verhindert.
4. **Metadaten-Tracking:** Nach Abschluss protokolliert der Client in das `BenchmarkResult`-DTO, ob die Kaskade verwendet wurde (`token_limit_fallback`) und welches Limit endgültig galt (`token_limit_used`).

### Hardware Context & "Prompt as Config"
CrucibleMark verfolgt den Architektur-Ansatz, dass alle Auswertungen an das Hardware- oder Kosten-Umfeld gekoppelt sein sollten.
Dies wird durch den **`SystemContextManager` (`utils/system_context.py`)** umgesetzt:
- **T/s Berechnung:** Dieser berechnet zentral die `tokens_per_second` (T/s) für alle Benchmark-Runs (aus Execution-Time und Output-Tokenanzahl).
- **Prompt-Injection:** Der Manager holt dynamische Rahmendaten über das Testsystem auf Basis des in der `benchmark_config.yaml` festgelegten `runner_environment` passend zum `run_type` (Local vs Commercial).
- **"Prompt-as-Config":** System-Prompts für textgenerierende Pipeline-Funktionen (wie z.B. für den Meta-Reviewer) sind vollständig **ausgelagert (z.B. nach `config/meta_reviewer_prompt.yaml`)**. Der System-Code führt lediglich ein `.format()` aus und injiziert Hardware-Variablen und Logs der Ergebnisse in das YAML-Template.
______________________________________________________________________

## 📦 Layer 2: Benchmark Modules

### MVC-Pattern (Strict Separation)

```
┌──────────────────────────────────────────────────────┐
│ test.py (Controller)                                 │
│ - LLM-Ausführung                                     │
│ - Zeit-Messung                                       │
│ - Delegation an Evaluator                            │
└──────────────────────────────────────────────────────┘
                    ↓ delegiert
┌──────────────────────────────────────────────────────┐
│ core/evaluators.py (Model/Logic)                     │
│ - Scoring-Algorithmen                                │
│ - Keyword-Matching                                   │
│ - Semantic Similarity                                │
│ - KEINE LLM-Calls!                                   │
└──────────────────────────────────────────────────────┘
                    ↓ nutzt
┌──────────────────────────────────────────────────────┐
│ core/constants.py (Config/Data)                      │
│ - Regex-Patterns                                     │
│ - Schwellenwerte                                     │
│ - Keyword-Listen                                     │
└──────────────────────────────────────────────────────┘
```

**Warum diese Trennung?**

1. **Testbarkeit:** Evaluators ohne LLM testbar (Unit-Tests)
1. **Reproduzierbarkeit:** Scoring deterministisch
1. **Modularität:** Scoring austauschbar (Regex → LLM-Judge)

______________________________________________________________________

### Modul-Discovery (Config-First)

**Ablauf:**

1. Framework parst `benchmark_config.yaml`
1. Filtert Module mit `enabled: true`
1. Lädt `benchmark_modules/<module_id>/config.yaml`
1. Importiert `test_class` dynamisch
1. Instanziiert Test-Objekt
1. Führt `execute()` aus

**Wichtig:** Ein Entwickler kann ein Modul hinzufügen, ohne Framework-Code zu ändern!

______________________________________________________________________

## 🧮 Layer 3: Scoring Engine

### 1. Granular Rubric Scoring

Genutzt für **Reasoning Modules** (Tier 1-2). Nutzt partielle Punktevergabe basierend auf Rubriken.

**Thresholds:**

- 80%+ matches: 100% credit
- 60-79% matches: 75% credit
- 40-59% matches: 50% credit
- <40% matches: 0% credit

```python
RUBRICS = {
    'reasoning_5c_001': {
        'problem_recognition': {'weight': 20, 'keywords': [...]},
        'appropriate_refusal': {'weight': 40, 'keywords': [...]},
        # ...
    }
}
```

### 2. Hybrid-Ansatz (Keyword + Semantic)

Genutzt für **Standard Modules** (Code Quality, UX Writing).

```python
def hybrid_score(response: str, asset: Dict) -> float:
    # 1. Keyword-Matching (40%)
    keywords = asset['evaluation']['keywords']
    found = sum(1 for kw in keywords if kw in response.lower())
    keyword_score = (found / len(keywords)) * 100

    # 2. Semantic Similarity (60%)
    golden = asset['evaluation']['golden_answer']
    semantic_score = calculate_similarity(response, golden) * 100

    # 3. Weighted
    return (keyword_score * 0.4) + (semantic_score * 0.6)
```

**Semantic Similarity:**

- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Metric:** Cosine Similarity (0-1 → 0-100%)
- **Threshold:** 0.78 (Standard), 0.55 (Expert Tier)

______________________________________________________________________

### Golden Standard Comparison

**Konzept:** Alle Modelle werden gegen **Mistral Large** (123B) als Referenz verglichen, das Leaderboard basiert jedoch auf **Absoluten Standards**.

**Absolute Standards:** Es gelten feste Hürden (z.B. >85% für Gold) für die Performance. Dadurch bleibt das Tier-Ranking konsistent, selbst wenn das hinterlegte Referenzmodell für die Berechnung der Semantik-Scores geupdatet wird.

## 📊 Layer 4: Data Persistence

### Leaderboard-Generation

**Score-Berechnung (v1.1):**

```python
# Modul Scores
routine_modules = [m for m in modules if "Reasoning" not in "Name"]
reasoning_modules = [m for m in modules if "Reasoning" in "Name"]

routine_score = avg(score for score in routine_modules)
reasoning_score = avg(score for score in reasoning_modules)

# Total Score (Balanced Average)
total_score = (routine_score + reasoning_score) / 2
```

**Badge-Vergabe (v1.1):**

```python
if total_score >= 85:
    badge = "🏆 Gold"
elif total_score >= 70:
    badge = "🥈 Silver"
elif total_score >= 55:
    badge = "🥉 Bronze"
else:
    badge = "⚖️ Standard"
```

**Skill Profile Generation:** Zusätzlich erstellt das System ein Profil basierend auf Speed Class und Top-Modul (z.B. "Fast Code Reviewer").

______________________________________________________________________

### Backup-Strategie (Snapshot & Prune)

**Workflow** (`make backup`):

1. **Snapshot:** Archiv erstellen
1. **Prune JSON-Logs:** Nur letzte 5 Runs behalten
1. **CSV-Konsolidierung:** Nur neueste Zeile pro (Modell, Asset)

**Effekt:** CSV-Dateien bleiben < 5 MB

**Siehe:** `docs/BACKUP_STRATEGY.md`

______________________________________________________________________

## 🔍 Observability & Logging

### "Silent Console, Noisy Log" Strategie

#### 1. Console (User-Facing)

```python
print("✅ Code Quality: 85%")
print("⏳ Testing Reasoning Module (2/7)...")
```

**Gefiltert:** Warnings von Drittanbieter-Bibliotheken

______________________________________________________________________

#### 2. Log-Datei (Developer-Facing)

**Pfad:** `logs/crucible.log`

**Inhalt:**

- Alles (Level: DEBUG)
- Inkl. unterdrückter Warnings
- Tracebacks bei Exceptions

______________________________________________________________________

## 🔧 Known Technical Debt

### Kategorie: Untested Assumptions

1. **Single-Module Isolation**

   - **Annahme:** Framework funktioniert mit nur 1 aktivem Modul
   - **Risiko:** Leaderboard könnte crashen
   - **Test:** Config mit nur 1 Modul aktiv

1. **Column Pruning**

   - **Annahme:** Leaderboard löscht Spalten deaktivierter Module
   - **Risiko:** Zombie-Spalten
   - **Test:** Modul deaktivieren → Spalte weg?

1. **Cache Orphans**

   - **Annahme:** JSON-Files werden bei Modul-Löschung bereinigt
   - **Risiko:** Festplatten-Müll
   - **Test:** Modul löschen → Prüfen

______________________________________________________________________

### Kategorie: Code Smells

1. **Duplicated Config Parsing**

   - **Problem:** 3+ Skripte parsen separat
   - **Fix:** Zentrales `core/config_manager.py`

1. **Hardcoded Paths**

   - **Problem:** Einige nutzen `results/` statt Config
   - **Fix:** Alle Pfade aus Config lesen

1. **Inconsistent Error Handling**

   - **Problem:** Ollama crasht, API retries
   - **Fix:** Einheitliche `ErrorHandler`-Klasse

______________________________________________________________________

### Kategorie: Missing Features

1. **No Rollback Mechanism**

   - **Impact:** Medium
   - **Effort:** 2 Stunden

1. **No Incremental Leaderboard**

   - **Impact:** Low
   - **Effort:** 4 Stunden

1. **No Diff Reports**

   - **Impact:** High
   - **Effort:** 6 Stunden

______________________________________________________________________

## 🗺️ Roadmap (Path to v1.0)

### Phase 1: Stability

**Ziel:** Framework-Contract validieren

**Tasks:**

- [ ] Single-Module-Test
- [ ] Column-Pruning-Test
- [ ] Cache-Cleanup-Test

______________________________________________________________________

### Phase 2: Code Hygiene

**Ziel:** DRY-Prinzip durchsetzen

**Tasks:**

- [ ] Zentrales Config-Parsing
- [ ] Type-Hints + Docstrings
- [ ] Einheitliches Error-Handling

______________________________________________________________________

### Phase 3: LLM-as-a-Judge

**Ziel:** Regex-Scoring durch LLM ersetzen

**Design:** GPT-4o-mini als Judge

**Backwards-Compatible:** Config-Flag `scoring_method`

______________________________________________________________________

## 📚 Appendix: Design-Patterns

### 1. Strategy Pattern (Scoring)

```python
class BaseEvaluator:
    def evaluate(self, response: str, asset: Dict) -> float:
        raise NotImplementedError
```

______________________________________________________________________

### 2. Template Method Pattern (BaseTest)

```python
class BaseTest:
    def run(self, model, llm_client):
        self.load_asset()
        result = self.execute(model, llm_client)  # Override
        result = self.score_response(result)      # Override
        self.save_to_csv(result)
```

______________________________________________________________________

### 3. Factory Pattern (Provider)

```python
class LLMClientFactory:
    @staticmethod
    def create(provider: str) -> LLMClient:
        if provider == "ollama":
            return OllamaProvider()
        # ...
```

______________________________________________________________________

**Dokumenten-Version:** 3.0.0 (Rewrite Mar 2026)\
**Kompatibel mit:** CrucibleMark v3.0.0+
