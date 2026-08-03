# Entwicklerhandbuch: CrucibleMark erweitern

**Stand: v5.1.0 · 2026-07-14**

**Zielgruppe:** Entwickler, die neue Test-Module erstellen oder das Scoring-System erweitern wollen.

**Inhalt:**

- Quick Start: Neues Modul in 15 Minuten
- Asset-Format & YAML-Schema
- Scoring-Logik implementieren
- CSV-Output & Leaderboard-Integration
- Tests & Validierung

> **Voraussetzung:** Grundkenntnisse in Python, YAML und Regex.

---

## 🛑 WICHTIG: Die 4 Design-Gesetze von CrucibleMark

Vor dem Schreiben eines neuen Moduls oder dem Erweitern von bestehendem Code **müssen** die obersten Architekturregeln dieses Projekts respektiert werden:

1. **Strict Separation of Concerns:** Die Datenmessung (Benchmark Loop) ist heilig, autark und darf NIEMALS durch Publishing-Funktionen blockiert werden.
2. **SSOT & DRY:** Jede Funktion hat **genau ein** Modul. Kein Code-Kopieren! Erweitere existierende Module (Open/Closed Principle).
3. **No Magic Numbers:** Alles läuft über YAML (Config-First). Keine hardkodierten Parameter im Code.
4. **Anti-God-Script:** Schütze das System vor monolithischen Skripten. Nutze gezielte Submodul-Breakouts.

> 📖 **Details zu diesen Regeln:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Quick Start: Neues Modul erstellen

### Option 1: Template kopieren (empfohlen)

Der einfachste Weg ist das Kopieren eines bestehenden Moduls als Template:

```bash
# Existierendes Modul als Vorlage kopieren
cp -r benchmark_modules/ux_writing benchmark_modules/your_module
```

Anschließend anpassen:
1. **Modul-ID umbenennen** in `config.yaml → metadata.id` und im Verzeichnisnamen
2. **Anzeigename + Beschreibung** in `config.yaml → metadata.name` / `description`
3. **Scoring-Logik** in `core/evaluators.py` ersetzen
4. **Test-Assets** in `assets/*.yaml` definieren

Für ein vollständig neues Modul siehe [ARCHITECTURE.md](ARCHITECTURE.md) → "Eigenes Benchmark-Modul erstellen".

---

### Development Loop & Testing

Für schnelle Iterationen ohne lange Wartezeiten den **Dev-Modus** nutzen:

```bash
# Startet Benchmark mit verkürzten Pausen (5-10s statt 20-30s)
make benchmark-dev
```

Oder direkt über das CLI:

```bash
python run_benchmark.py --dev --model ministral:8b
```

**Adaptive Pausen:**
Das Framework nutzt `utils/adaptive_pause.py` für dynamische Erholungspausen (wichtig für Mac M-Chips mit Unified Memory). Im Dev-Modus sind diese Pausen kürzer – das kann Performance-Messungen leicht verfälschen, reduziert aber die Entwicklungszeit erheblich.

---

### Option 2: Manuell (für volle Kontrolle)

```bash
# Struktur erstellen
mkdir -p benchmark_modules/your_module/{assets,core}
touch benchmark_modules/your_module/{__init__.py,test.py,config.yaml,README.md}
touch benchmark_modules/your_module/core/{__init__.py,evaluators.py,constants.py}
```

**Minimale Dateien:**

- `config.yaml` – Metadaten & Leaderboard-Config
- `test.py` – Runner (Controller)
- `core/evaluators.py` – Scoring-Logik
- `assets/*.yaml` – Test-Cases

---

## Modul-Anatomie

### Verzeichnis-Struktur

```text
benchmark_modules/
└── your_module/
    ├── README.md              # Dokumentation (Template siehe unten)
    ├── config.yaml            # ⚙️ SSOT (Single Source of Truth)
    ├── test.py                # 🎮 Controller (LLM-Ausführung)
    ├── assets/                # 📦 Test-Fixtures
    │   ├── your_module_001_task.yaml
    │   ├── your_module_002_task.yaml
    │   └── ...
    └── core/                  # 🧠 Business Logic
        ├── __init__.py
        ├── evaluators.py      # Scoring-Engine
        └── constants.py       # Schwellenwerte, Regex-Patterns
```

---

## Lokale OpenAI-kompatible Connectoren (llama.cpp)

Für `llamacpp` und `llamacpp_spark` gilt im aktuellen Stand:

- Die Startbereitschaft wird über `health` plus einen minimalen Completion-Probe-Request mit `Hallo` ermittelt.
- Die Probe akzeptiert auch valide Antworten ohne sichtbaren `content`, wenn z. B. `reasoning_content`, `finish_reason` oder `usage.total_tokens` vorliegen.
- Ein bereits aktiver fremder OpenAI-kompatibler Endpoint unter derselben `base_url` wird nicht automatisch gestoppt.
- Stattdessen gibt der Connector eine Warnung aus und der Benchmark-Lauf endet kontrolliert.
- Läuft dasselbe Zielmodell bereits auf dem Endpoint, nutzt der Connector ein Warmup-Fenster und adoptiert den laufenden Server statt vorschnell abzubrechen.

Für `llamacpp_spark` sind im Regelfall nur diese provider-spezifischen Keys relevant:

- `base_url`, `model_dir`, `server_start_cmd`, `server_stop_cmd`
- `server_ready_timeout_sec`, `server_ready_poll_sec`, `server_ready_probe_timeout_sec`
- `server_log`, `bind_host`, `threads`, `parallel`, `hardware_profile`
- `cleanup_on_exit`, `server_post_stop_cmd`

Historische Lifecycle-Flags wie `always_stop_before_start` sind für den konsolidierten Connector nicht mehr Teil der empfohlenen Konfiguration.

Seit v4.3.0 gilt zusätzlich: Der `UnifiedBenchmarkRunner` führt den lokalen Provider-Cleanup in `finally` aus. Bei aktivem `cleanup_on_exit` werden `server_stop_cmd` und optional `server_post_stop_cmd` deshalb auch bei `KeyboardInterrupt`/Abbruch ausgeführt.

### Hardware-Profile & `{hardware_context}` für Reviewer-Prompt (ab Session 56)

Jeder lokale Provider in `provider_config.yaml` hat ein `hardware_profile`-Feld. Dieser Key wird in `benchmark_config.yaml:runner_environment.profiles` aufgelöst und bestimmt, welche Hardware-Beschreibung der Meta-Reviewer im Prompt sieht.

**Pflicht:** Jeder `hardware_profile`-Key in `provider_config.yaml` MUSS in `benchmark_config.yaml` definiert sein. Fehlt der Key, fällt der Lookup auf `active_profile` (M4) zurück → der Reviewer zitiert die falsche Hardware.

| Provider | Key | Hardware | `ram_gb` | Template |
|---|---|---|---|---|
| `llamacpp` | `m4_macbook_pro_metal` | Apple Silicon M4, 24 GB | 24 | constrained (Swapping-Risiken) |
| `llamacpp_spark` | `dgx_spark_cuda` | NVIDIA DGX Spark, 115 GB | 115 | ample (kein Engpass) |
| `vllm_spark` | `asus_gx10_blackwell` | ASUS GX10 / DGX Spark, 115 GB | 115 | ample (kein Engpass) |

**Lookup-Kette in `generate_review.py`:**
1. `_get_hardware_profile_for_model()` — Provider-Config (SSoT)
2. `_get_hardware_profile_from_csv()` — Fallback: rohe CSV `hardware_profile`-Spalte (für auskommentierte Modelle)
3. `SystemContextManager.get_editor_prompt_injection()` — löst Key gegen `benchmark_config.yaml` auf

**Local-Template konditional:** Bei `ram_gb < 64` (memory-constrained) nennt das Template "Swapping-Risiken" als legitimen Diskurspunkt. Bei `ram_gb >= 64` (ample) formuliert es "Speicher ist hier kein Engpass" — keine Speicher-Spekulation. Die Sperrklausel im Prompt (`meta_reviewer_prompt.yaml:30`) verbietet dem Reviewer zusätzlich, Hardware-Annahmen zu erfinden, die nicht im `{hardware_context}`-Datenfeld stehen.

### Spark: Token-Management pro Modell (ab Session 26)

Der `llamacpp_spark`-Server ist ein eigenständiger Prozess mit eigenem Kontextfenster. Drei Ebenen steuern das Token-Verhalten:

1. **`context_length`** (Provider-Config, per-Modell) → `--ctx-size` beim Serverstart
   - Gesamtkontextfenster (Input + Output gemeinsam)
   - Bestimmt KV-Cache-Speicher pro Slot: `context_length × layer_count × head_dim × 2`
   - Beispiel: 32768 × 27B × Q8 = ~16 GB KV-Cache pro Slot
   - **Alle Spark-Modelle sollten explizit `context_length` setzen** — nicht auf den Provider-Default (65536) verlassen

2. **`max_tokens`** (Provider-Config, per-Modell) → HTTP `max_tokens` pro Anfrage
   - Begrenzt nur die Generierung, nicht den Input
   - **Kardinalregel:** `max_tokens < context_length`
   - Ohne Cap generiert das Modell bis zum Kontextfenster → HTTP-Read-Timeout-Loop
   - Per-Model-Cap wird in `llamacpp_base.py:query()` NACH `resolve_token_budget()` angewendet

3. **`parallel`** (Provider-Config, Provider-Level oder per-Modell) → `--parallel`
   - Anzahl gleichzeitiger Request-Slots (Continuous Batching)
   - Für sequentiellen Benchmark: `parallel=2` (Spare Slot für Health-Checks) statt `parallel=4`
   - Hybrid-Attention-Modelle (z.B. Hermes 4.3 36B): `parallel=1` (SWA-Re-Processings verursachen Connection-Resets bei mehreren Slots)

4. **`read_timeout`** (Provider-Config, Provider-Level) → httpx Read-Timeout
   - Default 300s — zu kurz für lokale 27B-Modelle bei 10-15 t/s
   - `llamacpp_spark`: 2400s (40 Min) — deckt 16K Tokens × 12 t/s + Sicherheitsmarge
   - Berechnung: `read_timeout ≥ max_tokens / min_tps × 1.5`

**Config-Beispiel (provider_config.yaml):**

```yaml
llamacpp_spark:
  read_timeout: 2400          # Provider-Level (httpx)
  parallel: 2                 # Provider-Default
  models:
  - id: my-thinking-model
    context_length: 32768     # Explizit (nicht 65536 Provider-Default)
    max_tokens: 16384         # Output-Cap (Hälfte von context_length)
    enable_thinking: true
  - id: my-hybrid-model
    context_length: 16384     # Kleiner wegen Hybrid-Attention
    parallel: 1               # Per-Modell-Override
```

### Spark: `reasoning_content`-Extraktion (ab Session 26)

llama.cpp-Modelle mit `--reasoning on` (bzw. `enable_thinking: true`) geben Thinking-Inhalte im API-Response-Feld `reasoning_content` zurück — **nicht** im Standard-`content`. Die Extraktion in `_extract_response_content()` (`llamacpp_base.py`):

