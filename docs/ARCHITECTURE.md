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

1. **Config-First:** Alle Module entdeckt das Framework via `benchmark_config.yaml` und `config/provider_config.yaml` (kein Hardcoding)
2. **Provider-Agnostisch:** Module wissen nicht, ob sie Ollama, llama.cpp oder GPT-4 testen
3. **Stateless Runs:** Jeder Benchmark ist unabhängig (keine Cross-Run-Pollution)
4. **Reproducibility:** Fixe Seeds und deterministische Prompts

---

## Layer-Architektur

```text
┌─────────────────────────────────────────────────────┐
│ Layer 1: Framework Core (Orchestration)            │
│ - Benchmark Runner (run_benchmark.py)              │
│ - Config Manager (benchmark_config.yaml +          │
│   config/provider_config.yaml, gemergt via         │
│   ConfigValidator)                                 │
│ - Provider Abstraction (Ollama, llama.cpp, OpenAI, │
│   Mistral, …)                                      │
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
│ - Vendor Cards (benchmark_scores/vendor_cards/)│
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Layer 5: Publishing (Downstream, entkoppelt)        │
│ - Meta-Reviewer (generate_review.py)               │
│ - Web Export Pipeline (scripts/web_export/)        │
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
- `cloud_models_benchmark.csv` (Open-Weights-Modelle auf Cloud-/Server-Infrastruktur: OpenRouter, Groq LPU)
- `commercial_models_benchmark.csv` (Closed-Source-Modelle, ausschließlich über proprietäre API verfügbar: OpenAI, Anthropic, Google, xAI, Mistral)

> **Benchmark-Philosophie:** `cloud_models_benchmark.csv` enthält bewusst **keine** lokalen Modelle. Open-Weights-Modelle wie Kimi K2 oder Qwen 3 werden hier auf der Infrastruktur gemessen, auf der sie mit kommerziellen Modellen konkurrieren — Cloud-Server oder LPU-Cluster, nicht Desktop-VRAM. Die Kernfrage lautet: *Wie stark sind Open-Weights-Modelle auf gleichwertiger Infrastruktur im Vergleich zu Closed-Source-APIs?*
>
> **Terminologie:** „Open Weights" ≠ „Open Source". Open-Weights-Modelle (z. B. Llama, Kimi K2, Qwen) veröffentlichen ihre trainierten Gewichte unter permissiven Lizenzen (Apache 2.0 o. ä.), legen aber Trainingsdaten, Trainings-Code und vollständige Architektur-Details in der Regel **nicht** offen. Sie sind damit öffentlich nutzbar, aber nicht im klassischen Open-Source-Sinne inspizierbar. CrucibleMark adressiert genau diese Intransparenz: Durch Beleuchtung des Verhaltens aus mehreren Perspektiven (Code, Logik, Sprache, Kultur) entsteht eine empirische Einordnung, die sonst mangels Quelleinsicht nicht möglich wäre.

**Delegate-Script-Mechanismus (spezialisierte Sub-Runner):**

Nicht alle Benchmark-Module laufen über den `UnifiedBenchmarkRunner`. Module mit komplexen, eigenständigen Execution-Anforderungen können in `benchmark_config.yaml` unter `execution.delegate_script` ein dediziertes Sub-Runner-Skript registrieren. `benchmark_auto.py` erkennt diesen Key und delegiert die gesamte Ausführung für dieses Modul per `subprocess.run()` an das Skript — statt `UnifiedBenchmarkRunner` zu instanziieren.

```yaml
# benchmark_config.yaml — Beispiel
tooluse:
  execution:
    execution_mode: delegate
    delegate_script: scripts/run_tooluse_benchmark.py
    delegate_extra_args: ["--audit"]
