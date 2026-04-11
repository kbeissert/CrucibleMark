# CrucibleMark: System-Architektur

**Zielgruppe:** Engineers, die den Framework-Core verstehen oder erweitern wollen.

**Was du hier findest:**

- Layer-basierte Architektur (Core → Modules → Scoring → Data)
- MVC-Pattern & Design-Prinzipien
- Provider-Abstraktion (Ollama, OpenAI, Mistral)
- Datenfluss & Observability
- Known Technical Debt

> **Siehe auch:** DEVELOPER_GUIDE.md (für Modul-Entwicklung)

______________________________________________________________________

## 🏗️ Architektur-Übersicht

### 🛑 Oberste Regel: Strict Separation of Concerns (Measurement vs. Publishing)

Das gesamte CrucibleMark-Projekt folgt einer unumstößlichen Prämisse: der strikten Trennung der reinen Datenmessung (Measurement) von nachgelagerten Auswertungen (Publishing).

1. **Measurement (Core Benchmark Loop):**
   Der Kern der Benchmark-Orchestrierung (Runner) ist kompromisslos iterativ, ausfallsicher (`try...finally`) und minimalistisch. Sein **einziges** Ziel: LLM-Tests isoliert ausführen, Roh-/Audit-Logs führen und nach jedem Modul-Durchlauf das Leaderboard fehler- und blockierungsfrei generieren und speichern. Keine externen Abhängigkeiten gefährden diesen Prozess.

2. **Publishing (Downstream-Features):**
   Zusätzliche redaktionelle oder bewertende Funktionen – z. B. der KI-basierte **Meta-Reviewer** – sind vollständig vom Core-Runner entkoppelt. Sie laufen offline als eigenständige Prozesse und dürfen den iterativen Benchmark-Prozess niemals blockieren, verlangsamen oder durch Fehler abbrechen lassen.

### 🛑 Zweite Regel: Single Source of Truth (SSOT) & DRY (Don't Repeat Yourself)

Jede logische Funktion hat **genau einen festen Platz** in einem spezifischen Modul.
- **Wiederverwendung vor Neuerfindung:** Eine etablierte Funktion an anderer Stelle darf niemals neu geschrieben, dupliziert oder in ein Hilfsskript ausgelagert werden.
- **Erweiterung (Open/Closed Principle):** Reicht die Funktionalität eines Moduls für einen neuen Use Case nicht aus, abstrahiert oder parametrisiert man das ursprüngliche Modul so, dass es den neuen Fall mitabdeckt, ohne die alte Funktion zu verlieren.

### 🛑 Dritte Regel: Configuration-Driven & No Magic Numbers

Das Projekt läuft strikt über Konfigurationen.
- **Keine Magic Numbers:** Alle Zahlen, Formeln, Metriken und statischen Konstanten bleiben außerhalb des Python-Codes.
- **Auslagerung:** Diese Werte stehen in zentralen YAML-Konfigurationsdateien und werden dort importiert.

### 🛑 Vierte Regel: Anti-God-Script & Modularisierung

Das Framework wehrt sich aktiv gegen monolithische Skripte ("God-Scripts").
- **Aktives Monitoring:** Bei Weiterentwicklungen überwacht man Skriptlänge und Komplexität. Droht ein God-Script, muss sofort gegengesteuert werden.
- **Submodul-Kapselung:** Wachsende Skripte zerlegt man logisch. Funktionalitäten kapselt man in kleine, fokussierte Module und importiert sie ins Hauptskript.

CrucibleMark folgt einer **Plugin-basierten Architektur**, bei der Benchmark-Module vom Core-Framework durch Konfigurations-Contracts entkoppelt sind.

### Design-Prinzipien

1. **Config-First:** Alle Module entdeckt das Framework via `benchmark_config.yaml` (kein Hardcoding)
2. **Provider-Agnostisch:** Module wissen nicht, ob sie Ollama oder GPT-4 testen
3. **Stateless Runs:** Jeder Benchmark ist unabhängig (keine Cross-Run-Pollution)
4. **Reproducibility:** Fixe Seeds und deterministische Prompts

______________________________________________________________________

## 🎯 Layer-Architektur