1. `content = msg.content` — die sichtbare Antwort
2. `reasoning = msg.reasoning_content` — der Thinking-Block
3. `reasoning_tokens` — bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` (llama.cpp-native), Fallback auf `completion_tokens` nur wenn Content leer
4. `think_content` — der vollständige Thinking-Block (Key einheitlich mit `base_runner.py`)

**Historischer Bug (Session 26):** `_extract_response_content()` speicherte `"thinking_content"` statt `"think_content"` — `base_runner.py:163` las aber `"think_content"`. Ergebnis: `think_content` blieb immer leer in CSV. Zusätzlich: `reasoning_tokens` wurde nur bei leerem Content gesetzt — jetzt bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` gelesen.

### Provider-Connector Thinking/Reasoning-Extraktion (ab v4.10.1)

Alle Provider-Connectors in `utils/providers/` extrahieren seit v4.10.1 konsistent drei Felder in `last_response_metadata`:

| Feld | OpenAI | Anthropic | Google | Mistral | OpenRouter | Ollama | Groq | xAI | Cohere |
|------|--------|-----------|--------|---------|------------|--------|------|-----|--------|
| `reasoning_tokens` | `usage.completion_tokens_details.reasoning_tokens` | `usage.output_tokens_details.reasoning_tokens` | `usage_metadata.thoughts_token_count` | `usage.completion_tokens_details.reasoning_tokens` | `usage.completion_tokens_details.reasoning_tokens` | `eval_count` (wenn Thinking erkannt) | `usage.completion_tokens_details.reasoning_tokens` | `usage.completion_tokens_details.reasoning_tokens` | `usage.tokens.output_tokens` (v2 API) |
| `think_content` | `msg.reasoning` / `msg.reasoning_content` | `response.content[b].thinking` (type=thinking) | `candidates[0].content.parts[].thinking` | `chunk.thinking` (list-Response) | `msg.reasoning` / `msg.reasoning_content` / `msg.think_content` | `msg.thinking` (Streaming) | `msg.reasoning` / `msg.reasoning_content` | `msg.reasoning` / `msg.reasoning_content` | N/A (kein separates Thinking-Feld in v2 API) |
| `usage` | `response.usage` | `response.usage` | `usage_metadata` | `response.usage` | `response.usage` | Dict (synthetisiert) | `response.usage` | `response.usage` | `response.usage` (Cohere v2) |

**Streaming-Pfade (ab v4.10.1):**

| Provider | Reasoning-Streaming | Usage-Streaming |
|----------|---------------------|-----------------|
| OpenAI | `delta.reasoning` akkumuliert | `chunk.usage` (mit `stream_options={"include_usage": True}`) |
| Anthropic | `content_block_delta.delta.thinking` (type=thinking_delta) | `message_delta.usage` |
| Google | `candidates[0].content.parts[].thinking` (pro Chunk) | `chunk.usage_metadata` (kumulativ — letzter Chunk gewinnt) |
| OpenRouter | `delta.reasoning` akkumuliert | `chunk.usage` (letzter Chunk) |
| Groq | `delta.reasoning` akkumuliert | `chunk.usage` (falls verfügbar) |
| xAI | `delta.reasoning` akkumuliert | `chunk.usage` (falls verfügbar) |
| Ollama | `msg.thinking` akkumuliert | Final-Chunk (`chunk.get("done") == True`) |
| Mistral | Kein Streaming (Blocking-Only) | Blocking-Only |
| Cohere | Kein Streaming (Blocking-Only) | Blocking-Only (v2 API: `response.usage`) |

**DRY-Helper `_extract_reasoning_tokens(usage)`:**

Definiert in `anthropic.py`, `openai.py`, `groq.py`, `xai.py`:

```python
def _extract_reasoning_tokens(self, usage) -> int | None:
    """Extrahiere reasoning_tokens aus usage-Objekt (OpenAI-kompatibel)."""
    if not usage:
        return None
    details = getattr(usage, "completion_tokens_details", None)
    if details:
        return getattr(details, "reasoning_tokens", None)
    return None
```

**Pitfall: ohne `usage`-Objekt fällt `llm_client.py` auf `estimate_tokens()` zurück** (`llm_client.py:248`):

```python
# llm_client.py:238
usage = self.last_response_metadata.get("usage")
input_tokens, output_tokens = LLMParser.extract_usage_tokens(usage)

# Fallback to estimation for Local/Ollama or if Usage missing
if input_tokens == 0 and output_tokens == 0:
    input_tokens = self.estimate_tokens(prompt)
    output_tokens = self.estimate_tokens(response_text)
```

Ohne `usage` in `last_response_metadata` werden Tokens geschätzt (1 Token ≈ 4 Zeichen) statt von der API gezählt. **Bei allen Provider-Fixes muss `usage` mitgespeichert werden**, damit `LLMParser.extract_usage_tokens()` echte Werte liefert.

**Pitfall: Anthropic hat keinen einheitlichen Usage-Schema.** OpenAI-kompatible Provider (`usage.completion_tokens_details.reasoning_tokens`) und Google (`thoughts_token_count`) liefern Reasoning-Tokens direkt im Usage-Objekt. Anthropic hat das in `usage.output_tokens_details.reasoning_tokens` (neue SDK-Versionen). Beide Schemata müssen parallel geprüft werden.

### Cohere Native ToolUse (ab v4.10.8)

Cohere's Reasoning-Modelle (`command-a-plus`, `command-a-reasoning`) kollidieren mit prompt-basierten JSON-Tool-Schemas: das `thinking`-Feld erwartet `{"type": "enabled"|"disabled"}`, was bei prompt-injizierten Schemas fehlt → HTTP 422. Zusätzlich liefern komplexe System-Prompts (Benchmark-Szenarien) bei `command-a-plus` persistente HTTP 500 mit nativen Tools (MoE-Instabilität).

**Architektur-Lösung:**

```
ToolUse-Modul → system_prompt (mit JSON-Tool-Schema)
                    │
                    ▼
cohere.py: _extract_tool_schema(system_prompt)
    → extrahiert Tool-Schema via Bracket-Counting
    → _schema_to_cohere_tools(schema)
    → Cohere-native `tools`-Parameter
    → thinking: {"type": "disabled"} (Reasoning-Modelle)
                    │
                    ▼
Cohere API v2: POST /v2/chat (mit `tools`-Parameter)
                    │
                    ▼
cohere.py: _format_tool_calls_as_text(response)
    → {"tool_call": {"name": ..., "parameters": ...}}
    → kompatibel mit ToolUse-Modul-Parser
```

**Module-Key-Dispatch:** `_module_key == "tooluse"` triggert den nativen Pfad. Alle anderen Module bleiben prompt-basiert (unverändert).

**Reasoning-Modell-Erkennung:** `_is_cohere_reasoning_model(model)` prüft auf Substring-Match (`command-a-reasoning`, `command-a-plus`).

**Pitfall:** NIEMALS prompt-basierte Tool-Schemas für Cohere-Reasoning-Modelle verwenden — immer den nativen Pfad. `command-a-plus` hat persistente 500er bei Benchmark-Prompts (MoE-Instabilität, serverseitiger Bug) — `supports_tool_use=false`.

### Config-Lookup mit ID-Normalisierung (Defense-in-Depth)

Die Model-IDs in `config/provider_config.yaml` werden in der Regel in der rohen Schreibweise des Providers eingetragen (z. B. `qwen3.5-35b-a3b-q8` mit Punkten). `resolve_canonical_model_id()` in `utils/model_utils.py` normalisiert diese ID früh im Entry-Point (Punkte/Bindestriche → Underscores), sodass `qwen3_5-35b-a3b-q8` durch die gesamte Benchmark-Pipeline gereicht wird — identisch zur Schreibweise in CSV-Spalten, Card-Dateinamen und Leaderboard-Zeilen.

Damit der Config-Lookup in `_model_cfg()` (`utils/providers/llamacpp_base.py`) diese ID-Variante trotzdem findet, ist der Lookup **defense-in-depth** aufgebaut:

1. **Schneller Pfad:** exakter String-Match zwischen übergebener `model_id` und `entry.id`.
2. **Fallback:** normalisierter Vergleich beider Seiten via `_normalize_model_name()` (Punkt **und** Bindestrich → Underscore).

Ohne diesen Fallback wirft `_resolve_model_path()` einen `ValueError: no model_file configured for model 'qwen3_5-35b-a3b-q8'`, weil die Config den Eintrag unter `qwen3.5-35b-a3b-q8` führt. Betroffen sind alle Modelle mit Versions-/Größenangaben in der ID (`qwen3.5`, `qwen3.6`, `qwen2.5-coder-7b`, `llama-3.3-70b`, `gemma-3-12b` etc.).

Regressionstests: `tests/test_llamacpp_provider_separation.py::test_model_cfg_finds_dotted_id_via_canonical_form` und `::test_model_cfg_returns_empty_for_unknown_id`.

### Sampling-Defaults via `llama_cpp_defaults` (SSoT)

Alle llama.cpp-Server-Start-Flags für Sampling-Parameter werden aus dem Block `providers.local.config.llama_cpp_defaults` in `config/provider_config.yaml` gelesen. Diese Werte entsprechen den **llama.cpp-Upstream-Defaults** — mit Ausnahme von `seed=42` für reproduzierbare Benchmarks.

| Flag | Default | Quelle | Verhalten |
|---|---|---|---|
| `--temp` | `0.8` | llama.cpp-Default | Lässt Modelle frei atmen |
| `--top-p` | `0.95` | llama.cpp-Default | Leichte Nucleus-Filterung |
| `--top-k` | `40` | llama.cpp-Default | Filtert nur echten Müll |
| `--min-p` | `0.0` | llama.cpp-Default | Deaktiviert |
| `--presence-penalty` | `0.0` | llama.cpp-Default | Deaktiviert |
| `--repeat-penalty` | `1.0` | llama.cpp-Default | Kein Penalty gegen Loops |
| `--seed` | `42` | **explizit gesetzt** | Reproduzierbarkeit (Upstream wäre `-1`) |

**Pro-Modell-Override:** In `provider_config.yaml > providers.local.*.models` kann jedes Modell eigene Werte setzen:

```yaml
- id: hermes-4-14b-q4
  temperature: 0.3        # überschreibt Default 0.8
  top_p: 0.9              # überschreibt Default 0.95
  repeat_penalty: 1.05
```

Der Code in `_build_server_cmd()` (`utils/providers/llamacpp_base.py`) prüft für jeden Parameter: wenn `model_cfg.<param>` gesetzt ist, gewinnt der Modell-Wert; sonst greift der `llama_cpp_defaults`-Wert; sonst der hardcoded Code-Fallback. Die Override-Reihenfolge ist:

1. **Modell-Level** (`model_cfg.<param>`) — höchste Priorität
2. **Provider-Level Defaults** (`llama_cpp_defaults.<param>`) — SSoT
3. **Code-Hardcoded Fallback** — letzte Verteidigungslinie

**Beide Provider teilen sich die Defaults:** `llamacpp` (M4) und `llamacpp_spark` (DGX) lesen denselben `llama_cpp_defaults`-Block. Damit sind Sampling-Bedingungen identisch, nur die Hardware-spezifischen Settings (Context-Window, GPU-Layers, SSH-Start) unterscheiden sich.