```

Aktuell genutzte Delegate-Module:

| Modul | Sub-Runner | Besonderheit |
|---|---|---|
| `political_compass` | `scripts/core/run_cross_model_benchmark.py --module political_compass` | Batch-Modus: 81+ Fragen pro Modell, eigene CSV-Architektur (`political_compass_results.csv`, `political_compass_leaderboard.csv`) |
| `tooluse` | `scripts/run_tooluse_benchmark.py` | Benötigt aktiven MCP-Server; Zwei-Phasen-Scoring; eigene Leaderboard-CSV |

**Skip-Logik für Delegate-Module:** `benchmark_auto.py` prüft vor dem Delegate-Aufruf anhand der jeweiligen Leaderboard-CSV (z. B. `political_compass_leaderboard.csv`), ob ein Modell bereits getestet wurde. Das vermeidet teure Re-Runs ohne `--force`.

**Verantwortlichkeiten (Shared Framework):**

- Config-Parsing
- Modul-Discovery (nur aktive Module laden)
- Execution-Flow (Standard via `UnifiedBenchmarkRunner`, spezialisiert via `delegate_script`)
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

### Lokale Connector-Topologie (llama.cpp)

CrucibleMark unterscheidet zwei lokale Betriebsformen für llama.cpp:

1. **On-Device lokal (`llamacpp`):** Benchmark-Runner und llama-server laufen auf derselben Maschine (z. B. Mac).
2. **Intranet-lokal (`llamacpp_spark`):** Benchmark-Runner läuft lokal auf dem Mac, steuert den llama-server aber per SSH auf einem Intranet-Host (DGX Spark).

Gemeinsame Invarianten beider Connectoren:

- Modellwechsel erfolgt als Stop + Start (kein Reload-API-Zwang im Framework).
- Ein Modell gilt erst als startklar nach doppelter Prüfung: Health-Endpunkt plus kurzer Probe-Completion-Request mit einem einfachen `Hallo`.
- Ein fremder aktiver OpenAI-kompatibler Endpoint unter derselben `base_url` wird nicht automatisch gestoppt oder übernommen.
- Readiness akzeptiert neben sichtbarem Content auch gültige Completion-Signale ohne sichtbaren Text (`reasoning_content`, `finish_reason`, `usage.total_tokens`).
- Für identisches bereits aktives Modell nutzt der Connector ein Warmup-Wartefenster statt eines sofortigen Abbruchs.

Spark-spezifische Besonderheiten:

- Steuerkommandos (`server_start_cmd`, `server_stop_cmd`) sind SSH-basiert.
- Optionaler End-of-Run-Cleanup (`cleanup_on_exit`) mit zusätzlichem Cache-Clear (`server_post_stop_cmd`).
- Bei Endpoint-Konflikten wird nur gewarnt; der Lauf bricht kontrolliert ab statt den fremden Server zu überschreiben.
- Seit v4.3.0 erzwingt `UnifiedBenchmarkRunner.run_benchmark()` den lokalen Provider-Cleanup in `finally`; bei `cleanup_on_exit: true` werden Stop- und Post-Stop-Kommandos auch bei Abbruch ausgeführt.

**Spark Token-Management (Session 26):**

Der `llamacpp_spark`-Server ist ein eigenständiger llama.cpp-Prozess mit eigenem Kontextfenster. Drei Config-Ebenen steuern das Token-Verhalten pro Modell:

| Config-Ebene | Feld | Server-Flag | Wirkung |
|---|---|---|---|
| 1. Kontextfenster | `context_length` | `--ctx-size` | KV-Cache-Größe beim Serverstart (Input + Output gemeinsam) |
| 2. Output-Cap | `max_tokens` | HTTP `max_tokens` | Maximale Output-Tokens pro einzelner Anfrage |
| 3. Parallelität | `parallel` | `--parallel` | Gleichzeitige Request-Slots (KV-Cache-Multiplikator) |

**Kardinalregel:** `max_tokens` muss kleiner sein als `context_length`, und der httpx `read_timeout` muss groß genug sein für `max_tokens / tokens_per_second`. Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster → HTTP-Read-Timeout-Loop.

**Per-Model-Cap-Logik** (`llamacpp_base.py:query()`, ab Session 26):
Nach `resolve_token_budget()` wird der per-Model `max_tokens` aus der provider_config angewendet:
```python
model_cfg_max_tokens = self._model_cfg(model).get("max_tokens")
if model_cfg_max_tokens is not None:
    initial_tokens = min(initial_tokens, model_cfg_max_tokens)
```

**`read_timeout`-Konfiguration** (ab Session 26):
Der httpx Read-Timeout wird provider-seitig konfiguriert (`provider_config.yaml → read_timeout`), Default 300s. Für `llamacpp_spark` auf 2400s gesetzt (40 Min), da lokale 27B-Modelle bei 10-15 t/s für 16K Output-Tokens ~22 Minuten benötigen.

**Empfohlene Spark-Config pro Modell:**
```yaml
- id: my-model
  context_length: 32768     # Explizit statt Provider-Default (65536)
  max_tokens: 16384         # Output-Cap (Hälfte von context_length)
  parallel: 2               # Provider-Default; 1 für Hybrid-Attention-Modelle
```

**`reasoning_content`-Verhalten bei Thinking-Modellen:**
llama.cpp-Modelle mit `--reasoning on` geben Thinking-Inhalte im separaten API-Feld `reasoning_content` zurück (nicht im Standard-`content`). `_extract_response_content()` in `llamacpp_base.py` extrahiert beide Felder. `reasoning_tokens` wird bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` gelesen (llama.cpp-native), Fallback auf `completion_tokens` nur wenn Content leer. Das `think_content`-Feld in der CSV enthält den vollständigen Thinking-Block.