```text
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
│ - Model Cards (benchmark_scores/model_cards/)      │
│ - Provider Cards (benchmark_scores/provider_cards/)│
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Layer 5: Publishing (Downstream, entkoppelt)        │
│ - Meta-Reviewer (generate_review.py)               │
│ - Web Export Pipeline (web_export.py)              │
│ - Judge-Flow → verdichtet in Review-Artikel        │
└─────────────────────────────────────────────────────┘
```

______________________________________________________________________

## 🎮 Layer 1: Framework Core

### Benchmark Orchestrator

**Einstiegspunkt:** `make benchmark` / `make benchmark-auto` → `run_benchmark.py` / `scripts/core/benchmark_auto.py` → `scripts/core/unified_runner.py`

**Unified-Runner Strategy:** CrucibleMark steuert lokale, Cloud-basierte Open-Weights und kommerzielle Laufzeitumgebungen über eine zentrale `UnifiedBenchmarkRunner` Klasse, wendet aber je nach Provider unterschiedliche Strategien an, um faire Ergebnisse zu liefern.

1. **Lokale & Cloud-Proxy Ausführung (Ollama / Provider):**

   - **Ziel:** „User Experience Simulation" (Wie fühlt es sich lokal an?) bzw. „Proxy-Stabilität".
   - **Komponente:** `AdaptivePauseCalculator` (`utils/adaptive_pause.py`)
   - **Logik:** Pausiert bei lokalen Ausführungen zwischen Tests basierend auf Modellgröße (RAM Footprint), Output-Länge (Context Overhead) und voriger Ausführungszeit.
   - **Modi:** `PRODUCTION` (15–30 s Pausen für maximale Stabilität) vs. `DEV` (5–10 s Pausen für schnelle Iteration).

2. **Kommerzielle APIs / Cloud Open-Weights Ausführung:**

   - **Ziel:** „Throughput & Reliability" (API-Stress-Test)
   - **Komponente:** `RateLimiter` (`utils/rate_limiter.py`)
   - **Logik:** Respektiert spezifische Provider-Limits (RPM/TPM per `config/rate_limits.yaml`), nutzt aber ansonsten minimale Pausen für maximalen Durchsatz.

**Speicherung & Trennung (3-CSV-Architektur):**
Die Ergebnisse werden vom Runner durch den `ResultManager` (`utils/result_manager.py`) automatisch in eine von drei Quellen getrennt (Single Source of Truth Konzept):
- `local_models_benchmark.csv` (Lokale VRAM Ausführungen)
- `cloud_models_benchmark.csv` (API Proxies, Cloud Open-Weights, z.B. LPU inference)
- `commercial_models_benchmark.csv` (Closed-Source Commercial APIs wie OpenAI)

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

**Provider-Spezifische Eigenheiten:**

| Provider | Auth | Token Limit | Streaming | Retry Logic |
|----------|------|-------------|-----------|-------------|
| Ollama | Keine (localhost) | Modellabhängig (8K–128K) | ✅ | N/A (lokal) |
| OpenAI | Bearer token | 128K (GPT-4) | ✅ | 429 → Exponential Backoff |
| Mistral | API key | 32K | ❌ | 500 → 3× Retry |
| Anthropic | API key | 200K | ✅ | 429 → Exponential Backoff |
| Google | API key | 1M–2M | ❌ | SDK-seitig |

**Globaler Token-Fallback-Wrapper:**
Das Framework implementiert einen robusten Ansatz zur Bewältigung harter Output-Token-Limits, zentral im `BaseProviderClient` über `_execute_with_token_fallback`.

1. **Zentrale Kaskade:** Die Systemkonfiguration (`benchmark_config.yaml`) definiert eine globale Fallback-Kaskade (z. B. `[8192, 4096, 2048, 1024]`).
2. **Dynamische Reduzierung:** Schlägt eine API-Anfrage wegen Limitüberschreitungen fehl, fängt der Wrapper die Exception ab und probiert das nächstkleinere Limit transparent erneut.
3. **Fast-Fail für Budget:** Bei Budget- oder Quota-Fehlern (`"402 payment required"`, `"insufficient_quota"`) greift ein Fast-Fail-Mechanismus und verhindert teure Retries.
4. **Metadaten-Tracking:** Nach Abschluss protokolliert der Client in das `BenchmarkResult`-DTO, ob die Kaskade aktiv war (`token_limit_fallback`) und welches Limit galt (`token_limit_used`).