**Historischer Rename (2026-06-08):** Der Block hieß zuvor `benchmark_defaults` und war auf `temperature: 0.1` / `top_p: 0.9` / `repeat_penalty: 1.1` (sehr deterministisch) gesetzt. Mit dem Rename auf `llama_cpp_defaults` wurde die Semantik klar (Upstream-Defaults als Fallback) und die Pro-Modell-Override-Mechanik in den Vordergrund gerückt. Alte Repo-Konfig-Files, die noch `benchmark_defaults` nutzen, führen beim Server-Start zu einem Fehler — der Block muss umbenannt werden.

Regressionstests: `tests/test_llamacpp_provider_separation.py::test_build_server_cmd_uses_llama_cpp_defaults`, `::test_build_server_cmd_model_override_wins`, `::test_build_server_cmd_works_without_defaults_block`.

### vLLM Dual-Thinking-Profile: Config-Driven-Expansion (ab Session 52)

vLLM-Modelle mit `enable_thinking: true` werden beim Config-Load automatisch in **zwei Benchmark-Profile** expandiert — ein Container bedient beide Profile per-Request, ohne Server-Neustart beim Profil-Wechsel.

**Warum nur vLLM?** vLLM's `enable_thinking` ist ein Chat-Template-Kwarg, der per-Request via `chat_template_kwargs` gesteuert wird. llama.cpp's `enable_thinking` ist ein Server-Start-Flag (`--reasoning on`/`off`) — kann nicht per-Request gewechselt werden. Die Expansion läuft daher NUR für Provider mit `api_type == "vllm"`.

**Mechanik:**

1. **Config-Expansion** (`utils/config_validator.py:_expand_thinking_profiles()`): Aufgerufen in `_load_config` nach Merge, vor `_check_duplicate_model_ids`. Für jeden vLLM-Modell-Eintrag mit `enable_thinking: true`:
   - **Original-Eintrag** (Standard-Profil): konsumiert `enable_thinking`, setzt `chat_template_kwargs: {"enable_thinking": false}`.
   - **Generierter Thinking-Eintrag**: `id: {original_id}-thinking`, `config:` identisch (→ kein Container-Swap), `card_model_id: {original_id}` (→ teilt Card), `chat_template_kwargs: {"enable_thinking": true}`, `max_tokens: {thinking_max_tokens}`.

2. **Swap-Entkopplung** (`utils/providers/vllm_base.py`): Neue Instance-Variable `_active_config` trackt die TOML-Config des aktiven Modells. `_ensure_model_ready` vergleicht `config:` statt `model_id`:
   - Gleiche `config:` (z.B. Standard → Thinking desselben Modells) → **kein `swap_model`**, nur per-Request-Param-Wechsel.
   - Unterschiedliche `config:` → `swap_model` wie bisher (echter Modell-Wechsel).
   - Backward-compat: `_active_config is None` → bisheriges Verhalten.

3. **Card-Lookup via `card_model_id`** (`utils/model_utils.py`): `_find_card()` und `resolve_canonical_model_id()` akzeptieren optional `model_cfg`. Wenn `card_model_id` vorhanden → Card-Lookup über dieses Feld. `resolve_canonical_model_id` gibt die **Profile-eigene ID** zurück (`{id}-thinking`), NICHT die Card's `model_id` — CSV `model_id` bleibt eindeutig. `enforce_card_first()` threaded `model_cfg` durch → keine Platzhalter-Cards für Thinking-Profile.

**Config-Beispiel (`provider_config.yaml`):**

```yaml
vllm_spark:
  thinking_max_tokens: 32768   # Provider-Default für Thinking-Profile
  models:
  - id: ornith-1.0-35B-FP8
    config: Ornith1-35B-FP8
    enable_thinking: true      # ← Trigger für Expansion
    max_tokens: 8192           # Standard-Profil Output-Cap
    temperature: 0.7
    top_p: 0.8
    top_k: 20
```

**Resultierende expandierte Config (transparent für alle Downstream-Konsumenten):**

```yaml
# Standard-Profil (generiert):
- id: ornith-1.0-35B-FP8
  config: Ornith1-35B-FP8
  chat_template_kwargs: {"enable_thinking": false}
  max_tokens: 8192
  temperature: 0.7
  top_p: 0.8
  top_k: 20

# Thinking-Profil (generiert):
- id: ornith-1.0-35B-FP8-thinking
  config: Ornith1-35B-FP8           # ← identisch → kein Swap
  card_model_id: ornith-1.0-35B-FP8  # ← teilt Card
  chat_template_kwargs: {"enable_thinking": true}
  max_tokens: 32768                  # ← thinking_max_tokens
  temperature: 0.7
  top_p: 0.8
  top_k: 20
```

**`thinking_max_tokens`-Quelle (Priorität):**
1. `model_cfg.thinking_max_tokens` (pro Modell überschreibbar)
2. `provider.thinking_max_tokens` (Provider-Default)
3. Fehler (kein Hardcoding)

**Leaderboard-Auswirkung:** Zwei separate CSV-Einträge (`ornith-1_0-35B-FP8` und `ornith-1_0-35B-FP8-thinking`), zwei Leaderboard-Einträge, eine geteilte Model-Card.

**Pitfall: `resolve_provider` muss expandierte Config sehen.** `resolve_provider()` nutzt `ConfigValidator().config` als primäre Quelle (merge + expansion aware), nicht die Roh-YAML. Andernfalls sind generierte `{id}-thinking`-Profile unsichtbar → fälschlicher Fallback auf Ollama.

Regressionstests: `tests/test_config_thinking_expansion.py` (18 Tests), `tests/test_card_model_id_lookup.py` (7 Tests), `tests/test_vllm_spark_provider.py` (+5 Swap-Entkopplungs-Tests).

### Dual-Thinking-Profile: Leaderboard-Darstellung (ab Session 54)

Thinking-Profile erscheinen im Leaderboard unter dem **originalen Display-Namen** des Modells (nicht mit "Thinking"-Suffix). Die Unterscheidung erfolgt über zwei Mechanismen:

| Mechanismus | Standard-Profil | Thinking-Profil |
|---|---|---|
| `model_id` (CSV/Leaderboard) | `ornith-1_0-35B-FP8` | `ornith-1_0-35B-FP8-thinking` |
| `display_name` (Leaderboard) | `Ornith 1.0 35B (FP8)` | `Ornith 1.0 35B (FP8)` (derselbe!) |
| `thinking_mode` (CSV/Leaderboard-Spalte) | `Standard` | `Thinking` |
| Karte | `ornith-1_0-35B-FP8--VSPK.json` | `ornith-1_0-35B-FP8--VSPK.json` (geteilt) |

**`thinking_mode`-Spalte (`utils/base_runner.py:_resolve_thinking_mode`):**

| Config | `thinking_mode` |
|---|---|
| `card_model_id` vorhanden (vLLM Dual-Profile Thinking) | `Thinking` |
| `chat_template_kwargs.enable_thinking: false` (vLLM Dual-Profile Standard) | `Standard` |
| `chat_template_kwargs.enable_thinking: true` | `Thinking` |
| `enable_thinking: true` (llama.cpp) | `Thinking` |
| `enable_thinking: false` (llama.cpp) | `Standard` |
| Keine Thinking-Config (Cloud/Commercial) | `n/a` |

**Trennung Runtime-Config vs. Capability:**
- `thinking_mode` = was war für diesen Lauf konfiguriert (pro-Run, CSV-Spalte).
- `thinking_probe_detected` = kann das Modell Thinking (Card-Feld, stabil).

Beide Felder sind unabhängig — ein Modell mit `thinking_mode=Standard` kann `thinking_probe_detected=true` haben (Capability ja, aber nicht aktiviert).

**Display-Name-Sharing (`scripts/leaderboard/module_integration.py:_add_thinking_profile_names`):**

Die Funktion ergänzt `display_lookup` für Thinking-Profile aus der expandierten Config:
```python
for model_cfg in providers["local"][provider_key]["models"]:
    if "card_model_id" in model_cfg:
        profile_id = _safe_name(model_cfg["id"])
        card_ref = _safe_name(model_cfg["card_model_id"])
        display_lookup[profile_id] = display_lookup[card_ref]
```

### Dual-Thinking-Profile: Card-Lookup-Fallback (ab Session 54)

Der `card_model_id`-Redirect in `_find_card()` und `resolve_canonical_model_id()` greift nur, wenn `model_cfg` übergeben wird. Viele Caller (`generate_review.py`, `review/risk_calculator.py`, `review/metrics.py`, `sync_cards.py`) rufen `_find_card()` ohne `model_cfg` auf — dort greift der Redirect nicht.

**Lösung — deterministischer `-thinking`-Suffix-Fallback in `_find_card()`:**

```python
# Last-Resort-Fallback in _find_card():
if model_cfg is None and lookup_id.endswith("-thinking"):
    base_id = lookup_id[: -len("-thinking")]
    base_path = _find_card(base_id, card_dir=card_dir)
    if base_path.exists():
        return base_path
```

Greift nur wenn `model_cfg is None` UND keine Card für `{id}-thinking` gefunden wurde (nach allen anderen Fallbacks). Deterministisch (kein Heuristik-Raten), generisch für alle vLLM-Modelle mit `enable_thinking: true`.

**Kritische Trennung — `resolve_canonical_model_id` schützt Thinking-Profil-Identität:**

Wenn `_find_card` via Suffix-Fallback die Basis-Card findet, DARF `resolve_canonical_model_id` NICHT `card.model_id` zurückgeben — sonst würden Basis- und Thinking-Profil im Leaderboard zu einer ID verschmelzen (CSV-Zeile wird überschrieben).

```python
_is_thinking_suffix = (
    model_cfg is None
    and base.endswith("-thinking")
)
if _used_card_redirect or _is_thinking_suffix:
    return _safe_name(base)  # Profil-eigene ID, NICHT card.model_id
```

**Zusammenfassung:**

| Funktion | Suffix-Strip erlaubt? | Begründung |
|---|---|---|
| `_find_card` | ✅ Ja (Last-Resort) | Findet Card-Datei; Suffix-Strip ist deterministisch |
| `resolve_canonical_model_id` | ❌ Nein | Muss CSV-Identität erhalten; gibt `_safe_name(base)` bei Thinking-Suffix zurück |

Regressionstests: `tests/test_card_model_id_lookup.py` (+1 Test: `test_resolve_canonical_thinking_without_cfg_preserves_thinking_id`).

### Dual-Thinking-Profile: `thinking_mode`-Sichtbarkeit (ab Session 55)

`thinking_mode` ist auf drei Ebenen sichtbar — eine Datenquelle (`_resolve_thinking_mode()` aus model_cfg), drei Ausgabeorte:

| Ebene | Wo | Sichtbar für | Code |
|---|---|---|---|
| **CSV-Spalte** | `thinking_mode` pro Task-Zeile | Datenanalyse, Leaderboard | `utils/base_runner.py:build_base_result()` |
| **Audit-Log-Header** | `**Thinking Mode:** Thinking/Standard` nach `**Provider:**` | Mensch (Datei direkt) | `utils/benchmark_utils.py:save_audit_log()` |
| **Leaderboard-Spalte** | `"Thinking Mode"` zwischen `Speed Profile` und `Total Score` | Leaderboard-Leser | `scripts/leaderboard/exporter.py` |
| **Review-Prompt-Variable** | `{model_thinking_mode}` als hartes Datenfeld | LLM-Reviewer | `scripts/analysis/generate_review.py:_resolve_thinking_mode_for_review()` |