| Provider | Auth | Token Limit | Streaming | Retry Logic | Besonderheiten |
|----------|------|-------------|-----------|-------------|----------------|
| Ollama | Keine (localhost) | Modellabhängig (8K–128K) | ✅ | N/A (lokal) | `finish_reason` + `tps_eval` aus Ollama-Metadaten; `usage` aus `prompt_eval_count`/`eval_count` synthetisiert |
| OpenAI | Bearer token | 128K (GPT-4) | ✅ | 429 → Exponential Backoff | `reasoning_tokens` aus `usage.completion_tokens_details`; `think_content` aus `msg.reasoning` |
| Mistral | API key | 32K | ❌ | 500 → 3× Retry | ThinkChunk-Handling für Magistral (Streaming-Artefakt); `think_content` aus `chunk.thinking` |
| Anthropic | API key | 200K | ✅ | 429 → Exponential Backoff | `stop_reason` → normalisiert zu `finish_reason`; `think_content` aus ContentBlock `type="thinking"`; Streaming mit `thinking_delta`-Events |
| Google | API key | 1M–2M | ❌ | SDK-seitig | `STOP` uppercase → normalisiert; `think_content` aus `candidates[0].content.parts[].thinking`; `thoughts_token_count` für Reasoning-Token-Count |
| OpenRouter | Bearer token | Modellabhängig | ✅ | Im Wrapper | **Reasoning-Token-Budget** (siehe unten); Free-Tier-Modelle (`vendor/model:free`) nutzen separates Rate-Limit-Profil (`openrouter_free`, 18 RPM); `think_content` aus `msg.reasoning`/`msg.reasoning_content` |
| xAI | Bearer token | Modellabhängig | ✅ | Im Wrapper | `finish_reason` aus Streaming-Chunks extrahiert; `reasoning_tokens` aus `usage.completion_tokens_details` |
| Groq | Bearer token | Modellabhängig | ✅ | Im Wrapper | `max_completion_tokens` statt `max_tokens` (config-getrieben); `reasoning_tokens` aus `usage.completion_tokens_details` |
| Cohere | API key | 128K (Command) | ❌ | 500 → 2× Retry (Backoff) | **Native `tools`-API für ToolUse-Modul** (v4.10.8); Prompt-basierte Tool-Schemas kollidieren mit Reasoning-Modellen; `thinking: {"type": "disabled"}` bei Native Tools; `command-a-plus`: MoE-Instabilität bei komplexen Prompts (HTTP 500) |

**vLLM Dual-Thinking-Profile (ab Session 52):**

vLLM-Modelle mit `enable_thinking: true` werden beim Config-Load automatisch in zwei Benchmark-Profile expandiert — ein Container bedient beide per-Request, ohne Server-Neustart beim Profil-Wechsel.

| Aspekt | Mechanik |
|---|---|
| **Expansion-Trigger** | `enable_thinking: true` im model_cfg (nur `api_type == "vllm"`) |
| **Standard-Profil** | `{id}` mit `chat_template_kwargs: {"enable_thinking": false}`, `max_tokens` aus Config |
| **Thinking-Profil** | `{id}-thinking` mit `chat_template_kwargs: {"enable_thinking": true}`, `max_tokens: thinking_max_tokens`, `card_model_id: {id}` |
| **Container-Reuse** | `_active_config`-Tracking in `vllm_base.py` vergleicht `config:` (TOML) statt `model_id` → gleiche `config:` = kein Swap |
| **Card-Sharing** | `card_model_id`-Feld → `_find_card()` nutzt Original-Card für Thinking-Profil (deterministisch, kein Suffix-Stripping) |
| **Leaderboard** | Zwei separate CSV-Einträge (`{id}` + `{id}-thinking`), zwei Leaderboard-Einträge, eine geteilte Card |
| **`thinking_max_tokens`-Quelle** | model_cfg > provider > Fehler (kein Hardcoding) |

**Warum nur vLLM?** vLLM's `enable_thinking` ist ein Chat-Template-Kwarg (per-Request via `chat_template_kwargs`). llama.cpp's `enable_thinking` ist ein Server-Start-Flag (`--reasoning on`/`off`) — kann nicht per-Request gewechselt werden. Expansion läuft daher NUR für `api_type == "vllm"`.

**Provider Thinking/Reasoning-Extraktion (ab v4.10.1):**

Alle Provider-Connectors in `utils/providers/` extrahieren seit v4.10.1 konsistent drei Felder in `last_response_metadata`:

| Feld | Quelle | Konsument |
|------|--------|-----------|
| `reasoning_tokens` | `usage.completion_tokens_details.reasoning_tokens` (OpenAI-kompatibel), `usage.output_tokens_details.reasoning_tokens` (Anthropic), `usage_metadata.thoughts_token_count` (Google), `eval_count` (Ollama) | Judge-Evaluator (`judge_evaluator.py:272`), `base_runner.py:159` (Reasoning-Budget-Entscheidung) |
| `think_content` | `msg.reasoning`/`msg.reasoning_content` (OpenAI), `delta.reasoning` (OpenAI Streaming), `part.thinking` (Google), `block.thinking` (Anthropic), `delta.thinking`/`block.thinking` (Anthropic Streaming), `msg.thinking` (Ollama), `chunk.thinking` (Mistral) | Judge-Evaluator (`judge_evaluator.py:273`), `base_runner.py:163`, Audit-Log (`benchmark_utils.py:382`) |
| `usage` | `response.usage` (OpenAI/Anthropic/Mistral/OpenRouter/Groq/xAI), `usage_metadata` (Google), `{"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}` (Ollama) | `LLMParser.extract_usage_tokens()` (`llm_client.py:244`) — ermöglicht echte API-Token-Zählung statt `estimate_tokens()`-Fallback |

