# CrucibleMark: System-Architektur

**Zielgruppe:** Engineers, die den Framework-Core verstehen oder erweitern wollen.

**Inhalt:**

- Layer-basierte Architektur (Core → Modules → Scoring → Data)
- MVC-Pattern & Design-Prinzipien
- Provider-Abstraktion (Ollama, OpenAI, Mistral)
- Datenfluss & Observability
- Bekannte technische Schulden

> **Siehe auch:** DEVELOPER_GUIDE.md (für Modul-Entwicklung)

---

## Architektur-Übersicht

### 🛑 Oberste Regel: Strict Separation of Concerns (Measurement vs. Publishing)

Das gesamte CrucibleMark-Projekt folgt einer unumstößlichen Prämisse: der strikten Trennung der reinen Datenmessung (Measurement) von nachgelagerten Auswertungen (Publishing).

1. **Measurement (Core Benchmark Loop):**
   Der Kern der Benchmark-Orchestrierung (Runner) ist kompromisslos iterativ, ausfallsicher (`try...finally`) und minimalistisch. Sein **einziges** Ziel: LLM-Tests isoliert ausführen, Roh-/Audit-Logs führen und nach jedem Modell-Durchlauf (sobald mindestens ein neues Ergebnis gespeichert wurde) das Leaderboard fehler- und blockierungsfrei generieren und speichern. Keine externen Abhängigkeiten gefährden diesen Prozess.

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

---

## Layer-Architektur

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

---

## Layer 1: Framework Core

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
- `local_models_benchmark.csv` (Lokale VRAM-Ausführungen auf Consumer-Hardware via Ollama)
- `cloud_models_benchmark.csv` (Open-Weights-Modelle auf Cloud-/Server-Infrastruktur: OpenRouter, Groq LPU, Ollama Cloud-Proxies)
- `commercial_models_benchmark.csv` (Closed-Source-Modelle, ausschließlich über proprietäre API verfügbar: OpenAI, Anthropic, Google, xAI, Mistral)

> **Benchmark-Philosophie:** `cloud_models_benchmark.csv` enthält bewusst **keine** lokalen Modelle. Open-Weights-Modelle wie Kimi K2 oder Qwen 3 werden hier auf der Infrastruktur gemessen, auf der sie mit kommerziellen Modellen konkurrieren — Cloud-Server oder LPU-Cluster, nicht Desktop-VRAM. Die Kernfrage lautet: *Wie stark sind Open-Weights-Modelle auf gleichwertiger Infrastruktur im Vergleich zu Closed-Source-APIs?*
>
> **Terminologie:** „Open Weights" ≠ „Open Source". Open-Weights-Modelle (z. B. Llama, Kimi K2, Qwen) veröffentlichen ihre trainierten Gewichte unter permissiven Lizenzen (Apache 2.0 o. ä.), legen aber Trainingsdaten, Trainings-Code und vollständige Architektur-Details in der Regel **nicht** offen. Sie sind damit öffentlich nutzbar, aber nicht im klassischen Open-Source-Sinne inspizierbar. CrucibleMark adressiert genau diese Intransparenz: Durch Beleuchtung des Verhaltens aus mehreren Perspektiven (Code, Logik, Sprache, Kultur) entsteht eine empirische Einordnung, die sonst mangels Quelleinsicht nicht möglich wäre.

**Verantwortlichkeiten (Shared Framework):**

- Config-Parsing
- Modul-Discovery (nur aktive Module laden)
- Execution-Flow
- Provider-Abstraktion

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

**`is_accessible()` — Typisierte Exception-Semantik:**
Die Methode prüft vor jedem Provider-Run ob die API erreichbar und authentifiziert ist. Kritisch: **HTTP 404 (Model Not Found) bedeutet NICHT „kein Zugriff"** — die API ist erreichbar, nur das Test-Modell existiert nicht. Ein generischer `except Exception`-Handler würde 404 fälschlicherweise als Auth-Fehler werten und den Provider komplett überspringen.