**Config-getriebener Output-Cap (Token-Budget-System, ab v3.4.0):**
Ergänzend zum Fallback-Wrapper setzt `base_runner.py` über `execute_test_module()` für definierte Module einen direkten `max_tokens`-API-Parameter als fairen Vergleichbarkeits-Cap. Der Wert wird aus `benchmark_config.yaml → token_budgets[module_key]` gelesen und nur übergeben, wenn er nicht `None` ist. Reasoning-Module sind bewusst ausgenommen. Schöpft ein Modell das Budget aus, wird `token_limit_cutoff=True` im Result gesetzt und ein `[!NOTE]`-Block ins Audit-Log injiziert.

### Hardware Context & „Prompt as Config"

CrucibleMark koppelt alle Auswertungen an das Hardware- oder Kosten-Umfeld. Der **`SystemContextManager` (`utils/system_context.py`)** setzt das um:

- **T/s Berechnung:** Berechnet zentral die `tokens_per_second` für alle Benchmark-Runs.
- **Prompt-Injection:** Holt dynamische Rahmendaten über das Testsystem basierend auf dem in `benchmark_config.yaml` festgelegten `runner_environment` passend zum `run_type` (Local vs. Commercial).
- **„Prompt-as-Config":** System-Prompts für textgenerierende Pipeline-Funktionen (z. B. für den Meta-Reviewer) sind vollständig nach `config/meta_reviewer_prompt.yaml` ausgelagert. Der System-Code führt lediglich ein `.format()` aus und injiziert Hardware-Variablen und Ergebnislogs in das YAML-Template.
- **Data-Coupling & Regex-Integration:** Das System injiziert Metadaten (Token-Limits, Loop-Errors, ausgelöste Safety-Protokolle) via Warnblöcke direkt in die auszuwertenden Markdown-Logs. Der Evaluierungs-Flow parst diese Metadaten über vordefinierte Regex-Muster oder ID-Anker (z. B. "7.2.001"). Das befähigt den Judge, Modelle ganzheitlich – einschließlich technischer Flaws – zu bewerten. Hartes Grammar-Enforcement im Prompt verhindert Halluzinationen über einen aktiven Willen der KI-Modelle.

______________________________________________________________________

## 📦 Layer 2: Benchmark Modules

### MVC-Pattern (Strict Separation)

```text
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

______________________________________________________________________

### Modul-Discovery (Config-First)

**Ablauf:**

1. Framework parst `benchmark_config.yaml`
2. Filtert Module mit `enabled: true`
3. Lädt `benchmark_modules/<module_id>/config.yaml`
4. Importiert `test_class` dynamisch
5. Instanziiert Test-Objekt
6. Führt `execute()` aus

**Wichtig:** Neue Module lassen sich hinzufügen, ohne Framework-Code zu ändern.

______________________________________________________________________

## 🧮 Layer 3: Scoring Engine

### 1. Granular Rubric Scoring

Für **Reasoning Modules** (Tier 1–2). Nutzt partielle Punktevergabe basierend auf Rubriken.

**Schwellenwerte:**

- 80 %+ matches: 100 % credit
- 60–79 % matches: 75 % credit
- 40–59 % matches: 50 % credit
- < 40 % matches: 0 % credit

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

Für **Standard Modules** (Code Quality, UX Writing).

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
- **Metric:** Cosine Similarity (0–1 → 0–100 %)
- **Threshold:** 0.78 (Standard), 0.55 (Expert Tier)

______________________________________________________________________

### Golden Standard Comparison

Das Leaderboard basiert auf **statischen Golden Standards** (Design by Intention). Feste Tier-Schwellenwerte in `benchmark_config.yaml` (`scoring_tiers`) sorgen für konsistente Rankings. Seit Version 2.5 gibt es kein dynamisches Referenzmodell mehr. Das folgende Code-Snippet zeigt die Badge-Logik als Illustration – die tatsächlich gültigen Schwellenwerte stehen ausschließlich in der Config.

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

**Aktuelle Tier-Spezifikation:** Siehe [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md).

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

**Skill Profile Generation:** Das System erstellt ein Profil basierend auf Speed Class und Top-Modul (z. B. „Fast Code Reviewer").

______________________________________________________________________

### Web Export Pipeline

**Einstiegspunkt:** `make web-export` → `scripts/web_export.py`

Der Web Exporter ist ein eigenständiger Publishing-Schritt (Layer 4 Downstream), der vollständig vom Core-Benchmark-Loop entkoppelt ist. Er liest ausschließlich aus bereits generierten Artefakten und schreibt in das externe Frontend-Repository.

**SSOT-Prinzip:** Die Leaderboard-CSV ist die einzige Datenquelle. Ein vollständiger Rebuild (`shutil.rmtree` auf `models/`) stellt sicher, dass der Export immer synchron mit dem Leaderboard ist — Modelle die nicht in der CSV stehen, erscheinen nicht im Export.

**Model Cards & Provider Cards:** Strukturierte JSON-Steckbriefe pro Modell (`benchmark_scores/model_cards/`) und pro Provider (`benchmark_scores/provider_cards/`), generiert via LLM (`make model-cards`, `make provider-cards`). Sie enthalten Entwickler, Herkunftsland, Stärken/Schwächen, Datenschutz-Metadaten und Sovereign-Risk-Einschätzung. Die Cards werden (a) als Kontext-Block in den Meta-Reviewer injiziert und (b) als eigenständige JSON-API für das Web-Frontend bereitgestellt.

**Verzeichnis-Auflösung (Fallback-Matcher):** Interne Modell-IDs (Ordnernamen in `outputs/audit_logs/`) weichen oft von den CSV-Anzeigenamen ab (Provider-Prefix wie `moonshotai_`, Versions-Suffix wie `-20251001`). Der Exporter löst das über einen gestuften Lookup: Exact Match → Suffix-Match (Provider-Prefix) → Prefix-Match (Versions-Suffix).

**Export-Struktur:**

```text
<web_export_dir>/
├── leaderboard.json              ← globale Rangliste (aus CSV)
├── meta.json                     ← Export-Metadaten (Zeitstempel, Modellzahl)
├── provider_landscape_review.md  ← Provider-Gesamtreview
└── models/<model-slug>/
    ├── data.json                 ← Scores + Modul-Details pro Modell
    ├── comparisons/
    │   └── review_<timestamp>.md ← Meta-Reviewer-Artikel (aus docs/reviews/)
    └── audit_logs/
        └── *.md                  ← sanitierte Einzellogs (ohne Judge-Sektion)