**Sonderfälle:**

- **OpenAI o-Series:** Reasoning wird intern verborgen — `reasoning_tokens` und `think_content` sind leer. Karten manuell mit `thinking_probe_manual_override: true` setzen.
- **Anthropic Extended Thinking:** `think_content` aus ContentBlock `type="thinking"` mit Thinking-Inhalt + `signature` (verifiziertes Thinking). Streaming über `content_block_start`/`content_block_delta` mit `type="thinking_delta"`.
- **Google Gemini:** `thoughts_token_count` ist kumulativ — letzter Chunk hält den finalen Wert (nicht addieren).
- **Ollama:** Keine separate `reasoning_tokens`-API — `eval_count` wird als Reasoning-Count verwendet wenn Thinking erkannt wurde (sonst Output-Token-Count).
- **Groq/xAI:** Reasoning-Unterstützung in `usage` prüfen — `completion_tokens_details.reasoning_tokens` ist OpenAI-kompatibel und verfügbar.
- **Cohere (ab v4.10.8):** ToolUse-Modul nutzt Cohere-native `tools`-API statt Prompt-basierte JSON-Schemas. Reasoning-Modelle (`command-a-plus`, `command-a-reasoning`) werden über `_is_cohere_reasoning_model()` erkannt (Substring-Match). `thinking: {"type": "disabled"}` bei Native Tools verhindert 422. `command-a-plus` hat persistente 500er bei Benchmark-Prompts (MoE-Instabilität) — `supports_tool_use=false`.

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

**Reasoning-Erkennung (ThinkingProbe) & Card-First Workflow (ab v3.5.8, erweitert v4.7.2/3):**
Um `is_reasoning_model()` empirisch statt heuristisch zu fundieren, wurde die Probe-Infrastruktur in mehreren Stufen ausgebaut:

1. **`probe_thinking_model(model_id, provider_key, config, prompts=None)`** in `utils/model_utils.py` sendet Probe-Prompts an die Modell-API und wertet drei Signale aus:
   - **Signal A (Tags):** Einer von 13 bekannten Think-Tags im Response-Body (`<think>`, `<|thinking|>`, `<reasoning>`, `<reflection>`, `<scratchpad>`, `<solution>`, ...) → `confidence=high`. SSoT: `_THINK_TAGS` Tupel in `utils/model_utils.py`. Helper: `_find_think_tags()` (lowercase, Multi-Tag-aware).
   - **Signal B (reasoning_tokens):** `completion_tokens_details.reasoning_tokens > 0` in der API-Metadaten-Antwort → `confidence=medium`. **Sonderfall llama.cpp:** Modelle, die Reasoning über das Feld `reasoning_content` zurückgeben (z. B. Gemma-4 E4B), werden vom Standard-Probe nicht erkannt — `llamacpp.py` extrahiert dieses Feld explizit und setzt `reasoning_tokens = completion_tokens` intern. Diese Modelle benötigen `thinking_probe_manual_override: true` in der Model Card.
   - **Signal C (Inline-CoT, ab v4.7.2 rehabilitiert):** Heuristik im Content (`>200 chars` UND `≥2 Berechnungs-Operatoren/CoT-Tokens`) → `confidence=medium`. **Befund aus Discovery (9/9 Modelle, 100% Erkennungsrate):** Signal A ist bei `enable_thinking: false` (llama.cpp) und OpenRouter-Strip unzuverlässig; Signal B nur bei OpenRouter; Signal C ist der einzige robuste Trigger über alle Provider.

2. **Multi-Prompt-Aggregation (ab v4.7.2):** `_PROBE_PROMPTS` Dict mit drei Domänen (math/code/decision). Höchste Confidence gewinnt. Bei `prompts=None` (Default) werden alle drei Prompts gesendet; Single-Prompt-Modus bleibt für Card-First-Hook erhalten. Aggregation: wenn irgendein Prompt `detected=True` liefert, ist das Gesamtergebnis `detected=True` mit kombinierter Evidence.

3. **`ThinkingProbeResult`** (Dataclass, ab v4.7.2 mit Backward-Compat-Defaults): `detected: bool`, `evidence: str`, `confidence: Literal["high","medium","low"]`, `prompts_used: list[str]`, `tags_found: list[str]`.

4. **`is_reasoning_model_from_card(model_id)`:** Liest `thinking_probe_detected` aus der JSON-Model-Card. Dateiname-Auflösung via `_find_card(model_id)` (SSoT — inkl. `-latest`-Alias-Fallback). Gibt `None` zurück wenn kein Eintrag vorhanden.

5. **`is_reasoning_model()` Lookup-Hierarchie:**
   1. Card-Lookup (`is_reasoning_model_from_card()`) — hat immer Vorrang
   2. String-Trigger-Heuristik als Fallback