| Exception | Bedeutung | `is_accessible()` gibt zurück |
|---|---|---|
| `AuthenticationError` / `AuthError` | Ungültiger API-Key | `False` |
| `PermissionDeniedError` / `403` | Budget erschöpft, IP-Block | `False` |
| `NotFoundError` / `404` | Test-Modell nicht gefunden (API funktioniert) | `True` |
| `RateLimitError` / `429` | Throttling (API erreichbar) | `True` |
| Unbekannte Exception | Sicherheits-Fallback | `False` |

Das Test-Modell für den Health-Check ist pro Provider konfiguriert. Anthropic: `claude-haiku-4-5-20251001`.

**Provider-Spezifische Eigenheiten:**

| Provider | Auth | Token Limit | Streaming | Retry Logic | Besonderheiten |
|----------|------|-------------|-----------|-------------|----------------|
| Ollama | Keine (localhost) | Modellabhängig (8K–128K) | ✅ | N/A (lokal) | `finish_reason` + `tps_eval` aus Ollama-Metadaten |
| OpenAI | Bearer token | 128K (GPT-4) | ✅ | 429 → Exponential Backoff | — |
| Mistral | API key | 32K | ❌ | 500 → 3× Retry | ThinkChunk-Handling für Magistral (Streaming-Artefakt) |
| Anthropic | API key | 200K | ✅ | 429 → Exponential Backoff | `stop_reason` → normalisiert zu `finish_reason` |
| Google | API key | 1M–2M | ❌ | SDK-seitig | `STOP` uppercase → normalisiert |
| OpenRouter | Bearer token | Modellabhängig | ✅ | Im Wrapper | **Reasoning-Token-Budget** (siehe unten) |
| xAI | Bearer token | Modellabhängig | ✅ | Im Wrapper | `finish_reason` aus Streaming-Chunks extrahiert |
| Groq | Bearer token | Modellabhängig | ✅ | Im Wrapper | `max_completion_tokens` statt `max_tokens` (config-getrieben) |

**Globaler Token-Fallback-Wrapper:**
Das Framework implementiert einen robusten Ansatz zur Bewältigung harter Output-Token-Limits, zentral im `BaseProviderClient` über `_execute_with_token_fallback`.

1. **Zentrale Kaskade:** Die Systemkonfiguration (`benchmark_config.yaml`) definiert eine globale Fallback-Kaskade (z. B. `[8192, 4096, 2048, 1024]`).
2. **Dynamische Reduzierung:** Schlägt eine API-Anfrage wegen Limitüberschreitungen fehl, fängt der Wrapper die Exception ab und probiert das nächstkleinere Limit transparent erneut.
3. **Fast-Fail für Budget:** Bei Budget- oder Quota-Fehlern (`"402 payment required"`, `"insufficient_quota"`) greift ein Fast-Fail-Mechanismus und verhindert teure Retries.
4. **Metadaten-Tracking:** Nach Abschluss protokolliert der Client in das `BenchmarkResult`-DTO, ob die Kaskade aktiv war (`token_limit_fallback`) und welches Limit galt (`token_limit_used`).

**Config-getriebener Output-Cap (Token-Budget-System, ab v3.4.0):**
Ergänzend zum Fallback-Wrapper setzt `base_runner.py` über `execute_test_module()` für definierte Module einen direkten `max_tokens`-API-Parameter als fairen Vergleichbarkeits-Cap. Der Wert wird aus `benchmark_config.yaml → token_budgets[module_key]` gelesen und nur übergeben, wenn er nicht `None` ist. Reasoning-Module sind bewusst ausgenommen. Schöpft ein Modell das Budget aus, wird `token_limit_cutoff=True` im Result gesetzt und ein `[!NOTE]`-Block ins Audit-Log injiziert.

**SSoT Token-Budget-Berechnung (`resolve_token_budget()`, ab v3.5.7):**
Die Budget-Berechnung für Reasoning-Modelle ist in `utils/model_utils.py` als `resolve_token_budget(model, requested_max_tokens, config, module_key)` zentralisiert. Alle Provider (`openai.py`, `openrouter.py`, `mistral.py`) delegieren an diese Funktion statt inline-Logik zu duplizieren. Der Token-Parametername (`max_tokens` vs. `max_completion_tokens`) wird pro Provider aus `benchmark_config.yaml → providers.commercial.<provider>.token_param_name` gelesen.

