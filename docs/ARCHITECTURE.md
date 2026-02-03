# CrucibleMark: System Architecture

**Zielgruppe:** Engineers, die den Framework-Core verstehen oder erweitern wollen.

**Was Sie hier finden:**
- Layer-basierte Architektur (Core → Modules → Scoring → Data)
- MVC-Pattern & Design-Prinzipien
- Provider-Abstraktion (Ollama, OpenAI, Mistral)
- Datenfluss & Observability
- Known Technical Debt & Roadmap

> **Siehe auch:** DEVELOPER_GUIDE.md (für Modul-Entwicklung)

---

## 🏗️ Architektur-Übersicht

CrucibleMark folgt einer **Plugin-basierten Architektur**, bei der Benchmark-Module vom Core-Framework durch Konfigurations-Contracts entkoppelt sind.

### Design-Prinzipien

1. **Config-First:** Alle Module werden via `benchmark_config.yaml` entdeckt (kein Hardcoding)
2. **Provider-Agnostisch:** Module wissen nicht, ob sie Ollama oder GPT-4 testen
3. **Stateless Runs:** Jeder Benchmark ist unabhängig (keine Cross-Run-Pollution)
4. **Reproducibility:** Fixe Seeds + deterministische Prompts

---

## 🎯 Layer-Architektur

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Framework Core (Orchestration)            │
│ - Benchmark Runner (crucible_mark.py)              │
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

---

## 🎮 Layer 1: Framework Core

### Benchmark Orchestrator

**Einstiegspunkt:** `make benchmark` → `scripts/core/run_local_benchmark.py`

**Verantwortlichkeiten:**
- Config-Parsing
- Modul-Discovery (nur aktive Module laden)
- Execution-Flow
- Provider-Abstraktion
- Rate-Limiting & Retry-Logic

**Key Invariant:** Der Orchestrator kennt **keine Modul-Namen**. Alles läuft über Config-Discovery.

---

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

| Provider | Auth | Token Limit | Streaming | Retry Logic |
|----------|------|-------------|-----------|-------------|
| Ollama | None (localhost) | Model-dependent (8K-128K) | ✅ Yes | N/A (local) |
| OpenAI | Bearer token | 128K (GPT-4) | ✅ Yes | 429 → Exponential Backoff |
| Mistral | API key | 32K | ❌ No | 500 → Retry 3x |

---

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
2. **Reproduzierbarkeit:** Scoring deterministisch
3. **Modularität:** Scoring austauschbar (Regex → LLM-Judge)

---

### Modul-Discovery (Config-First)

**Ablauf:**

1. Framework parst `benchmark_config.yaml`
2. Filtert Module mit `enabled: true`
3. Lädt `benchmark_modules/<module_id>/config.yaml`
4. Importiert `test_class` dynamisch
5. Instanziiert Test-Objekt
6. Führt `execute()` aus

**Wichtig:** Ein Entwickler kann ein Modul hinzufügen, ohne Framework-Code zu ändern!

---

## 🧮 Layer 3: Scoring Engine

### 1. Granular Rubric Scoring (v2.0)
Genutzt für **Reasoning Modules** (Tier 1-2). Ersetzt binäre Scores durch partielle Punktevergabe basierend auf Rubriken.

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

---

### Golden Standard Comparison

**Konzept:** Alle Modelle werden gegen **Mistral Large** (123B) als Referenz verglichen, aber das Leaderboard basiert ab v1.1 auf **Absoluten Standards**.

**Warum Absolute Standards?**
Die "Performance Ratio" (Relativ zu Mistral) war hilfreich, führt aber zu Verwirrung, wenn sich der Referenzwert ändert. Ab v1.1 gelten feste Hürden (z.B. >85% für Gold).

---

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

**Skill Profile Generation:**
Zusätzlich erstellt das System ein Profil basierend auf Speed Class und Top-Modul (z.B. "Fast Code Reviewer").

---

### Backup-Strategie (Snapshot & Prune)

**Workflow** (`make backup`):