### SSoT-Auflösung Card + Override (ab v4.7.1, erweitert v4.7.3)

**Architektur:** `resolve_effective_thinking(model_card, provider_model_cfg, *, model_id, now)` in `utils/model_utils.py` ist die **Single Source of Truth** für das effektive Thinking-Flag. Auflösungs-Priorität:

```
1. aktiver thinking_override?  → (override_value, "override")  + Audit-Log [ThinkingOverride]
2. Card thinking_probe_detected? → (card_value, "card_probe")
3. nichts                       → (None, "none")
```

**Override-Schema** in `config/card_template_vendor.yaml` (Optionalfeld, `since v4.7.1`):

```yaml
thinking_override:
  value: false                              # bool, Pflicht
  reason: "Cost-Benchmark: CoT-Suppression"  # Pflicht (Whitespace-only zählt als leer)
  active_until: "2026-12-31"                # Optional, ISO-8601, Auto-Expiry
```

Aktivierungs-Regeln (`_is_override_active`): `value` muss bool sein, `reason` Pflicht, `active_until` muss in der Zukunft liegen (naive wird UTC), sonst Card-Probe gewinnt automatisch. Drift-Schutz durch Auto-Expiry.

### Runner-Consumer-Anbindung (ab v4.7.3)

`utils/base_runner.py:121` reicht `provider=provider` an `resolve_token_budget()` durch, damit ein aktiver `thinking_override` das Token-Budget beeinflusst. `resolve_token_budget(..., *, provider=None)` löst die SSoT-Hierarchie auf:

1. `provider=None` (Backward-Compat) → `is_reasoning_model()` mit Trigger-Fallback
2. `provider="..."` → `load_vendor_card()` → `resolve_effective_thinking()` mit Override + Card-Probe
3. Override aktiv → Override-Wert gewinnt (Audit-Log)
4. Card-Probe gesetzt → Probe-Wert gewinnt
5. Keine Info → Trigger-Liste

**Effekt:** `thinking_override.value: false` in Provider-Card schaltet den 5×-Reasoning-Multiplikator **aus** (Cost-Benchmark-fair). `value: true` schaltet ihn an (A/B-Test auf Non-Reasoning-Modell). Card-Probe `false` gewinnt über magistral-Trigger im Namen. 5 alte Call-Sites (`mistral.py`, `openrouter.py`, `openai.py`, `llamacpp_base.py`) funktionieren unverändert ohne `provider`-Argument.

**Discovery-Inventar** (3 Wellen, 9 Modelle, 27 Probes, 2026-06-09): siehe `docs/THINKING_TAGS_INVENTORY.md` + `_M4/_SPARK/_CLOUD.md` für Roh-Daten pro Familie. Methodik-Doku: `docs/THINKING_PROBE.md`.

5. **`_ensure_model_card()` Hook in `unified_runner.py`:** Vor dem ersten Benchmark-Run eines Modells:
   - Card mit `thinking_probe_detected`-Feld → Skip
   - Card ohne Feld → Probe → Feld in Card eintragen
   - Keine Card → Probe → Minimal-Card erstellen (`card_status: "minimal"`)
   - Probe-Fehler 429 (Wochenlimit) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter
   - Probe-Fehler 403 (Subscription) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter
   - Probe-Fehler (sonstiger) → clean Warning, Modell in `_probed_models`, Benchmark läuft weiter

6. **`scripts/tools/probe_thinking.py`** (Standalone-CLI): Retroaktiver und On-Demand-Probe-Betrieb. Modi: `--model <id>`, `--missing` (Batch: alle Cards ohne Feld), `--all` (Force-Rescan). Provider-Inference: Config → `/` im ID → `openrouter` → sonst `ollama`. Batch-Modus bricht bei Einzelfehlern nicht ab.

> **Wichtig:** Zwei Modellklassen können via Probe nicht erkannt werden und benötigen manuellen Override: (1) **OpenAI o-Series** (o1/o3-mini/o4-mini) — verbergen Reasoning intern, liefern keine `reasoning_tokens`. (2) **llama.cpp-Modelle mit `reasoning_content`-Feld** (z. B. Gemma-4 E4B) — Reasoning landet in einem separaten API-Response-Feld, das der Standard-Probe nicht auswertet. Für beide Klassen gilt: `thinking_probe_detected: true` + `thinking_probe_manual_override: true` manuell in der Card setzen.

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

Jede Modell-ID ist der einzige Schlüssel, der Config, CSV und Model Card verbindet. Die ID kommt aus `config/provider_config.yaml → providers.<section>.<provider>.models[].id` und wird **unverändert** in alle drei Benchmark-CSVs geschrieben.

> **Duplikat-Schutz:** `ConfigValidator` prüft beim Laden alle expliziten Modell-IDs über alle Provider hinweg. Taucht eine ID mehrfach auf, wird eine `WARNING` geloggt; der erste Eintrag gewinnt (First-Win). `auto_discover`-Provider (Ollama) werden vom Check ausgenommen.