Logik:
- Reasoning-Modell + explizites Budget → `token_budgets_reasoning_models[module_key]` (Fallback: Budget × 5)
- Reasoning-Modell ohne explizites Budget + < 10.000 Tokens → 25.000 Tokens fix
- Normales Modell → Budget unverändert

**OpenRouter: Reasoning-Token-Budget-Konflikt (ab v3.5.x):**
OpenRouter verrechnet bei Reasoning-Modellen (z. B. MiniMax M2, DeepSeek R1) die internen Denk-/Chain-of-Thought-Tokens direkt gegen das `max_tokens`-Budget. Das heißt: Ein Modell, das intern 7.500 Reasoning-Tokens verbraucht, hat bei `max_tokens=8192` nur noch ~692 Tokens für den sichtbaren Output — oder gar keine, wenn der Reasoning-Aufwand das Budget überschreitet. Das Framework löst das auf zwei Ebenen:

1. **Budget-Multiplikator:** `is_reasoning_model()` in `utils/model_utils.py` erkennt bekannte Reasoning-Architekturen (Trigger-Strings: `deepseek-r1`, `reasoning`, `phi4`, `qwq`, `o1`, `o3`, `magistral`, `glm-5`, `minimax-m2`, `gemini-2.5`, `kimi-k2`). Ab v3.5.8 hat die **Card-First-Lookup** Vorrang: Wurde ein Modell via Reasoning-Erkennung (ThinkingProbe) empirisch getestet, liefert `is_reasoning_model_from_card()` das validierte Ergebnis — unabhängig von String-Triggern. Für diese Modelle setzt `resolve_token_budget()` das Budget automatisch auf den erhöhten Wert aus `token_budgets_reasoning_models` in der Config (oder Faktor 5× bei unbekanntem Modul-Key).
2. **Transparenz:** Der OpenRouter-Provider extrahiert `completion_tokens_details.reasoning_tokens` aus der API-Antwort und speichert sie im `BenchmarkResult` (Feld `reasoning_tokens`). Bei gleichzeitigem `token_limit_cutoff=True` injiziert `benchmark_utils.py` einen `[!WARNING]`-Block ins Audit-Log mit Erklärung des Mechanismus.

> **Wichtig für neue Provider:** Wenn ein Provider Reasoning-Modelle hostet, muss geprüft werden, ob er Reasoning-Tokens gegen `max_tokens` verrechnet. Falls ja, muss `is_reasoning_model()` um die betroffenen Modell-Name-Trigger erweitert werden — `resolve_token_budget()` übernimmt dann automatisch die Budget-Anpassung für diesen und alle anderen Provider.

**Refusal-Metadaten (ab v3.5.7):**
Wenn ein Modell eine Antwort von < 15 Zeichen liefert (Ablehnungs-Signal), setzt `unified_runner.py` drei Felder ins BenchmarkResult:
- `refusal_flag: True` — maschinenlesbare Markierung
- `refusal_type: "content_safety"` — Klassifikation (zukünftig erweiterbar: `input_misclassification`, `api_error`, `token_budget_bug`)
- `refusal_note` — Freitext-Begründung

Alle drei Felder werden via `result_manager.py` als CSV-Spalten persistiert. Das unterscheidet eine aktive Ablehnung (Modell-Limitation) von einem ungetesteten Ergebnis.

**Reasoning-Erkennung (ThinkingProbe) & Card-First Workflow (ab v3.5.8):**
Um `is_reasoning_model()` empirisch statt heuristisch zu fundieren, führt v3.5.8 eine API-basierte Laufzeit-Erkennung ein:

1. **`probe_thinking_model(model_id, provider_key, config)`** in `utils/model_utils.py` sendet einen deterministischen Schritt-für-Schritt-Reasoning-Prompt an die Modell-API und wertet zwei Signale aus:
   - **Signal A:** `<think>` / `<thinking>` / `<thought>`-Tags im Response-Body → `confidence=high`
   - **Signal B:** `reasoning_tokens > 0` in der API-Metadaten-Antwort → `confidence=medium`
   - Signal C (Response-Länge) ist **nicht implementiert** — Instruction-Following-Modelle produzieren auf Reasoning-Prompts ebenfalls lange Antworten (False-Positive-Quelle).