**Warum drei Ebenen?** Verschiedene Konsumenten brauchen unterschiedliche Sichtbarkeit:
- **Mensch:** Audit-Log-File direkt lesen → Header-Zeile.
- **Datenanalyse:** CSV-Aggregation → Spalte.
- **Leaderboard:** Vergleichende Tabelle → Spalte.
- **LLM-Reviewer:** Prompt-Inhalt → Variable (sonst rät er aus Architektur-Tags, siehe Session-55-Befund).

**Review-Prompt-Pitfall (Session 55):** Externe Audit-Analyse zeigte, dass Reviewer beide Ornith-Läufe fälschlich als "Thinking-Lauf" deklarierten, obwohl Stabilitätsdaten (Timeout-Rate, P95) zeigten, dass einer Standard war. Wurzel: `{model_tags}` enthält "Thinking" als Architektur-Tag (Capability, immer vorhanden), aber kein Runtime-Modus-Datenfeld. Reviewer riet aus Tags statt aus Daten.

**Pflicht:** Jede Runtime-Config, die den Reviewer beeinflusst (thinking_mode, temperature, max_tokens), MUSS als hartes Datenfeld im Prompt stehen — nicht aus Modellnamen oder Architektur-Tags ableiten lassen.

**Backfill alter Audit-Logs:** Für Ornith wurden 149 Audit-Log-Dateien patchiert (49 Thinking, 50 vLLM-Standard, 50 llama.cpp-Standard). Idempotent — Script prüft `if "**Thinking Mode:**" in content: skip`.

---

## Reasoning-Modelle: Reasoning-Erkennung & Card-First Workflow

CrucibleMark erkennt ab v3.5.8 Reasoning-Modelle empirisch statt rein heuristisch. Diese Erkennung bestimmt das Token-Budget, die LLM-Judge-Bewertung und die Audit-Log-Ausgabe.

### Wann wird der Probe ausgelöst?

`_ensure_model_card()` in `scripts/core/unified_runner.py` wird **vor dem ersten Run** eines Modells aufgerufen:

```
┌────────────────────────────────────────────────────────┐
│ Card vorhanden + thinking_probe_detected feld          │
│ → Skip (kein API-Call)                                 │
├────────────────────────────────────────────────────────┤
│ Card vorhanden, aber Feld fehlt                        │
│ → Probe → Feld in bestehende Card schreiben            │
├────────────────────────────────────────────────────────┤
│ Keine Card                                             │
│ → Probe → Minimal-Card erstellen (card_status: minimal)│
├────────────────────────────────────────────────────────┤
│ Probe-Fehler (429 / 403 / sonstiger API-Fehler)        │
│ → ⚠️ Clean Warning, Modell in _probed_models (kein    │
│   Retry), Benchmark läuft weiter                       │
└────────────────────────────────────────────────────────┘
```

### Signale der Reasoning-Erkennung (ThinkingProbe)

`probe_thinking_model(model_id, provider_key, config)` in `utils/model_utils.py` schickt einen deterministischen Reasoning-Prompt (Zugproblem) und wertet aus:

| Signal | Kriterium | Konfidenz |
|--------|-----------|-----------|
| A | `<think>` / `<thinking>` / `<thought>`-Tags im Response | `high` |
| B | `reasoning_tokens > 0` in API-Metadaten | `medium` |

> **Signal C (Response-Länge) existiert nicht** — Instruction-Following-Modelle produzieren auf Reasoning-Prompts ebenfalls lange Antworten. Response-Länge darf nicht als CoT-Indikator verwendet werden.

Das Ergebnis landet als JSON in `benchmark_scores/model_cards/<model_id>.json`:

```json
{
  "thinking_probe_detected": true,
  "thinking_probe_evidence": "Signal A: <think> tags detected in response body",
  "thinking_probe_confidence": "high",
  "thinking_probe_manual_override": false
}
```

### `is_reasoning_model()` Lookup-Hierarchie

Die Funktion in `utils/model_utils.py` verwendet immer zuerst die Card:

```
1. is_reasoning_model_from_card(model_id)
   ├── Card + Feld vorhanden → Feldwert zurückgeben
   └── Fehlt Card oder Feld → None (kein False-Positive)

2. String-Trigger-Heuristik (Fallback)
   └── deepseek-r1, reasoning, phi4, qwq, o1, o3,
       magistral, glm-5, minimax-m2, gemini-2.5, kimi-k2
```

### Retroaktiver Probe (CLI)

Für bereits laufende Benchmark-Setups ohne Card-Felder:

```bash
# Einzelnes Modell
make probe-thinking MODEL=gemini-2.5-flash

# Alle Cards ohne thinking_probe_detected-Feld
make probe-all-thinking

# Direkter CLI-Aufruf mit Provider-Override
.venv/bin/python scripts/tools/probe_thinking.py --model <model-id> --provider openrouter
```

`scripts/tools/probe_thinking.py` unterstützt zusätzlich `--missing` (Batch: nur Cards ohne Feld) und `--all` (Force-Rescan aller Cards).

### Sonderfall: Modelle mit manuellem Override

Zwei Modellklassen können via Standard-Probe nicht korrekt erkannt werden:

#### OpenAI o-Series

o1, o3-mini, o4-mini verbergen Reasoning-Tokens intern. Die API liefert keine `<think>`-Tags und keine `reasoning_tokens`. Der Probe gibt `detected=False` zurück — fälschlicherweise.

#### llama.cpp-Modelle mit nativem Thinking (z. B. Gemma-4 E4B)

Manche llama.cpp-Modelle geben Reasoning-Inhalte im API-Response-Feld `reasoning_content` zurück — **nicht** im Standard-`content`-Feld. Das `content`-Feld ist bei diesen Modellen oft leer wenn das Thinking-Budget erschöpft ist. Der Standard-Probe schlägt fehl (kein `<think>`-Tag, `reasoning_tokens` fehlt in Standard-Metadaten). `llamacpp.py` extrahiert `reasoning_content` explizit und setzt `reasoning_tokens = completion_tokens` im Metadaten-Dict.

Für beide Klassen wird die Card **manuell** gesetzt:

```json
{
  "thinking_probe_detected": true,
  "thinking_probe_manual_override": true
}
```

> **Neue Modelle ergänzen:** Wenn ein Anbieter oder lokaler Provider Reasoning intern verbirgt oder in einem provider-spezifischen Feld übergibt, immer beide Felder manuell eintragen und `make probe-thinking MODEL=<id>` nicht als Quelle verwenden.

---

## Modell-IDs, Card-Benennung & Versionierung

Dieser Abschnitt beschreibt das vollständige System: von der Konfiguration einer Modell-ID bis zur gespeicherten Model Card und dem Leaderboard-Eintrag.

---

### Konzept: Was ist eine Modell-ID?

Die **Modell-ID** ist die kanonische Kennung eines Modells — die genaue Zeichenfolge, die in der API-Anfrage verwendet wird. Sie ist die einzige Quelle der Wahrheit für:

- den **Dateinamen der Model Card** (`benchmark_scores/model_cards/`) — bei `-latest`-Aliases mit bekannter Version weicht der Dateiname vom Alias ab (z. B. `mistral-large-latest` → `mistral-large-3.json`); `model_id` *in der Card* bleibt immer der API-Alias
- die **CSV-Spalte `model`** in allen drei Benchmark-CSVs
- den **Lookup** von Versionsinformationen und Reasoning-Flags

**SSoT:** `config/provider_config.yaml` → `providers.<section>.<provider>.models[].id`

> **Duplikat-Schutz:** `ConfigValidator` iteriert beim Start über alle explizit gelisteten Modell-IDs in `config/provider_config.yaml`. Taucht eine ID in mehr als einem Provider auf, wird `WARNING: Duplikat-Modell-ID '<id>': bereits registriert unter '<section>/<provider>', Eintrag unter '<section>/<provider>' wird ignoriert.` geloggt. Der erste Eintrag gewinnt (First-Win). `auto_discover`-Provider (Ollama) werden vom Check ausgenommen, da deren IDs erst zur Laufzeit bekannt sind.

#### Pinned IDs vs. Floating Aliases

| Typ | Beispiel | Risiko |
|---|---|---|
| **Pinned (Checkpoint-Slug)** | `moonshotai/kimi-k2-0711` | Kein Risiko — Modell ändert sich nie |
| **Floating Alias** | `mistral-large-latest` | Provider kann Silent Update durchführen — Card wird unter versionsspezifischem Namen gespeichert |

**Regel:** Wo ein Provider versionierte Slugs anbietet (typisch für OpenRouter: `model-YYYYMMDD`), **müssen** diese verwendet werden. Für Provider, die keine Versionskennung mitliefern (Anthropic, OpenAI, Google, Mistral Direct-API, Groq), ist die Floating-Alias-ID der korrekte Eintrag in Config und CSV — die Card hingegen wird unter `{base}-{version}.json` gespeichert, sobald die Version bekannt ist. Ist die Version (noch) nicht bekannt, bleibt der Alias als Dateiname (`codestral-latest.json`). Solange der Alias nicht von anderen Providern genutzt wird, entsteht keine Kollision.

---

### Vom Config-Eintrag zur Card-Datei: Vier Naming-Regeln

Die Funktion `_card_path(model_id, provider, *, for_write, resolved_version)` in `utils/model_utils.py` ist die einzige Stelle, die den Dateinamen einer Model Card berechnet. Sie implementiert vier Regeln — Regel 4 hat die höchste Priorität und wird vor allen anderen geprüft:

#### Regel 4 (höchste Priorität): `-latest`-Aliases → versionsspezifischer Dateiname

**Problem:** Floating Aliases wie `mistral-large-latest` sind *volatile* — derselbe Alias zeigt nach einem Provider-Update auf eine neue Modellversion. Eine Card unter dem Alias-Namen würde veraltete Metadaten für das neue Modell liefern (falsche Reasoning-Flags, falsche Kategorisierung).

**Lösung:** Ist die konkrete Modellversion bekannt (`resolved_version` ≠ stale), setzt sich der Dateiname aus Basis-Name + Version zusammen:

```
mistral-large-latest  + version="3"    →   mistral-large-3.json
mistral-medium-latest + version="2312" →   mistral-medium-2312.json
mistral-small-latest  + version="3"    →   mistral-small-3.json
codestral-latest      + version=stale  →   codestral-latest.json   (Fallback auf Regel 2)
```

**Stale-Versionen** (deaktivieren Regel 4): `"latest"`, `"unknown"`, `"k.A."`, `""`.

**Wichtig:** Die `model_id` *in der Card* bleibt immer der API-Alias — sie wird für API-Calls und CSV-Lookups verwendet. Nur der Dateiname ist versionsspezifisch.

Angewendet auf: alle Modell-IDs die auf `-latest` oder `:latest` enden, wenn `get_model_version()` einen nicht-stalen Wert liefert.

---

#### Regel 1: Namespaced IDs (enthalten `/`)

Der Provider-Namespace ist bereits in der ID eingebettet. Kein Prefix nötig.

```
moonshotai/kimi-k2-0711   →   moonshotai_kimi-k2-0711.json
z-ai/glm-5.1-20260406     →   z-ai_glm-5_1-20260406.json
qwen/qwen3-32b            →   qwen_qwen3-32b.json
meta-llama/llama-4-scout-17b-16e-instruct  →  meta-llama_llama-4-scout-17b-16e-instruct.json
```