**`resolve_provider(model_id)` — SSoT für Provider-Inference:**
`utils/model_utils.py` durchsucht beim Auflösen eines Provider-Keys **beide** Config-Dateien der Reihe nach: zuerst `benchmark_config.yaml`, dann `config/provider_config.yaml`. Damit werden auch Modelle, die nur in `provider_config.yaml` konfiguriert sind (z. B. llamacpp-Modelle), korrekt ihrem Provider zugeordnet — ohne manuelle Doppel-Eintragung in `benchmark_config.yaml`.

Provider-IDs unterliegen zwei Regimes:

| Regime | Beispiel | Handlungsregel |
|---|---|---|
| **Pinned Checkpoint-Slug** | `moonshotai/kimi-k2-0711` | Bevorzugt — Daten werden dem exakten Checkpoint zugeordnet |
| **Floating Alias** | `mistral-large-latest` | Akzeptabel wenn Provider keine Versionskennung anbietet |

#### Card-Pfad-Helfer als SSoT

Alle Card-Pfadoperationen laufen durch die ID-SSoT-Funktionen in `utils/model_utils.py`:

```python
CARD_DIR                                # Path("benchmark_scores/model_cards") — nie inline
normalize_model_id(id)                  # strippt hf.co/AUTHOR/-Präfix
_safe_name(id)                          # re.sub(r'[:/.\  ]', '_', id) — kanonische Transformation
strip_date_suffix(id)                   # entfernt -YYYYMMDD / -MMDD-Suffixe
resolve_canonical_model_id(id)          # Bridge: kanonische Form (Card-Lookup + Suffix-Strip + safe_name fallback)
enforce_card_first(id) -> (id, bool)    # Card-First-Vertrag: garantiert Card-Existenz (Draft falls fehlt)
_card_path(model_id, provider, for_write)   # Drei-Regeln-Lookup
_find_card(model_id, card_dir=None)         # Provider-unbekannter Lookup; card_dir für externe Pfade
WEIGHTS_TIER_DISPLAY                        # Tier → Display-String (SSoT, importierbar)
```

**Card-First-Vertrag:** `enforce_card_first()` ist die zentrale
Durchsetzungsstelle (genutzt in `utils/result_manager.py::save_results`).
Card vorhanden → `(canonical, True)`; fehlt → `ensure_card()` legt
Platzhalter-Draft an, WARNING wird geloggt (`kein Hard-Fail`). Damit ist
jede in CSVs geschriebene `model_id` garantiert durch eine Card im
Filesystem abgedeckt.

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
| `LCL` | Lokales llama.cpp-Modell | `llamacpp` |

SSoT: `_PROVIDER_SHORTCODES`-Dict in `utils/model_utils.py` + `short_code`-Feld pro Provider-Block in `config/provider_config.yaml` (beide müssen synchron gehalten werden).

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

**Einstiegspunkt:** `make web-export` → `python -m scripts.web_export` (Package `scripts/web_export/`, aufgespalten ab v4.10.18)

Der Web Exporter ist ein eigenständiger Publishing-Schritt (Layer 4 Downstream), der vollständig vom Core-Benchmark-Loop entkoppelt ist. Er liest ausschließlich aus bereits generierten Artefakten und schreibt in das externe Frontend-Repository.

**SSOT-Prinzip:** Die Leaderboard-CSV ist die primäre Datenquelle für Scores und Metadaten. Ein vollständiger Rebuild (`shutil.rmtree` auf `models/`) stellt sicher, dass der Export immer synchron mit dem Leaderboard ist — Modelle die nicht in der CSV stehen, erscheinen nicht im Export.

**Interne Architektur — Anti-God-Script (ab v3.7.3):**
`main()` ist ein schlanker Orchestrator (~80 Zeilen). Alle fachlichen Blöcke sind in 10 Top-Level-Hilfsfunktionen ausgelagert (alle mit vollständigen Type Hints, mypy-kompatibel):

| Funktion | Verantwortung |
|---|---|
| `load_csv_with_fallback(path)` | Lädt CSV sicher; gibt `None` bei Fehler statt Exception |
| `_resolve_dir(dirs, raw_slug)` | Löst model-ID-Slug → Verzeichnispfad (Direkt-Match SSoT + 3 Robustheits-Fallbacks für historische Dirs) |
| `_setup_output_dirs(args)` | Safety-Guard + `shutil.rmtree(models/)` + Verzeichnis-Init |
| `_load_sources(scores_dir)` | Lädt alle 4 Quell-CSVs zentral |
| `_build_pc_lookups(pc_lb)` | Baut PC-Leaderboard-Dicts (model_name + slug-Schlüssel) |
| `_load_pc_block_meta(config_path)` | Lädt Block-Metadaten aus `political_compass/config.yaml` (Fallback: statisches Dict) |
| `_export_model_files(model_out, audit_src, comp_src)` | Kopiert Audit-Logs + Review-Markdowns für ein Modell |
| `_build_leaderboard_entry(row, card, ...)` | Baut den vollständigen Leaderboard-Dict (~45 Felder); top-level `model_id` aus Card; `size_class` Card-prioritär; `model_card`-Objekt mit 35 Feldern (inkl. Pricing, `weights_license_tier`, `thinking_probe_*`, `heritage_ids`, ab v4.10.14 `quantization_format`/`model_variant`) |
| `_lookup_pc_row(model_name, slug, pc)` | Sucht AVG-Zeile in PC-Resultaten (exakt + slug-Fallback) |
| `_build_compass_entry(pc_row, lb_row, ..., block_meta)` | Baut den Political-Compass-Dict inkl. Archetyp-Felder |
| `_write_top_level_outputs(...)` | Schreibt `leaderboard.json`, `political_compass.json`, `provider_stats.json`, `meta.json` |