2. **`ThinkingProbeResult`** (Dataclass): `detected: bool`, `evidence: str`, `confidence: Literal["high","medium","low"]`

3. **`is_reasoning_model_from_card(model_id)`:** Liest `thinking_probe_detected` aus der JSON-Model-Card. Dateiname-Auflösung via `re.sub(r'[:/.\s]', '_', model_id)` — konsistent mit `_safe_name()` in `generate_model_cards.py`. Gibt `None` zurück wenn kein Eintrag vorhanden (kein False-Positive).

4. **`is_reasoning_model()` Lookup-Hierarchie:**
   1. Card-Lookup (`is_reasoning_model_from_card()`) — hat immer Vorrang
   2. String-Trigger-Heuristik als Fallback

5. **`_ensure_model_card()` Hook in `unified_runner.py`:** Vor dem ersten Benchmark-Run eines Modells:
   - Card mit `thinking_probe_detected`-Feld → Skip
   - Card ohne Feld → Probe → Feld in Card eintragen
   - Keine Card → Probe → Minimal-Card erstellen (`card_status: "minimal"`)
   - Probe-Fehler 429 (Wochenlimit) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter
   - Probe-Fehler 403 (Subscription) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter
   - Probe-Fehler (sonstiger) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter

6. **`scripts/tools/probe_thinking.py`** (Standalone-CLI): Retroaktiver und On-Demand-Probe-Betrieb. Modi: `--model <id>`, `--missing` (Batch: alle Cards ohne Feld), `--all` (Force-Rescan). Provider-Inference: Config → `/` im ID → `openrouter` → sonst `ollama`. Batch-Modus bricht bei Einzelfehlern nicht ab.

> **Wichtig:** API-Modelle, die Reasoning intern verbergen (z. B. OpenAI o-Series), können via Probe nicht erkannt werden — für diese Modelle wird `thinking_probe_detected: true` manuell mit `thinking_probe_manual_override: true` in der Card gesetzt.

### Hardware Context & „Prompt as Config"

CrucibleMark koppelt alle Auswertungen an das Hardware- oder Kosten-Umfeld. Der **`SystemContextManager` (`utils/system_context.py`)** setzt das um:

- **T/s Berechnung:** Berechnet zentral die `tokens_per_second` für alle Benchmark-Runs.
- **Prompt-Injection:** Holt dynamische Rahmendaten über das Testsystem basierend auf dem in `benchmark_config.yaml` festgelegten `runner_environment` passend zum `run_type` (Local vs. Commercial).
- **„Prompt-as-Config":** System-Prompts für textgenerierende Pipeline-Funktionen (z. B. für den Meta-Reviewer) sind vollständig nach `config/meta_reviewer_prompt.yaml` ausgelagert. Der System-Code führt lediglich ein `.format()` aus und injiziert Hardware-Variablen und Ergebnislogs in das YAML-Template.
- **Data-Coupling & Regex-Integration:** Das System injiziert Metadaten (Token-Limits, Loop-Errors, ausgelöste Safety-Protokolle) via Warnblöcke direkt in die auszuwertenden Markdown-Logs. Der Evaluierungs-Flow parst diese Metadaten über vordefinierte Regex-Muster oder ID-Anker (z. B. "7.2.001"). Das befähigt den Judge, Modelle ganzheitlich – einschließlich technischer Flaws – zu bewerten. Hartes Grammar-Enforcement im Prompt verhindert Halluzinationen über einen aktiven Willen der KI-Modelle.

---

## Layer 2: Benchmark-Module

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

---

### Modul-Discovery (Config-First)

**Ablauf:**

1. Framework parst `benchmark_config.yaml`
2. Filtert Module mit `enabled: true`
3. Lädt `benchmark_modules/<module_id>/config.yaml`
4. Importiert `test_class` dynamisch
5. Instanziiert Test-Objekt
6. Führt `execute()` aus

**Wichtig:** Neue Module lassen sich hinzufügen, ohne Framework-Code zu ändern.

---

## Layer 3: Scoring Engine

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

---

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