1. **Snapshot:** Archiv erstellen
2. **Prune JSON-Logs:** Nur letzte 5 Runs behalten
3. **CSV-Konsolidierung:** Nur neueste Zeile pro (Modell, Asset)

**Effekt:** CSV-Dateien bleiben < 5 MB

**Siehe:** `docs/BACKUP_STRATEGY.md`

---

## 🔍 Observability & Logging

### "Silent Console, Noisy Log" Strategie

#### 1. Console (User-Facing)

```python
print("✅ Code Quality: 85%")
print("⏳ Testing Reasoning Module (2/7)...")
```

**Gefiltert:** Warnings von Drittanbieter-Bibliotheken

---

#### 2. Log-Datei (Developer-Facing)

**Pfad:** `logs/crucible.log`

**Inhalt:**
- Alles (Level: DEBUG)
- Inkl. unterdrückter Warnings
- Tracebacks bei Exceptions

---

## 🔧 Known Technical Debt

### Kategorie: Untested Assumptions

1. **Single-Module Isolation**
   - **Annahme:** Framework funktioniert mit nur 1 aktivem Modul
   - **Risiko:** Leaderboard könnte crashen
   - **Test:** Config mit nur 1 Modul aktiv

2. **Column Pruning**
   - **Annahme:** Leaderboard löscht Spalten deaktivierter Module
   - **Risiko:** Zombie-Spalten
   - **Test:** Modul deaktivieren → Spalte weg?

3. **Cache Orphans**
   - **Annahme:** JSON-Files werden bei Modul-Löschung bereinigt
   - **Risiko:** Festplatten-Müll
   - **Test:** Modul löschen → Prüfen

---

### Kategorie: Code Smells

1. **Duplicated Config Parsing**
   - **Problem:** 3+ Skripte parsen separat
   - **Fix:** Zentrales `core/config_manager.py`

2. **Hardcoded Paths**
   - **Problem:** Einige nutzen `results/` statt Config
   - **Fix:** Alle Pfade aus Config lesen

3. **Inconsistent Error Handling**
   - **Problem:** Ollama crasht, API retries
   - **Fix:** Einheitliche `ErrorHandler`-Klasse

---

### Kategorie: Missing Features

1. **No Rollback Mechanism**
   - **Impact:** Medium
   - **Effort:** 2 Stunden

2. **No Incremental Leaderboard**
   - **Impact:** Low
   - **Effort:** 4 Stunden

3. **No Diff Reports**
   - **Impact:** High
   - **Effort:** 6 Stunden

---

## 🗺️ Roadmap (Path to v1.0)

### Phase 1: Stability

**Ziel:** Framework-Contract validieren

**Tasks:**
- [ ] Single-Module-Test
- [ ] Column-Pruning-Test
- [ ] Cache-Cleanup-Test

---

### Phase 2: Code Hygiene

**Ziel:** DRY-Prinzip durchsetzen

**Tasks:**
- [ ] Zentrales Config-Parsing
- [ ] Type-Hints + Docstrings
- [ ] Einheitliches Error-Handling

---

### Phase 3: LLM-as-a-Judge

**Ziel:** Regex-Scoring durch LLM ersetzen

**Design:** GPT-4o-mini als Judge

**Backwards-Compatible:** Config-Flag `scoring_method`

---

## 📚 Appendix: Design-Patterns

### 1. Strategy Pattern (Scoring)

```python
class BaseEvaluator:
    def evaluate(self, response: str, asset: Dict) -> float:
        raise NotImplementedError
```

---

### 2. Template Method Pattern (BaseTest)

```python
class BaseTest:
    def run(self, model, llm_client):
        self.load_asset()
        result = self.execute(model, llm_client)  # Override
        score = self.score_response(result)       # Override
        self.save_to_csv(score)
```

---

### 3. Factory Pattern (Provider)

```python
class LLMClientFactory:
    @staticmethod
    def create(provider: str) -> LLMClient:
        if provider == "ollama":
            return OllamaProvider()
        # ...
```

---

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)  
**Kompatibel mit:** CrucibleMark v0.9.5+