`WEIGHTS_TIER_DISPLAY` (Tier-String-Mapping) ist als öffentliche Konstante aus `utils/model_utils.py` importiert — `scripts/web_export/` führt kein Duplikat mehr. `load_model_card()` delegiert die Card-Pfad-Auflösung an `_find_card(card_dir=card_dir)` (SSoT) und behält nur die zwei web-spezifischen Fallbacks (Display-Name-Vollscan, hf.co-Suffix-Match). Block-Metadaten für den Political Compass kommen via `_load_pc_block_meta()` aus `benchmark_modules/political_compass/config.yaml` (Fallback: statisches Dict) — kein hardcodiertes Python-Dict mehr.

**Nullwert-Entfernung (ab v4.10.0):** `strip_none()` (in `utils/text_helpers.py`, Sektion-F-Refactor) entfernt `None`-Werte rekursiv aus allen exportierten Dicts (`leaderboard`-Entry, `model_card`-Sub-Dict, `political_compass`-Entry, `data.json`). Felder mit Wert (`0`, `False`, `""`, `[]`) bleiben erhalten. `"model_card": null` wird komplett entfernt (Key fehlt im JSON statt `null` zu exportieren). Verhindert Nullwert-Noise im Frontend-Payload.

**Model Cards & Vendor Cards:** Strukturierte JSON-Steckbriefe pro Modell (`benchmark_scores/model_cards/`) und pro Provider (`benchmark_scores/vendor_cards/`). Vendor Cards enthalten ausschließlich Deployment- und Datenschutz-Metadaten (CLOUD Act, GDPR, Datenstandort, NSL-Risiko) — **keine** Preise und **keine** Stärken/Schwächen. Letztere leben in den Model Cards. Die Cards werden (a) als Kontext-Block in den Meta-Reviewer injiziert, (b) als eigenständige JSON-API für das Web-Frontend bereitgestellt und (c) von `risk_calculator.py` für die Sovereign-Risk-Berechnung genutzt. Preisinformationen (`input_price_per_1m`, `output_price_per_1m`) sind alleiniges SSoT-Feld der Model Cards (ab v3.7.5).

**Model Card Lifecycle (`card_status`):** Cards werden durch einen schlanken Template-Generator ohne API-Call erstellt (`make model-card MODEL=<id>` → `scripts/analysis/generate_model_cards.py`). Das erzeugte Template enthält alle Pflichtfelder mit `"TODO"`-Platzhaltern und `card_status: "draft"`. Nach manueller Recherche und Befüllung wird `card_status` auf `"complete"` gesetzt. Minimal-Cards, die der ThinkingProbe-Hook automatisch anlegt, erhalten `card_status: "minimal"` — diese brauchen keine manuelle Vervollständigung für den Benchmark-Betrieb, sind aber für den Web-Export unvollständig.

**Card-Research Verifikation (`profile_verified`):** `make card-research MODEL=all` verifiziert alle unverifizierten Cards automatisch via LLM (Gemma 4 lokal via llama.cpp). Der Flow: (1) Template-Prefill fehlender Felder, (2) Pre-Findings (Lizenz-Heuristik, Community-Check), (3) LLM prüft nur Textfelder (summary, strengths, known_limitations, judge_context_hint, weights_provenance_risk_rationale), (4) Post-Apply (Lizenz-Konsistenz, GGUF-Konventionen), (5) Finale Validierung. `profile_verified=true` wird nur gesetzt wenn alle required Felder befüllt sind und keine Fehler mehr vorliegen. Batch-Processing: `MAX_CARDS=N` limitiert pro Run, nächster Run erkennt bereits verifizierte Cards automatisch. `FORCE=1` verarbeitet alle Cards unabhängig vom Status.

**Optionale Template-Felder (seit v4.10.0):** `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m` sind optional — Beschreibungen sagten "null wenn X" aber `required: true` war ein Widerspruch. `is_unknown_sentinel(None)` returned `True`, also wird `null` bei `required: true` als Fehler gewertet. Lokale/proprietäre Modelle ohne Angaben werden dadurch nicht mehr blockiert.