Angewendet auf: OpenRouter-Modelle, namespaced Groq-Modelle, alle Modelle mit `/` in der ID.

#### Regel 2: Direkte API-Provider (`API`-Shortcode)

Proprietäre Modellnamen sind global eindeutig. Kein Prefix nötig.

```
claude-sonnet-4-6          →   claude-sonnet-4-6.json
gpt-5                      →   gpt-5.json
gemini-2.5-pro             →   gemini-2_5-pro.json
codestral-latest           →   codestral-latest.json   (version unbekannt → Alias bleibt)
grok-3-mini                →   grok-3-mini.json
```

Angewendet auf: `anthropic`, `openai`, `google`, `xai`, `mistral` (alle mit Shortcode `API`) — sofern nicht Regel 4 greift (bekannte Version bei `-latest`-Alias).

#### Regel 3: Nicht-namespaced + nicht-API → Provider-Prefix

**Problem:** Die gleiche bare ID (`llama3.3:70b`) kann sowohl via Ollama als auch via Groq laufen. Ohne Prefix würden sich beide Cards gegenseitig überschreiben — ein **Ghost-Benchmark**: Die Card des einen Providers wird fälschlich für den anderen verwendet, Reasoning-Flags und size_class sind falsch.

**Lösung:** Prefix mit Provider-Shortcode.

```
# via ollama_local (Shortcode: LCL)
llama3.3:70b         →   LCL_llama3_3_70b.json

# via groq (Shortcode: GR), nicht-namespaced
llama-3.3-70b-versatile  →   GR_llama-3_3-70b-versatile.json
```

**Backward-Compat:** Bestehende Cards ohne Prefix (vor dieser Konvention angelegt) werden beim Read-Lookup als Fallback gefunden — `_card_path(for_write=False)` versucht zuerst `LCL_*`, fällt dann auf die unpräfixierte Datei zurück. Beim Schreiben (`for_write=True`) wird immer der präfixierte Pfad verwendet.

#### Entscheidungsbaum

```
model_id  +  resolved_version
   │
   ├── -latest/‌:latest Alias + resolved_version ≠ stale?
   │        └── JA ──► {safe_name(base)}-{version}.json              (Regel 4)
   │
   ├── enthält "/"?  ─── JA ──► safe_name(model_id).json             (Regel 1)
   │
   └── NEIN
         │
         ├── Provider-Shortcode == "API"?  ─── JA ──► safe_name(model_id).json  (Regel 2)
         │
         └── NEIN (LCL, GR)
               │
               └── for_write=True  ──► {SHORTCODE}_safe_name.json    (Regel 3)
               └── for_write=False ──► Prefixed? → Prefixed-Pfad
                                       Sonst     → Unprefixed (Legacy-Fallback)
```

---

### Helper-Funktionen als SSoT (`utils/model_utils.py`)

Alle Card-Pfadoperationen **müssen** diese Funktionen verwenden. Inline `Path(...) / f"{re.sub(...)}.json"` ist verboten — es würde die Vier-Regeln-Logik umgehen.

```python
from utils.model_utils import (
    CARD_DIR,
    WEIGHTS_TIER_DISPLAY,
    _card_path,
    _find_card,
    _safe_name,
    enforce_card_first,
    normalize_model_id,
    resolve_canonical_model_id,
    strip_date_suffix,
)
```

#### `_safe_name(model_id: str) → str`

Kanonische Dateiname-Transformation. Ersetzt alle Zeichen aus `[:/.\ ]` durch `_`.

```python
_safe_name("gemini-2.5-flash")                 # → "gemini-2_5-flash"
_safe_name("deepseek-r1:8b")                   # → "deepseek-r1_8b"
_safe_name("moonshotai/kimi-k2-0711")          # → "moonshotai_kimi-k2-0711"
_safe_name("z-ai/glm-5.1-20260406")            # → "z-ai_glm-5_1-20260406"

# FALSCH — führt zu Lookup-Miss ohne Fehlermeldung:
"gemini-2.5-flash".replace("/", "_")  # → "gemini-2.5-flash" (Punkt bleibt!)
```

#### `_card_path(model_id, provider=None, *, for_write=False, resolved_version=None) → Path`

Berechnet den vollständigen Pfad der Card-Datei nach den Vier Regeln.

```python
# Regel 4: -latest Alias mit bekannter Version → versionsspezifischer Dateiname
_card_path("mistral-large-latest", "mistral", for_write=True, resolved_version="3")
# → benchmark_scores/model_cards/mistral-large-3.json

# Regel 4: version ist stale → Fallback auf Regel 2 (Alias bleibt)
_card_path("codestral-latest", "mistral", for_write=True, resolved_version="latest")
# → benchmark_scores/model_cards/codestral-latest.json

# Regel 1: Namespaced
_card_path("moonshotai/kimi-k2-0711")
# → benchmark_scores/model_cards/moonshotai_kimi-k2-0711.json

# Regel 2: API-Provider
_card_path("claude-sonnet-4-6", "anthropic")
# → benchmark_scores/model_cards/claude-sonnet-4-6.json

# Regel 3: LCL — Read (Fallback auf Legacy)
_card_path("llama3.3:70b", "ollama_local")
# → benchmark_scores/model_cards/llama3_3_70b.json  (falls kein LCL_* existiert)

# Regel 3: LCL — Write (immer Prefix)
_card_path("llama3.3:70b", "ollama_local", for_write=True)
# → benchmark_scores/model_cards/LCL_llama3_3_70b.json
```

> **Wann `for_write=True`?** Nur beim Anlegen oder Überschreiben einer Card — also im Template-Generator `generate_model_cards.py`. Alle Lookup-Funktionen verwenden `for_write=False` (Default).

#### `_find_card(model_id: str) → Path`

Findet eine bestehende Card ohne Kenntnis des Providers. Nützlich in Utility-Funktionen, die nur die model_id kennen.

```python
# Nicht-namespaced (LCL/GR): LCL_deepseek-r1_8b.json → dann deepseek-r1_8b.json (Legacy)
path = _find_card("deepseek-r1:8b")
if path.exists():
    card = json.loads(path.read_text())

# -latest Alias: Fallback 3 — findet versionsspezifische Card via get_model_version()
path = _find_card("mistral-large-latest")
# → mistral-large-3.json  (wenn get_model_version("mistral-large-latest") == "3")
```

Lookup-Reihenfolge (vier Schritte):
1. **Namespaced IDs** (`/` im model_id) → direkt `safe_name.json`
2. **Prefixed Kandidaten** (`LCL_*`, `GR_*`) — erster existierender Treffer
3. **Unpräfixierter Pfad** (Legacy-Fallback) — existiert evtl. nicht
4. **`-latest` Version-Fallback** — ruft `get_model_version(model_id, provider="api")` auf und sucht `{base}-{version}.json`; Rückfall auf unpräfixierten Pfad wenn version stale

Rückgabewert ist immer ein `Path` — Aufrufer müssen `.exists()` prüfen.

#### `CARD_DIR: Path`

Konstante für das Card-Verzeichnis. Nie als `Path("benchmark_scores/model_cards")` inline schreiben.

```python
CARD_DIR  # → Path("benchmark_scores/model_cards")
```

#### `get_use_case_primary(model_id: str, card_data: dict | None = None) → str`

Liefert `use_case_primary` aus der Card mit Fallback `"generalist"`. Niemals direkt `.get("use_case_primary")` ohne Fallback aufrufen.

```python
get_use_case_primary("qwen2.5vl:7b")          # → "vision-language"
get_use_case_primary("codestral-latest")       # → "coding"
get_use_case_primary("unknown-model")          # → "generalist" (Fallback)
```

#### `normalize_model_id(model_id: str) → str`

Strippt bekannte Vendor-Präfixe (z. B. `hf.co/AUTHOR/`) und liefert die kanonische Modell-ID. Erster Schritt jeder ID-Bridge.

```python
normalize_model_id("hf.co/bartowski/Qwen-7B-GGUF:Q4_K_M")
# → "Qwen-7B-GGUF:Q4_K_M"

normalize_model_id("claude-sonnet-4-5-20250929")  # → unverändert
```

> **Nicht für Card-Pfade verwenden** — `normalize_model_id()` allein reicht nicht aus, weil Doppelpunkt/Punkt/Slash noch nicht ersetzt sind. Für Card-Pfade → `resolve_canonical_model_id()` (siehe unten).

#### `strip_date_suffix(model_id: str) → str`

Entfernt Datums-Suffixe in der Form `-YYYYMMDD` (8 Ziffern) oder `-MMDD` (4 Ziffern mit gültigem Monat 01-12). Idempotent.

```python
strip_date_suffix("claude-haiku-4-5-20251001")  # → "claude-haiku-4-5"
strip_date_suffix("qwen3-32b-1225")            # → "qwen3-32b"
strip_date_suffix("mistral-large-3")           # → unverändert (kein Suffix)
```

> **Anwendung:** Lookup-Vergleiche zwischen einer versionierten Config-ID (`claude-haiku-4-5-20251001`) und einer Suffix-strip-ten historischen Card (`claude-haiku-4-5`).

#### `resolve_canonical_model_id(model_id: str) → str`

**Die zentrale ID-Bridge.** Liefert die kanonische Form einer Modell-ID, indem drei Quellen in dieser Reihenfolge geprüft werden:

1. **Card-Lookup** (per `_find_card()`) — falls die ID direkt oder mit Suffix-Strip eine existierende Card findet, wird der `model_id` aus der Card zurückgegeben.
2. **Date-Suffix-Strip** — vergleicht gegen vorhandene Cards ohne Datums-Suffix.
3. **`_safe_name()`-Fallback** — falls keine Card existiert, wird die kanonische `_safe_name()`-Transformation angewendet (Sonderzeichen → Underscore).

```python
resolve_canonical_model_id("hf.co/bartowski/Qwen-7B-GGUF:Q4_K_M")
# → "Qwen-7B-GGUF:Q4_K_M" (kein Card-Match → Step 3: safe_name-normalisiert)

resolve_canonical_model_id("claude-haiku-4-5")
# → "claude-haiku-4-5-20251001" (Card-Match via Suffix-Strip)

resolve_canonical_model_id("mistral-large-latest")
# → "mistral-large-latest" (kein Card-Match, keine Normalisierung nötig)
```

**Wann nutzen?** Immer wenn ein roher Modellname in eine **kanonische Form** für Card-Pfade, Cross-File-Mappings oder Lookup-Keys überführt werden muss.

> **Brücken-Klassifikation:** `resolve_canonical_model_id()` ist der **Card-/Path-Use-Case**. Für **Leaderboard-/Display-Use-Cases** (menschenlesbare Vendor-Schreibweise) stattdessen `normalize_model_id()` + optional `strip_date_suffix()` verwenden.

#### `enforce_card_first(model_id: str, model_cfg: dict | None = None) → tuple[str, bool]`

**Card-First-Vertrag** (genutzt in `utils/result_manager.py::save_results`). Stellt sicher, dass jede geschriebene `model_id` durch eine Model Card im Filesystem abgedeckt ist.