## Layer 4: Datenpersistenz

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

---

---

### Model-ID-System & Card-Pfad-Architektur (v3.5.9)

#### Modell-ID als primärer Schlüssel

Jede Modell-ID ist der einzige Schlüssel, der Config, CSV und Model Card verbindet. Die ID kommt aus `benchmark_config.yaml → providers.<section>.<provider>.models[].id` und wird **unverändert** in alle drei Benchmark-CSVs geschrieben.

Provider-IDs unterliegen zwei Regimes:

| Regime | Beispiel | Handlungsregel |
|---|---|---|
| **Pinned Checkpoint-Slug** | `moonshotai/kimi-k2-0711` | Bevorzugt — Daten werden dem exakten Checkpoint zugeordnet |
| **Floating Alias** | `mistral-large-latest` | Akzeptabel wenn Provider keine Versionskennung anbietet |

#### Card-Pfad-Helfer als SSoT

Alle Card-Pfadoperationen laufen durch drei Funktionen in `utils/model_utils.py`:

```python
CARD_DIR          # Path("benchmark_scores/model_cards") — nie inline
_safe_name(id)    # re.sub(r'[:/.\  ]', '_', id) — kanonische Transformation
_card_path(model_id, provider, for_write)  # Drei-Regeln-Lookup
_find_card(model_id)                       # Provider-unbekannter Lookup
```

Die drei Naming-Regeln:

1. **Namespaced IDs** (`/` enthalten): `safe_name.json` — Provider-Namespace ist eingebettet
2. **Direct-API** (Shortcode `API`): `safe_name.json` — proprietäre Namen sind global eindeutig
3. **Non-namespaced + non-API** (`LCL`, `GR`): `{SHORTCODE}_safe_name.json` — verhindert Card-Kollisionen wenn dasselbe Modell über mehrere Provider getestet wird (z.B. `llama3.3:70b` via Ollama *und* Groq)

Backward-Compat: `_card_path(for_write=False)` fällt auf existierende Legacy-Cards ohne Prefix zurück.

**Niemals inline** `Path("benchmark_scores/model_cards") / f"{re.sub(...)}.json"` schreiben — diese Inline-Konstruktionen kennen die Drei-Regeln-Logik nicht.

#### Provider Shortcode System

Jeder Leaderboard-Eintrag trägt eine kombinierte Versionskennung (`k2-0711/OR`, `4-mini/API`, `4760c3/LCL`).

| Shortcode | Bedeutung | Provider-Schlüssel |
|---|---|---|
| `API` | Proprietäre Direkt-API | Anthropic, OpenAI, Google, xAI, Mistral |
| `OR` | OpenRouter | `openrouter` |
| `GR` | Groq | `groq` |
| `LCL` | Lokales Ollama-Modell | `ollama_local` |

SSoT: `_PROVIDER_SHORTCODES`-Dict in `utils/model_utils.py` + `short_code`-Feld pro Provider-Block in `benchmark_config.yaml` (beide müssen synchron gehalten werden).

**Datenfluss:**

1. Benchmark-CSVs speichern **nackte Version** (z.B. `k2-0711`, `4-mini`, `latest`) — kein Shortcode.
2. `score_calculator.py` aggregiert via `groupby`; `provider`-Spalte geht dabei verloren.
3. `scripts/leaderboard/__init__.py` re-attachiert `provider` nach `calculate_scores()` per pandas `mode()`-Merge.
4. `scripts/leaderboard/exporter.py` erzeugt daraus:
   - **Kompakt-CSV** (`benchmark_leaderboard.csv`): `Version` = kombinierter String (`k2-0711/OR`)
   - **Detailliert-CSV** (`benchmark_leaderboard_detailed.csv`): `Version` + `Provider Code` als separate Spalten + `model_id` (rohe Config-ID als SSOT für Downstream-Tools)

> **Vollständige Dokumentation des Modell-ID-Systems** (Naming-Regeln, Helper-API, Card-Generierungsprozess): [DEVELOPER_GUIDE.md — Modell-IDs, Card-Benennung & Versionierung](DEVELOPER_GUIDE.md)

---

### Web Export Pipeline

**Einstiegspunkt:** `make web-export` → `scripts/web_export.py`