```

**Audit-Log-Sanitierung:** Vor dem Export werden die Audit-Logs bereinigt (`sanitize_audit_log()`). Entfernt wird Section 3 (Judge-Auswertung, Scores, Golden-Standard-Referenzen). Erhalten bleiben Header, Prompt, Modellantwort und Modul-Metriken. Die Judge-Bewertung fließt nicht direkt in den Export, sondern verdichtet in die Review-Artikel ein.

______________________________________________________________________

### Backup-Strategie (Snapshot & Prune)

**Workflow** (`make backup`):

1. **Snapshot:** Archiv erstellen
2. **Prune JSON-Logs:** Nur letzte fünf Runs behalten
3. **CSV-Konsolidierung:** Nur neueste Zeile pro (Modell, Asset)

**Effekt:** CSV-Dateien bleiben < 5 MB

**Siehe:** `docs/BACKUP_STRATEGY.md`

______________________________________________________________________

## 🔍 Observability & Logging

### „Silent Console, Noisy Log" Strategie

#### 1. Console (User-Facing)

```python
print("✅ Code Quality: 85%")
print("⏳ Testing Reasoning Module (2/7)...")
```

Warnings von Drittanbieter-Bibliotheken werden unterdrückt.

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

   - **Annahme:** Framework funktioniert mit nur einem aktiven Modul
   - **Risiko:** Leaderboard könnte abstürzen
   - **Test:** Config mit nur einem Modul aktiv

2. **Column Pruning**

   - **Annahme:** Leaderboard löscht Spalten deaktivierter Module
   - **Risiko:** Zombie-Spalten
   - **Test:** Modul deaktivieren → Spalte weg?

3. **Cache Orphans**

   - **Annahme:** JSON-Files werden bei Modul-Löschung bereinigt
   - **Risiko:** Festplatten-Müll
   - **Test:** Modul löschen → prüfen

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## 🗺️ Roadmap

Die v1.x-Roadmap ist abgeschlossen. Die aktuelle Roadmap (Agentic Benchmarks, Multimodal, Web-UI, CI/CD) steht in [README.md](../README.md).

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

**Dokumenten-Version:** 3.1.0 (Überarbeitung März 2026)\
**Kompatibel mit:** CrucibleMark v3.4.3+