`make clean-model --model <ID>` entfernt seit v3.8.1 automatisch alle Spuren eines Modells: CSV-Zeilen, `outputs/audit_logs/<dir>/`, `outputs/comparisons/<dir>/`, `outputs/runs/<dir>/`, `docs/reviews/<dir>/`, `outputs/cost_log.csv`-Einträge **und** die Model Card JSON (`benchmark_scores/model_cards/<card>.json`). Kein manueller Aufräumschritt mehr nötig. **Ab v4.10.7:** Alle ID-Varianten (Underscore, Hyphen, Punkt) werden automatisch via `_collect_model_id_variants()` erkannt und bereinigt. Reihenfolge: CSVs vor Cards (Card wird für Variant-Auflösung gebraucht).

**🛑 SSOT Modell-Kategorisierung (`weights_license_tier`):**
Die Anzeige-Kategorie eines Modells wird **ausschließlich** aus dem Feld `weights_license_tier` der Model Card abgeleitet — nicht aus der Leaderboard-CSV-Spalte `Type`, nicht aus der Herkunft der Benchmark-CSV und nicht aus Heuristiken über Modellnamen.

```
Model Card (weights_license_tier)  →  get_model_category()  →  Display-String
──────────────────────────────────────────────────────────────────────────────
"proprietary"       →  "Proprietär"         (API-only, Gewichte nicht öffentlich)
"restricted-weights"→  "Restricted Weights" (Gewichte verfügbar, Lizenz eingeschränkt)
"open-weights"      →  "Open Weights"        (frei, Apache 2.0 / MIT o. ä.)
```

Die Funktion `get_model_category()` in `utils/model_utils.py` ist der einzige Einstiegspunkt. Sie versucht zuerst den Card-Lookup — fällt sie zurück auf Config-Heuristiken (kein Card-Feld vorhanden), liefert sie ebenfalls einen der drei obigen Strings. Niemand darf diese Strings hardcodieren oder selbst ableiten.

`scripts/web_export/` überschreibt das `type`-Feld im Export zur Laufzeit aus der Model Card, so dass auch ältere Leaderboard-CSV-Zeilen (die noch alte Strings wie `"Open Weights (Cloud)"` enthalten können) sofort die korrekten Werte liefern — ohne CSV-Rebuild.

**Verbotene Altstrings (seit v3.7.0 abgelöst):** `"Open Weights (Cloud)"`, `"Open Weights (Local)"`, `"Commercial"`, `"Local"`, `"cloud"`, `"local"` als Kategorie-Display-Strings dürfen nicht mehr vergeben werden. Sie können in historischen CSVs noch vorkommen — das Frontend behandelt sie via Legacy-Fallback.

**Lizenz-Metadaten (Kernziel des Benchmarks):** Jede Model Card enthält `license`, `license_url` und `commercial_use_allowed`. Diese Felder beantworten die Kernfrage von CrucibleMark: Wie gut schlagen sich selbstgehostete Open-Weights-Modelle als datenschutzkonforme, manipulationsfreie Alternative gegen proprietäre Cloud-Modelle — und welche davon sind frei einsetzbar (`commercial_use_allowed: true`, z. B. Apache 2.0 / MIT) versus Open-Weights mit eingeschränkten Lizenzen (Meta Community License, GLM-4 License) oder reinen Cloud-Diensten (`Proprietary`)? `commercial_use_allowed: null` markiert Modelle mit skalenabhängigen oder unklaren Bedingungen.

**Verzeichnis-Auflösung (SSOT via `model_id`):** Audit-Log-Verzeichnisse und Review-Verzeichnisse werden aus der `model_id`-Spalte von `benchmark_leaderboard_detailed.csv` abgeleitet — kein Raten aus dem Display-Namen. Die Slug-Bildung läuft über die lokale `slugify()`-Funktion (Sonderzeichen → Bindestrich, lowercase, URL-sicher) und ist damit unabhängig von der Card-`_safe_name()`-Logik in `utils/model_utils.py` (kanonischer Card-Filename mit Underscore). Die Auflösung in `_resolve_dir(dirs, raw_slug)` (Top-Level) ist ein Direkt-Match (SSoT) plus drei Robustheits-Fallbacks für historische Verzeichnisnamen: (1) Date-Suffix-Strip für Reviews, die vor der versioned model_id angelegt wurden, (2) Suffix-Match für Dirs ohne Provider-Präfix, (3) `-latest`-Alias-Auflösung über `get_model_version()` aus `model_utils.py`. Der 4-Stufen-Fallback ist **kein** Workaround, sondern legitime Robustheit gegen Legacy-Dir-Namen aus der Pre-Versioned-ID-Ära.

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
4. **Clean Reviews:** Verwaiste Review-Verzeichnisse entfernen (`make clean-reviews`)
5. **Prune Orphans:** Audit-Log-Verzeichnisse ohne Leaderboard-Eintrag bereinigen (`make clean-model --prune-orphans`)

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

**Dokumenten-Version:** 4.10.17 (Ueberarbeitung 2026-07)\
**Kompatibel mit:** CrucibleMark v3.8.0+