- Card vorhanden → `(canonical_id, True)` (kein Warning)
- Card fehlt → `ensure_card()` legt Platzhalter-Draft an, WARNING wird geloggt, Rückgabe `(canonical_id, False)` (kein Hard-Fail)

```python
canonical, has_card = enforce_card_first("claude-sonnet-4-5-20250929")
# has_card == True, falls Card existiert; sonst False + Draft wurde angelegt

canonical, has_card = enforce_card_first("unregistered-model-xyz")
# canonical == "unregistered-model-xyz"
# has_card == False
# → ensure_card() wurde aufgerufen, Draft unter benchmark_scores/model_cards/ angelegt
# → WARNING geloggt, Benchmark läuft weiter
```

> **Wichtig:** `enforce_card_first()` ist **kein** Hard-Fail. Ein unregistriertes Modell bricht den Benchmark-Lauf nicht ab — die Lücke wird stattdessen als Draft sichtbar und wandert in die Kartenpflege.

> **`model_cfg`-Parameter (ab Session 52):** Wenn `model_cfg` mit `card_model_id`-Feld übergeben wird (z.B. Thinking-Profil), nutzt `enforce_card_first` die Original-Card via `card_model_id`-Redirect statt eine Platzhalter-Card zu erstellen. `ResultManager._find_model_cfg()` löst die model_cfg aus der expandierten Config auf und reicht sie durch.

---

### Provider-Shortcodes

Shortcodes sind an zwei Stellen synchron gepflegt:

1. **`utils/model_utils.py`** → `_PROVIDER_SHORTCODES: dict[str, str]` + `get_provider_shortcode(provider)`
2. **`config/provider_config.yaml`** → `providers.<section>.<provider>.short_code`

| Shortcode | Bedeutung | Provider-Schlüssel |
|---|---|---|
| `API` | Proprietäre Direkt-API | `anthropic`, `openai`, `google`, `xai`, `mistral` |
| `OR` | OpenRouter (Routing-Layer) | `openrouter` |
| `GR` | Groq (Inferenz-Dienst) | `groq` |
| `LCL` | Lokales Ollama-Modell | `ollama_local`, `ollama`, `local` |
| `LCL` | Lokales llama.cpp-Modell | `llamacpp` |

Der Shortcode erscheint im Leaderboard als Suffix der Versionsspalte (`k2/OR`, `4-mini/API`, `4760c3/LCL`).

---

### Versionsermittlung

`get_model_version(model_name, provider, client)` in `utils/model_utils.py` liefert die **nackte Version** — ohne Provider-Suffix. Die Kombination mit dem Shortcode für die Anzeige übernimmt `scripts/leaderboard/exporter.py`.

#### Lookup-Hierarchie (in dieser Reihenfolge)

1. **Card-First:** `model_version`-Feld in der JSON-Card → hat immer Vorrang. Nützlich für manuelle Korrekturen oder Modelle mit ungewöhnlichen ID-Formaten.

   **Konvention für `model_version` in lokalen GGUF-Cards:**
   Das Feld beschreibt **Quantisierungsstufe und Format** — nicht die Download-Plattform.
   - `"Q4_K_M (GGUF)"` → Quantisierungsstufe + Format
   - `"GGUF (E4B)"` → Format + Architekturvariante bei unbenannter Quant-Stufe
   - **Nicht** in `model_version`: `"Hugging Face"`, `"Ollama Hub"`, `"local"` — das ist die Download-Plattform, nicht die Version.
   Die Download-Plattform gehört in das separate Feld `weights_source` (z. B. `"Hugging Face"`, `"Ollama Hub"`, `"official"`).

2. **Ollama-Hash (nur bei lokalen Providern):** `ollama list` → 7-stelliger Hex-Hash (z.B. `4760c3`). Erkennt Silent Updates sofort am Hash-Wechsel.

3. **Regex/Mapping für kommerzielle APIs:**

   | Familie | Beispiel-ID | Ergebnis |
   |---|---|---|
   | Anthropic | `claude-sonnet-4-6` | `4.6` |
   | Anthropic (datiert) | `claude-haiku-4-5-20251001` | `20251001` |
   | OpenAI | `gpt-4o` | `2024-05-13` |
   | OpenAI o-Serie | `o4-mini` | `4-mini` |
   | Mistral | `mistral-large-latest` | `2411` |
   | Codestral/Magistral | `magistral-medium-latest` | `latest` |
   | Google | `gemini-2.5-pro` | `2.5-pro` |
   | xAI | `grok-3-mini` | `3-mini` |
   | OpenRouter (namespaced) | `moonshotai/kimi-k2-0711` | `k2-0711` |
   | OpenRouter (namespaced) | `z-ai/glm-5.1-20260406` | `5.1-20260406` |
   | OpenRouter (namespaced) | `minimax/minimax-m2.7-20260318` | `m2.7-20260318` |
   | Groq (namespaced) | `qwen/qwen3-32b` | `3-32B` |

4. **Fallback:** `"latest"` wenn kein Muster greift.

---

### Vollständiger Prozess: Von der Config-ID zur Leaderboard-Zeile

```
config/provider_config.yaml
  providers.commercial.openrouter.models[].id = "moonshotai/kimi-k2-0711"
       │
       │  Benchmark-Run
       ▼
cloud_models_benchmark.csv
  model = "moonshotai/kimi-k2-0711"
  version = "k2-0711"          ← get_model_version() → Regex → "k2-0711"
  provider = "openrouter"
       │
       │  make leaderboard
       ▼
benchmark_leaderboard.csv
  Model Name = "Kimi K2 Thinking"       ← display_name aus Model Card
  Version    = "k2-0711/OR"             ← version + "/" + shortcode
       │
       │  _card_path("moonshotai/kimi-k2-0711", "openrouter")
       ▼
benchmark_scores/model_cards/moonshotai_kimi-k2-0711.json
  → Regel 1: namespaced → kein Prefix
  → Dateiname: moonshotai_kimi-k2-0711.json
```

---

### Card-Generierung

`scripts/analysis/generate_model_cards.py` erstellt ein leeres Template für eine neue Model Card — ohne LLM-Call, ohne API-Zugriff. Es ist der Einstiegspunkt für jede neue Modellaufnahme.

```bash
make model-cards MODEL=claude-opus-4-7              # Card-Template anlegen
make model-card  MODEL=qwen3:14b PROVIDER=ollama_local  # mit Provider-Präfix (LCL_*)
make model-cards                                    # interaktive Eingabe
```

1. Berechne `_card_path(model_id, provider_key, for_write=True)` → kanonischer Pfad
2. Falls Datei existiert und `--force` nicht gesetzt → Fehler (kein versehentliches Überschreiben)
3. Template mit allen Pflichtfeldern als `"TODO"`-Platzhalter + automatisch berechnetem `size_class` schreiben

**Nach der Template-Erstellung:** Alle `"TODO"`-Felder manuell befüllen, dann `card_status` auf `"complete"` setzen. Der Thinking-Probe-Workflow (`make probe-thinking MODEL=...`) ergänzt die `thinking_probe_*`-Felder automatisch vor dem ersten Benchmark-Run.

### Card-Lifecycle v2 (ab v4.10.0)

Seit v4.10.0 gibt es drei dedizierte Targets, die Erstellung, Struktur-Sync
und LLM-Recherche kapseln. Sie nutzen den vorhandenen Phase-1-Stack
(`manage_model_cards.py`, `sync_cards.py`, `ensure_card()`) und sind als
**dünne Wrapper** konzipiert — keine Duplikation der Sync- oder
LLM-Logik.

```bash
# 1. Neue Card anlegen (Skeleton + Pre-Fill aus provider_config.yaml)
make card-create MODEL=claude-sonnet-4-6

# 2. Struktur mit Template synchronisieren (deterministisch, kein LLM)
make card-validate                              # alle Cards
make card-validate MODEL=claude-sonnet-4-6      # einzelne Card
make card-validate YES=1                        # auto-ja fuer Loesch-Bestaetigung

# 3. Inhaltliche LLM-Recherche (mit profile_verified-Lock)
make card-research                              # alle unveraifizierten
make card-research MODEL=claude-sonnet-4-6      # einzelne Card
make card-research FORCE=1                      # auch verifizierte
make card-research DRY=1                        # Vorschau (kein Lock, kein Write)
```

**Implementation Map:**

| Target | Script | Mode | LLM? |
|---|---|---|---|
| `card-create` | `scripts/dev/create_model_card.py` | (eigenes) | nein |
| `card-validate` | `scripts/analysis/sync_cards.py` | `--card-type model` / `--model <id>` | nein |
| `card-research` | `scripts/manage_model_cards.py` | `--mode research` | ja |

**Warum `card-validate` und nicht nur `cards-sync`?**

`cards-sync` bleibt für Vendor-Cards und Cross-Type-Sync (`--card-type all`).
`card-validate` ist der **Model-Card-spezifische Wrapper** mit komfortablem
`MODEL=<id>`-Flag — der häufigste Use-Case in der redaktionellen Pflege.

**Warum eigener `card-research`-Modus statt eigenes Skript?**

`manage_model_cards.py` hat bereits die gesamte LLM-Infrastruktur
(`LLMSession`, `LLMSpec`, Override-Hierarchie, `OPERATOR_PROTECTED_FIELDS`,
JSON-Parser, Editor-Prompt-Loader). Der `--mode research`-Zweig fügt
nur die Lock-/Backup-Mechanik und Recherche-spezifische Findings
hinzu — keine Duplikation.

**Lock-Mechanismus:** `profile_verified` wird zu Beginn auf `false`
gesetzt (Resumption-Marker bei Abbruch), am Ende auf `true` zurück
mit `profile_verified_at` und `profile_verified_by="llm:<model>"`.
Kein File-Lock, keine `flock`-Dateien. Bei LLM-Fehler bleibt der
Lock offen — der nächste `make card-research` greift die Karte
automatisch wieder auf.