Der Web Exporter ist ein eigenständiger Publishing-Schritt (Layer 4 Downstream), der vollständig vom Core-Benchmark-Loop entkoppelt ist. Er liest ausschließlich aus bereits generierten Artefakten und schreibt in das externe Frontend-Repository.

**SSOT-Prinzip:** Die Leaderboard-CSV ist die einzige Datenquelle. Ein vollständiger Rebuild (`shutil.rmtree` auf `models/`) stellt sicher, dass der Export immer synchron mit dem Leaderboard ist — Modelle die nicht in der CSV stehen, erscheinen nicht im Export.

**Model Cards & Provider Cards:** Strukturierte JSON-Steckbriefe pro Modell (`benchmark_scores/model_cards/`) und pro Provider (`benchmark_scores/provider_cards/`), generiert via LLM (`make model-cards`, `make provider-cards`). Sie enthalten Entwickler, Herkunftsland, Stärken/Schwächen, Datenschutz-Metadaten und Sovereign-Risk-Einschätzung. Die Cards werden (a) als Kontext-Block in den Meta-Reviewer injiziert und (b) als eigenständige JSON-API für das Web-Frontend bereitgestellt.

**Lizenz-Metadaten (Kernziel des Benchmarks):** Jede Model Card enthält `license`, `license_url` und `commercial_use_allowed`. Diese Felder beantworten die Kernfrage von CrucibleMark: Wie gut schlagen sich selbstgehostete Open-Weights-Modelle als datenschutzkonforme, manipulationsfreie Alternative gegen proprietäre Cloud-Modelle — und welche davon sind frei einsetzbar (`commercial_use_allowed: true`, z. B. Apache 2.0 / MIT) versus Open-Weights mit eingeschränkten Lizenzen (Meta Community License, GLM-4 License) oder reinen Cloud-Diensten (`Proprietary`)? `commercial_use_allowed: null` markiert Modelle mit skalenabhängigen oder unklaren Bedingungen.

**Verzeichnis-Auflösung (SSOT via `model_id`):** Audit-Log-Verzeichnisse und Review-Verzeichnisse werden nach `model_id.replace('/', '_')` benannt (identisch zu `benchmark_utils.py`). `web_export.py` liest die `model_id`-Spalte aus `benchmark_leaderboard_detailed.csv` und wendet dieselbe Transformation an — kein Raten aus dem Display-Namen mehr. Zwei explizite Fallbacks decken historische Daten ab: (1) Date-Suffix strip für Reviews, die vor der versioned model_id angelegt wurden; (2) Suffix-Match für Dirs ohne Provider-Präfix.

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

---

### Backup-Strategie (Snapshot & Prune)

**Workflow** (`make backup`):

1. **Snapshot:** Archiv erstellen
2. **Prune JSON-Logs:** Nur letzte fünf Runs behalten
3. **CSV-Konsolidierung:** Nur neueste Zeile pro (Modell, Asset)

**Effekt:** CSV-Dateien bleiben < 5 MB

**Siehe:** `docs/BACKUP_STRATEGY.md`

---

## Observability & Logging

### „Silent Console, Noisy Log" Strategie

#### 1. Console (User-Facing)

```python
print("✅ Code Quality: 85%")
print("⏳ Testing Reasoning Module (2/7)...")
```

Warnings von Drittanbieter-Bibliotheken werden unterdrückt.

---

#### 2. Log-Datei (Developer-Facing)

**Pfad:** `logs/crucible.log`

**Inhalt:**

- Alles (Level: DEBUG)
- Inkl. unterdrückter Warnings
- Tracebacks bei Exceptions

---

## Bekannte technische Schulden

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

## Roadmap

Die v1.x-Roadmap ist abgeschlossen. Die aktuelle Roadmap (Agentic Benchmarks, Multimodal, Web-UI, CI/CD) steht in [README.md](../README.md).

---

## Anhang: Design-Patterns

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
        result = self.score_response(result)      # Override
        self.save_to_csv(result)
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

**Dokumenten-Version:** 3.6.0 (Überarbeitung Mai 2026)\
**Kompatibel mit:** CrucibleMark v3.6.0+