Vollständige Dokumentation (Workflows, Fehler-Verhalten, Pre-Check-Heuristik):
[docs/CARD_MANAGEMENT.md → Card-Lifecycle v2](CARD_MANAGEMENT.md#card-lifecycle-v2-ab-v4100).

---

### Historische Daten: Migration

Veraltete `k.A.`-Werte in Benchmark-CSVs können mit dem Migrations-Skript bereinigt werden:

```bash
.venv/bin/python scripts/maintenance/migrate_model_versions.py
```

Das Skript legt `.bak`-Backups aller drei Benchmark-CSVs an und füllt leere / `k.A.`-Versionswerte über `get_model_version()` nach.

---

### Model Card Schema — Pflichtfelder

Jede Model Card JSON muss folgende Felder enthalten. Cards mit `card_status: "draft"` sind manuell erstellte Templates (via `make model-card`) und dürfen `"TODO"`-Platzhalter enthalten. `card_status: "minimal"` kennzeichnet automatisch durch den ThinkingProbe-Hook angelegte Minimal-Cards (nur Probe-Felder befüllt). `card_status: "complete"` signalisiert, dass alle Pflichtfelder befüllt sind.

#### Kern-Identität

| Feld | Typ | Beschreibung |
|---|---|---|
| `model_id` | string | Kanonische API-ID (z. B. `"mistral-large-2411"`, `"hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M"`) — SSoT für alle Lookups |
| `display_name` | string | Anzeigename im Frontend |
| `vendor` | string | API-Anbieter (z. B. `"Mistral AI"`, `"OpenAI"`) |
| `card_status` | string | `"draft"` / `"minimal"` / `"complete"` — steuert Vollständigkeits-Guards |
| `heritage_ids` | list[string] | Frühere Model-IDs / Alias-Namen, unter denen Review-Dirs abgelegt wurden. Web-Exporter fällt bei fehlender primärer Dir auf diese zurück. |

#### Profile-Verifikation (ab v4.9.0, erweitert v4.10.0)

| Feld | Typ | Default | Bedeutung |
|---|---|---|---|
| `profile_verified` | bool | `false` | Inhaltliche Felder wurden recherchiert und verifiziert (Editor-Prompt `model_card_verification`) |
| `profile_verified_at` | str | `null` | ISO-8601-Datum der letzten Verifikation (YYYY-MM-DD) |
| `profile_verified_by` | str | `null` | Wer hat verifiziert: `"human"` \| `"llm:<model>"` \| `null` (v4.10.0) |
| `last_modified_at` | str | `null` | ISO-8601-Datum der letzten inhaltlichen Änderung (v4.10.0) |

#### Architektur & Deployment

| Feld | Typ | Werte / Format | Beschreibung |
|---|---|---|---|
| `parameter_architecture` | string | `dense` / `moe` | Dense = alle Parameter aktiv; MoE = nur Teilnetzwerke aktiv |
| `params_total_b` | float | z. B. `14.0` | Gesamtparameter in Milliarden (**optional**, null bei proprietären Modellen ohne Angabe) |
| `params_active_b` | float | z. B. `3.5` | Aktive Parameter (MoE); bei MoE ist dies der relevante Vergleichswert (**optional**, null bei proprietären Modellen) |
| `context_window_k` | integer | z. B. `128` | Maximales Kontextfenster in Kilotoken |
| `knowledge_cutoff` | string | `YYYY-MM` | Trainingsdaten-Stichtag (**optional**, wird nachgetragen wenn bekannt) |
| `size_class` | string | `Nano` / `Edge` / `Desktop` / `Workstation` / `Server` / `Frontier` | Hardware-Tier — abgeleitet aus Parameteranzahl oder API-Only-Status |
| `deployment_type` | string | `api_only` / `local_weights` | Ob das Modell lokal deploybar ist |
| `supports_tool_use` | boolean | `true` / `false` | Function-Calling-Unterstützung |
| `use_case_primary` | string | `generalist` / `coding` / `reasoning` / `vision-language` / `agentic` | Steuert den Reviewer-Bewertungsrahmen |

#### Lizenz & Kategorisierung

| Feld | Typ | Beschreibung |
|---|---|---|
| `weights_license_tier` | string | `proprietary` / `restricted-weights` / `open-weights` — Bestimmt die Kategorie-Anzeige via `get_model_category()` |
| `license` | string | SPDX-ID oder Kurzname (z. B. `"Apache-2.0"`, `"Meta Community License"`) |
| `license_url` | string | URL zur Volllizenz (**optional**, null bei Proprietary) |
| `commercial_use_allowed` | boolean / null | `true` = frei kommerziell nutzbar; `false` = verboten; `null` = skalenabhängig / unklar |
| `weights_provenance_risk_rationale` | string | Begründung für Lizenz-/Herkunftsrisiken (z. B. CNKI-Verbindungen, dual-use) |

#### Pricing (SSoT)

| Feld | Typ | Beschreibung |
|---|---|---|
| `input_price_per_1m` | float | Preis pro 1M Input-Tokens in USD (**optional**, null bei lokalen Modellen) |
| `output_price_per_1m` | float | Preis pro 1M Output-Tokens in USD (**optional**, null bei lokalen Modellen) |

**Wichtig:** Preise gehören ausschließlich in die Model Card.

#### Thinking Probe

| Feld | Typ | Beschreibung |
|---|---|---|
| `thinking_probe_capable` | boolean | Ob das Modell Chain-of-Thought-Denken zeigt |
| `thinking_probe_evidence` | string | Erklärung der Evidenz (Signal A / B) |
| `thinking_probe_manual_override` | boolean | `true` wenn Wert manuell gesetzt (z. B. OpenAI o-Series ohne `reasoning_tokens`) |
| `thinking_probe_at` | string | ISO-Timestamp des letzten Probe-Runs |

**Signals:** Signal A = `<think>`-Tags in Antwort, Signal B = `reasoning_tokens > 0`. Response-Länge ist kein Signal (ThinkingProbe Signal-C-Verbot, siehe AGENTS.md).

---

**Taxonomy-SSoT:** Die erlaubten Werte für `use_case_primary` und `size_class` (inkl. `reviewer_guidance` pro Wert) liegen in `config/classification_taxonomy.json`. Dieses File wird von `generate_review.py` beim Start eingelesen und als `{use_case_classification_context}` in den Reviewer-Prompt injiziert.

**Hilfsfunktionen:**
- `get_use_case_primary(model_id, card_data=None)` → `use_case_primary` mit Fallback `"generalist"`
- `get_model_category(model_id, card_data=None)` → **einziger** Einstiegspunkt für Display-Kategorie-Strings; liefert `"Proprietär"` / `"Restricted Weights"` / `"Open Weights"` — niemals selbst ableiten oder hardcoden

### Migration: Neue Card-Felder nachpflegen

Wenn neue Pflichtfelder eingeführt werden, stehen dedizierte Migrationsskripte bereit:

```bash
# use_case_primary in alle bestehenden Cards eintragen
python scripts/dev/migrate_use_case_primary.py --dry-run   # Vorschau
python scripts/dev/migrate_use_case_primary.py             # Ausführen

# context_window_k und knowledge_cutoff nachpflegen
python scripts/dev/migrate_context_fields.py --dry-run
python scripts/dev/migrate_context_fields.py
```

Die Skripte überspringen Cards, die das Feld bereits haben, und geben einen tabellarischen Report aus (Modell | Assigned Value | Basis der Zuweisung).

### Modell vollständig entfernen

`make clean-model MODEL=<id>` (via `scripts/maintenance/clean_results.py`) entfernt seit v3.8.1 alle Spuren eines Modells in einem einzigen Schritt:

- CSV-Zeilen aus allen Benchmark-, PC- und Leaderboard-CSVs (inkl. `cost_log.csv`)
- `outputs/audit_logs/<dir>/`, `outputs/comparisons/<dir>/`, `outputs/runs/<dir>/`
- `docs/reviews/<dir>/`
- Model Card JSON (`benchmark_scores/model_cards/<card>.json`) — **alle Varianten** (Underscore, Hyphen, Punkt)
- Political-Compass-Session-Checkpoint (`outputs/temp/session_*.json`)

```bash
make clean-model MODEL="mistral-large-2411"       # Löschen
make clean-model MODEL="mistral-large-2411" DRY=1 # Vorschau
```

**Variant-Handling (ab v4.10.7):** Model-IDs existieren oft in mehreren Schreibweisen (z.B. `grok-4_1-fast-reasoning`, `grok-4-1-fast-reasoning`, `grok-4.1-fast-reasoning`). `_collect_model_id_variants()` sammelt automatisch alle Varianten über `_safe_name()` + Card-Inhalt-Scan und bereinigt ALLE Spuren. Die Reihenfolge ist kritisch: CSVs werden VOR Cards bereinigt, da `resolve_canonical_model_id()` die Card für die Variant-Auflösung benötigt.

Verwaiste Verzeichnisse (kein Leaderboard-Eintrag mehr, aber Dir noch vorhanden) lassen sich mit `make clean-model PRUNE_ORPHANS=1` aufspüren und entfernen.

### SSOT Prinzip (Single Source of Truth)

Die `config.yaml` gliedert sich in **zwei Bereiche**:

#### 1. GLOBAL (Mandatory) – Framework-Contract

```yaml
# ====================================================================
# GLOBAL CONFIGURATION (Required by Framework)
# ====================================================================

metadata:
  id: "your_module"                    # Eindeutige ID (Dateiname-Prefix)
  name: "Your Module Name"             # Anzeigename im Leaderboard
  version: "1.0.0"                     # SemVer
  description: "What this module tests"

integration:
  leaderboard:
    enable_scoring: true               # false = Info-Modul (kein Ranking)

    # Fallback für alle Assets ohne eigene Definition
    default_contribution:
      routine: 1.0                     # 100% Routine-Anteil
      reasoning: 0.0                   # 0% Reasoning-Anteil

    # Spalten im Leaderboard (optional)
    columns:
      - id: "your_score"
      - label: "Your Score"

execution:
  test_class: "YourModuleTest"         # Klassenname in test.py
  execution_mode: "standard"           # "standard" oder "batch"
  assets_dir: "assets"                 # Verzeichnis mit YAML-Files

# ====================================================================
# BENCHMARK DEFINITIONS (Cascading Scoring)
# ====================================================================

benchmarks:
  # Fall A: Standard (erbt default_contribution)
  - id: "your_module_001"
    name: "Basic Task"
    tier: 1

  # Fall B: Ausnahme (überschreibt Default)
  - id: "your_module_002"
    name: "Complex Puzzle"
    tier: 3
    score_contribution:
      routine: 0.2                     # 20% Routine
      reasoning: 0.8                   # 80% Reasoning
```

---

### OUTPUT CONTRACT: BENCHMARK RESULT

---

Jeder Controller (`test.py`) muss ein `BenchmarkResult`-Objekt zurückgeben. Dieses strikt typisierte DTO stellt sicher, dass alle Module kompatible Daten für das Leaderboard liefern.

Das Result Schema (`schemas/result.py`) enthält:

```python
class BenchmarkResult(BaseModel):
    status: str
    primary_score: Optional[float]
    rendered_value: str

    # Execution Metrics
    execution_time: float   # Total runtime (Inference + Latency)
    load_time: float        # Cold Start / Loading to VRAM (Ollama specific)

    # ...
```

`load_time` lässt sich in `execute()` wie folgt befüllen:

```python
# Example in your Controller (test.py)
load_time = getattr(llm_client, "last_response_metadata", {}).get("load_duration", 0.0)

return BenchmarkResult(
    # ...
    load_time=load_time,
    # ...
)
```

```python
from schemas.result import BenchmarkResult

# The Object Schema
class BenchmarkResult(BaseModel):
    status: str = "success"           # success | error | truncated | verbose_outlier | language_mismatch
    primary_score: Optional[float]    # 0.0 - 100.0 (ranking)
    rendered_value: str = "N/A"       # Display string ("85.5 %")

    # Execution Metrics
    execution_time: float             # Seconds
    tokens_used: int                  # Estimated token count
    cost_usd: float                   # Estimated cost
    raw_response: str                 # The full LLM output text

    # Identification
    model_version: str                # Nackte Version, z.B. "4.6", "k2", "latest" (kein Shortcode-Suffix)

    # Deep Data
    data: Dict[str, Any] = {}         # Module-specific details metrics
    meta: Dict[str, Any] = {}         # Context (timestamp, prompt_len)
```

**Warum strikt typisiert?**
Frühere Versionen gaben lose Dictionaries zurück. Das führte zu chaotischen CSV-Spalten (`score` vs. `total_score` vs. `result`). Die `BenchmarkResult`-Klasse erzwingt einen einzigen Standard.

---

#### 2. LOKAL (Optional) – Modul-spezifische Config

```yaml
# ====================================================================
# LOCAL CONFIGURATION (Module-specific, ignored by framework)
# ====================================================================

config:
  keyword_threshold: 0.4               # Min. 40% Keywords gefunden
  semantic_threshold: 0.78             # Semantische Ähnlichkeit

parameters:
  max_response_length: 2000
  timeout_seconds: 30

interpretation:
  tier1_description: "Labeled errors (easy)"
  tier2_description: "Obvious issues (medium)"
```

**Zugriff in test.py:**

```python
self.config = self.load_config()
threshold = self.config['config']['keyword_threshold']
```

---

### Execution Modes

| Mode | Verhalten | Use Case |
|------|-----------|----------|
| **`standard`** | Framework lädt Assets einzeln, instanziiert Test pro Asset | Code Quality, UX Writing (isolierte Tests) |
| **`batch`** | Framework übergibt alle Assets, Test kontrolliert Loop | Political Compass (3× Runs), Custom Aggregation |

---

### Kaskadierende Score-Contributions

Das Framework berechnet **Routine Score** und **Reasoning Score** automatisch als Durchschnitt der entsprechenden Module.

1. **Asset-Level** (höchste Priorität):

   ```yaml
   - id: "reasoning_5d_002"
     score_contribution:
       reasoning: 1.0  # Ordnet dieses Asset dem Reasoning Score zu
   ```

2. **Modul-Level** (Standard):
   Definiert in `config.yaml` → `integration` → `default_contribution`.

   - `routine: 1.0` → Zählt zum „Routine Score" (z. B. Documentation, UX)
   - `reasoning: 1.0` → Zählt zum „Reasoning Score" (z. B. Logical Reasoning)

3. **Total Score Berechnung:**

   ```python
   Total Score = (Routine Score + Reasoning Score) / 2
   ```

---

## Asset-Format (YAML-Schema)

### Namenskonvention & Gruppierung (Last-Hyphen-Rule)

Das Framework ermittelt die Anzahl der Tests anhand der Dateinamen im `assets/`-Ordner. Die Logik basiert auf dem **letzten Bindestrich (`-`)**:

- Alles **vor** dem letzten Bindestrich (gefolgt von Ziffern) gilt als **Gruppen-ID**.
- Alles **danach** ist die Variante und zählt nicht separat.

| Dateiname | Erkannte Gruppe | Zählt als... |
|-----------|-----------------|--------------|
| `test_001.yaml` | `test_001` (Ganze Datei) | **1 Test** |
| `pol_axis1-001.yaml` | `pol_axis1` | **1 Test** (zusammen mit -002) |
| `pol_axis1-002.yaml` | `pol_axis1` | (Variante, zählt nicht extra) |

---

### Standard-Assets

```yaml
meta:
  id: "your_module_001"                # Muss mit Dateiname übereinstimmen
  difficulty: 2                        # Tier (1-4)
  name: "Descriptive Task Name"
  tags: ["category", "subcategory"]    # Optional

input:
  prompt: |
    Your instruction to the LLM.
    Can be multi-line.

  context: |                           # Optional: Zusätzlicher Context
    Background information...

evaluation:
  # Keyword-basierte Bewertung
  keywords:
    - "expected_term_1"
    - "expected_term_2"

  # Semantische Referenz (optional)
  golden_answer: |
    The ideal response should explain...

  # Strukturelle Anforderungen (optional)
  min_length: 100
  max_length: 500
  required_format: "markdown"          # markdown, json, code, text

# Hard Constraints (optional) ─────────────────────────────────────────
# Werden NACH dem inhaltlichen Scoring ausgewertet. Ein Verstoß löst
# eine automatische Penalty aus (unabhängig von der inhaltlichen Qualität).
constraints:
  max_expected_words: 150              # Wortanzahl-Obergrenze (progressiv)
  # Penalty-Stufen: ≤120% kein Abzug | 121–200% −20% | 201–300% −40% | >300% −60%
  # Trigger und Stufe werden als > [!WARNING] ins Audit-Log geschrieben.

# Metadaten (optional, für Sprach-Constraint) ──────────────────────────
metadata:
  language: "de"                       # "de" → Language-Mismatch-Check aktiv
  # Das Framework prüft per DE/EN-Marker-Heuristik, ob die Antwort
  # in der Zielsprache verfasst ist. Bei EN-Antwort auf DE-Task:
  # status = "language_mismatch" (kein Score-Abzug, separater Status-Flag).
```

---

### Info-Module (Structured Output)

Für Module ohne Scoring (z. B. Political Compass):

```yaml
meta:
  id: "political_compass_q001"

input:
  prompt: "Statement: Free markets solve all problems."

evaluation:
  # Keine Keywords! Stattdessen:
  output_type: "coordinate"            # coordinate, label, json
  expected_structure:
    x_range: [-10, 10]                 # Wirtschaftliche Achse
    y_range: [-10, 10]                 # Soziale Achse
```

---

## Scoring-Logik implementieren

### Architektur-Prinzip: MVC

```text
test.py (Controller)
   ↓ delegiert an
core/evaluators.py (Model/Logic)
   ↓ nutzt
core/constants.py (Config/Data)
```

**Regel:** `test.py` darf **keine** Scoring-Logik enthalten. Es orchestriert nur den Aufruf und verpackt das Ergebnis in `BenchmarkResult`.

### Der Controller (`test.py`)

```python
from schemas.result import BenchmarkResult

def execute(self, model: str, llm_client: Any, **kwargs) -> BenchmarkResult:
    # 1. Run LLM
    start_time = time.time()
    response_text = llm_client.query(prompt, ...)
    elapsed_time = time.time() - start_time

    # 2. Return pre-scored BenchmarkResult
    return BenchmarkResult(
        status="success",
        raw_response=response_text,
        execution_time=elapsed_time,
    )

def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
    # 3. Delegate to pure text Evaluator
    evaluator = CodeQualityEvaluator(self.asset)
    scoring_result = evaluator.score_response(result.raw_response)

    # 4. Map Dict to the BenchmarkResult fields
    result.primary_score = scoring_result.get("score")
    result.tier = scoring_result.get("tier", "Tier 1 (Undefined)")
    result.data = scoring_result
    result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"

    return result
```

---

### Beispiel: `core/evaluators.py`

```python
# Scoring Logic for Your Module

from typing import Dict, Any
import re

class YourEvaluator:
    # Evaluates LLM responses against criteria

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.keyword_threshold = self.config.get('keyword_threshold', 0.4)

    def evaluate(self, response_text: str, asset: Dict) -> Dict[str, Any]:
        # Main entry point
        # Args: response_text (raw LLM output), asset (YAML definition)
        # Returns: dict with score, details, passed flag

        # 1. Preprocessing
        clean_text = self._clean_response(response_text)

        # 2. Component Scoring
        keyword_score = self._check_keywords(clean_text, asset)
        structure_score = self._check_structure(clean_text, asset)

        # 3. Weighted Aggregation
        total_score = (keyword_score * 0.7) + (structure_score * 0.3)

        return {
            "score": total_score,
            "details": {
                "keywords": keyword_score,
                "structure": structure_score
            },
            "passed": total_score >= 50.0
        }

    def _clean_response(self, text: str) -> str:
        # Remove thinking tags, normalize whitespace
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return text.strip()

    def _check_keywords(self, text: str, asset: Dict) -> float:
        # Keyword matching with threshold
        # Returns: 0-100 based on percentage of keywords found
        keywords = asset.get('evaluation', {}).get('keywords', [])
        if not keywords:
            return 100.0

        found = sum(1 for kw in keywords if kw.lower() in text.lower())
        percentage = (found / len(keywords))

        if percentage >= self.keyword_threshold:
            return 100.0 * percentage
        else:
            return 0.0

    def _check_structure(self, text: str, asset: Dict) -> float:
        # Check formatting requirements
        min_len = asset.get('evaluation', {}).get('min_length', 0)

        if len(text) >= min_len:
            return 100.0
        else:
            return (len(text) / min_len) * 100.0
```

---

## CSV-Output & Leaderboard

### Automatische Spalten

| Spalte | Typ | Quelle |
|--------|-----|--------|
| `asset_id` | String | Dateiname |
| `model` | String | Parameter |
| `timestamp` | DateTime | System |
| `execution_time` | Float | `BenchmarkResult.execution_time` |
| `total_score` | Float | `BenchmarkResult.primary_score` |
| `percentage` | Float | Normalisiert (0–100) |
| `routine_contribution` | Float | config.yaml |
| `reasoning_contribution` | Float | config.yaml |
| `thinking_mode` | String | `utils/base_runner.py:_resolve_thinking_mode()` — `"Thinking"`/`"Standard"`/`"n/a"` pro Task. Automatisch via `_get_updated_fieldnames()`. Wird auch im Leaderboard als `"Thinking Mode"`-Spalte angezeigt. |

### Custom Spalten

Das Framework schreibt automatisch die Werte aus `BenchmarkResult.data` in die CSV, sofern sie flach genug sind.

```python
# Evaluator return
return {
    "score": 85.0,
    "details": {
        "keyword_match": 100.0,    # Wird CSV-Spalte
        "structure_score": 70.0    # Wird CSV-Spalte
    }
}
```

---

## Tests & Validierung

### Asset-Schema prüfen

```bash
make validate-assets
```

### Modul-Isolations-Test

```bash
# Nur dein Modul in benchmark_config.yaml aktivieren
make benchmark-single MODEL=qwen2.5:7b MODULE=your_module
```

### Leaderboard-Integration

```bash
make leaderboard
# Prüfen: Ist die Spalte da? Sind die Werte korrekt?
```

---

## Best Practices

### DO's ✅

1. **MVC-Trennung:** test.py = Controller, evaluators.py = Logik
2. **Determinismus:** Fixe Seeds, kein Random ohne Seed
3. **Config-First:** Schwellenwerte in config.yaml
4. **Dokumentation:** README.md nach Template

### DON'Ts ❌

1. **Keine LLM-Calls in Evaluators**
2. **Keine Modell-spezifischen Hacks** (unfairer Boost)
3. **Keine Silent Failures** (Exceptions loggen!)

---

## Fehlerbehebung

### „Scores are always 0%"

Debug-Checklist:

1. Nimmt `score_response()` ein `BenchmarkResult` an und gibt es zurück?
2. Wird `score_dict["score"]` zu `result.primary_score` übertragen?
3. Keywords case-sensitive?

Debug-Tool:

```bash
python run_benchmark.py --debug-responses
```

---

## Weiterführende Ressourcen

- **ARCHITECTURE.md** – System-Design & MVC-Patterns
- **USER_GUIDE.md** – Wie Nutzende Module ausführen
- **GOLDEN_STANDARDS.md** – Referenz-Methodik
- **BACKUP_STRATEGY.md** – Backup-Lifecycle, SSoT-Konfiguration und Pre-Backup-Hygiene (Phase 27)
- **MAINTENANCE_LOG.md** – v4.6.6 Phase-27-Eintrag mit SSoT-Refactor-Diffs
>>>>>>>+++++++ REPLACE


---

**Dokumenten-Version:** 5.1.2 (Ueberarbeitung 2026-08)\
**Kompatibel mit:** CrucibleMark v3.8.2+
