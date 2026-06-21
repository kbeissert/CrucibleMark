# Thinking-Probe — Methodik, SSoT und Konsumenten

> **Single Source of Truth** für die Thinking-Erkennung in CrucibleMark.
> Empirische Probe (`probe_thinking_model`) + Card-First-Property + optionaler `thinking_override` (Provider-Card).

**Inhalt:**

- [Zweck und Motivation](#zweck-und-motivation)
- [Drei-Signal-Hierarchie](#drei-signal-hierarchie)
- [Multi-Prompt-Aggregation](#multi-prompt-aggregation)
- [Bekannte Think-Tags](#bekannte-think-tags)
- [Inline-CoT-Heuristik (Signal C)](#inline-cot-heuristik-signal-c)
- [SSoT-Auflösung: Card + Override (ab v4.7.1)](#ssot-auflösung-card--override-ab-v471)
- [Override-Aktivierungs-Regeln](#override-aktivierungs-regeln)
- [Runner-Consumer-Anbindung (ab v4.7.1)](#runner-consumer-anbindung-ab-v471)
- [Discovery-Inventar](#discovery-inventar)
- [Offene Folgearbeiten](#offene-folgearbeiten)

---

## Zweck und Motivation

CrucibleMark braucht pro Modell eine verlässliche Aussage, ob es sich um ein **Reasoning-/Thinking-Modell** handelt. Diese Information beeinflusst:

- **Token-Budget** (Reasoning → 5×-Multiplikator, siehe `resolve_token_budget()`)
- **Provider-seitige Reasoning-Steuerung** (z. B. `enable_thinking: false`)
- **Konsument-Anpassungen** in Modulen mit Reasoning-Slots (`reasoning_logic`, `code_quality`, `political_compass`)

**Frühere Probleme (v3.5.x und früher):**

- Heuristik via String-Trigger (`magistral`, `o1`, `kimi-k2` im Modellnamen) — fehleranfällig bei Aliases
- Config-only Override via `enable_thinking` — empirisch unzuverlässig (Discovery-Fund 2026-06-09: Modelle produzieren weiterhin CoT trotz `enable_thinking: false`)
- Inline-CoT über Response-Länge war verboten (False-Positives bei Instruction-Following)

**Lösung ab v4.7.x:** Empirische Probe mit Card-Persistierung + optionaler Override-Escape-Hatch.

---

## Drei-Signal-Hierarchie

Die Probe wertet drei Signale aus, in absteigender Confidence:

| Signal | Quelle | Confidence | Beispiel |
|---|---|---|---|
| **A — Tags** | Bekannte Think-Tags im Response-Content | `high` | `<think>…</think>` |
| **B — reasoning_tokens** | Provider-API-Metadaten (`reasoning_tokens > 0` **und** Output nicht leer) | `medium` | Kimi K2 Thinking: 4503 Tokens |
| **C — Inline-CoT** | Heuristik im Content (Länge + Berechnungs-Operatoren) | `medium` | Qwen 3 14B Decision: 4619 chars |

**Befund aus Discovery (9 Modelle, 27 Probes, 2026-06-09):**
- Signal A hat sich als **wenig zuverlässig** erwiesen (llama.cpp strippt Tags bei `enable_thinking: false`, OpenRouter strippt Tags aus dem Content)
- Signal B war initial **nur bei OpenRouter** verfügbar (OpenAI-kompatible Metadaten) — **ab v4.10.1 wird Signal B in allen Provider-Connectors extrahiert**: `reasoning_tokens` aus `usage.completion_tokens_details.reasoning_tokens` (OpenAI/Mistral/OpenRouter/Groq/xAI), `usage.output_tokens_details.reasoning_tokens` (Anthropic), `usage_metadata.thoughts_token_count` (Google), `eval_count` (Ollama bei Thinking-Modellen).
- Signal C ist die **einzige robuste Erkennung** über alle Provider hinweg

→ Inline-CoT ist der primäre Trigger, Tags/Metadaten sind Verstärkung.

**Provider-Extraktion (ab v4.10.1):** Alle Provider-Connectors in `utils/providers/` speichern `reasoning_tokens` und `think_content` in `last_response_metadata`. Konsumenten: `judge_evaluator.py` (Thinking-Aufwand pro Aufgabe), `base_runner.py` (Reasoning-Budget-Entscheidung), `benchmark_utils.py` (Audit-Log mit Reasoning-Token-Block). Siehe `docs/ARCHITECTURE.md` → "Provider Thinking/Reasoning-Extraktion" für die vollständige Mapping-Tabelle.

---

## Multi-Prompt-Aggregation

`probe_thinking_model(prompts=None)` sendet **3 Probe-Prompts** (math/code/decision), um zu vermeiden, dass Familien falsch klassifiziert werden, die CoT nur in bestimmten Domänen zeigen:

```python
_PROBE_PROMPTS: dict[str, str] = {
    "math":     "Solve step by step: A train travels 120 km in 1.5 hours. What is its average speed in km/h? Show your reasoning.",
    "code":     "Sort this list step by step and explain your algorithm: [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]",
    "decision": "Should an autonomous car swerve to avoid a pedestrian even if it risks the passenger's life? Think through the ethical considerations before answering.",
}
```

**Aggregation:** Höchste Confidence gewinnt. Wenn irgendein Prompt `detected=True` liefert, ist das Gesamtergebnis `detected=True` mit kombinierter Evidence. Bei `prompts=None` (Default) werden alle 3 Prompts gesendet; Single-Prompt-Modus (1 Eintrag) bleibt für Card-First-Hook erhalten.

**Begründung:** Manche Familien zeigen CoT nur bei ethischen/Decision-Fragen, andere nur bei Code-Reasoning, wieder andere nur bei Mathematik. Drei Domänen = robuste Familien-Klassifikation.

---

## Bekannte Think-Tags

SSoT: `_THINK_TAGS` in `utils/model_utils.py` (13 Tags, ab v4.7.2):

```python
_THINK_TAGS = (
    '<think>', '<thinking>', '<thought>',          # Qwen 3, Magistral, GLM
    '<|thinking|>', '<|reasoning|>',                # OpenAI OSS / gpt-oss
    '<reasoning>', '<reason>',                      # DeepSeek R1 / V3
    '<reflection>',                                  # Meta Llama 4
    '<analysis>', '<plan>',                         # Anthropic Extended Thinking
    '<scratchpad>',                                  # NousResearch Hermes
    '<solution>',                                    # Mistral Reasoning
    '<cot>',                                         # Custom / Future
)
```

`_find_think_tags(text) -> list[str]` gibt alle gefundenen Tags zurück (lowercase, Multi-Tag-aware).

**Bei neu entdeckten Tags:** `_THINK_TAGS` ergänzen + Test in `test_thinking_probe_families.py`.

---

## Inline-CoT-Heuristik (Signal C)

**Konfiguration (`utils/model_utils.py`):**

```python
_INLINE_COT_LENGTH_THRESHOLD = 200   # chars
_INLINE_COT_MIN_OPS = 2              # Berechnungs-Operatoren (math/code)
```

**Triggert, wenn Antwort:**

1. `len(content) > 200` UND
2. Mindestens 2 der folgenden Operatoren/Tokens im Text: `=`, `+`, `-`, `*`, `/`, `step`, `then`, `because`, `therefore`, `thus`, `first`, `next`, `finally`, `algorithm`, `complexity`

**Heuristik-Begründung:** Alle 9 Discovery-Modelle zeigten 400-4619 chars Chain-of-Thought. Schwelle 200 chars + ≥2 Ops verhindert False-Positives bei kurzen, direkten Antworten (z. B. "80 km/h").

**Vor v3.5.8 war die Heuristik Response-Länge-basiert allein** — das verursachte False-Positives bei Instruction-Following-Modellen, die auf Reasoning-Prompts ebenfalls lange Antworten produzieren. Ab v3.5.8 wurde Length-Signal gestrichen. Inline-CoT wurde in v4.7.x als **legitimes** Signal C rehabilitiert, weil es mit Operator-Token-Kombination deutlich präziser ist.

---

## SSoT-Auflösung: Card + Override (ab v4.7.1)

**Architektur (Option C):** Die Thinking-Probe ist die **Single Source of Truth** (SSoT). Ein optionaler `thinking_override` in der Provider-Card ist ein expliziter Escape-Hatch mit Pflicht-Begründung und optionalem Expiry-Datum.

### Auflösungs-Priorität

```python
def resolve_effective_thinking(
    model_card: dict,
    provider_model_cfg: dict | None = None,
    *,
    model_id: str | None = None,
    now: datetime | None = None,
) -> tuple[bool | None, str]:
    # 1. aktiver thinking_override?  → (override_value, "override")
    # 2. Card thinking_probe_detected? → (card_value, "card_probe")
    # 3. nichts                       → (None, "none")
```

### Override-Schema (in `config/card_template_vendor.yaml`)

```yaml
providers:
  commercial:
    openai:
      models:
      - id: gpt-5.4-mini
        name: GPT-5.4 Mini
        # Opt-in Escape-Hatch (Pflicht: reason; Optional: active_until)
        thinking_override:
          value: false
          reason: "Cost-Benchmark: CoT-Suppression fuer faire Speed-Vergleiche"
          active_until: "2026-12-31"   # ISO-8601, Auto-Expiry
```

**Schnittstelle:** `utils/model_utils._is_override_active(override, now=None)` validiert das Schema und prüft `active_until` gegen den aktuellen Zeitpunkt.

---

## Override-Aktivierungs-Regeln

| Bedingung | Anforderung |
|---|---|
| `value` | muss `true` oder `false` sein (bool, Pflicht) |
| `reason` | Pflicht (Whitespace-only zählt als leer) |
| `active_until` | Optional, ISO-8601; muss in der Zukunft liegen, naive wird UTC interpretiert |
| Bei Inaktivität | Card-Probe gewinnt automatisch |

**Audit-Trail:** Jede Override-Anwendung wird geloggt: `[ThinkingOverride] model_id: override active (value=…, reason=…)`.

**Auto-Expiry:** `active_until` verhindert ewige Drift zwischen Card und Config — nach Ablauf greift automatisch die Card-Probe.

---

## Runner-Consumer-Anbindung (ab v4.7.1)

`base_runner.py` reicht den Provider an `resolve_token_budget()` durch, damit ein aktiver `thinking_override` das Token-Budget beeinflusst:

```python
# utils/base_runner.py:121
_token_budget, _ = resolve_token_budget(
    model, _raw_budget, self.validator.config, _module_key,
    provider=provider,   # ab v4.7.1
)
```

**Auflösungs-Pfad in `resolve_token_budget()`:**

1. `provider=None` (Backward-Compat) → `is_reasoning_model()` mit Trigger-Fallback
2. `provider="..."` → `load_vendor_card()` → `resolve_effective_thinking()` mit Override + Card-Probe
3. Override aktiv → Override-Wert gewinnt
4. Card-Probe gesetzt → Probe-Wert gewinnt
5. Keine Info → Trigger-Liste

**Effekt:**

| Szenario | Token-Budget-Verhalten |
|---|---|
| `thinking_override.value: false` aktiv | **KEIN** 5× Reasoning-Multiplikator (Cost-Benchmark-fair) |
| `thinking_override.value: true` auf Non-Reasoning-Modell | 5× Multiplikator (A/B-Test) |
| Card-Probe `false` trotz magistral-Trigger | **KEIN** 5× (Card-First) |
| Card fehlt, Provider ohne Override | Trigger-Liste (Backward-Compat) |

**Backward-Compat:** 5 alte Call-Sites (mistral.py, openrouter.py, openai.py, llamacpp_base.py) ohne `provider`-Argument funktionieren unverändert.

---

## Discovery-Inventar

`scripts/tools/discover_thinking_tags.py` führt **read-only Discovery** durch — keine Card-Updates. Pro Lauf:

- Pro Familie wird 1 Repräsentant ausgewählt (Priorität: lokal > openrouter > cloud; Thinking-Modelle bevorzugt)
- 3 Probe-Prompts pro Modell, aggregierte Ergebnisse
- Output: `docs/THINKING_TAGS_INVENTORY.md` mit Tabellen, Cross-Family-Statistik, Roh-Antworten (gekürzt)

**Bisherige Läufe (2026-06-09):**

| Welle | Modelle | Familien | Bevorzugter Signal-Typ |
|---|---|---|---|
| M4 (MacBook Pro) | 4 | Gemma, Hermes, Qwen, Qwen-Coder | Inline CoT (alle) |
| Spark (DGX) | 2 | Gemma 4 26B-A4B, Hermes 4.3 36B | Inline CoT (alle) |
| Cloud (OpenRouter) | 3 | DeepSeek, Kimi, NVIDIA | Mixed (Inline CoT + reasoning_tokens) |

**Erkennungsrate 9/9 (100%)** — keine Probe fehlgeschlagen. Detail-Tabellen: `docs/THINKING_TAGS_INVENTORY_M4.md`, `_SPARK.md`, `_CLOUD.md`.

**Empfohlene Folge-Discovery-Läufe:**

- DeepSeek V4 Pro / R1 (sollte `<reasoning>` Tags zeigen)
- GLM 5 (sollte `<think>` Tags zeigen)
- GPT-OSS 120B via Groq (`<|reasoning|>` Tags erwartet)
- Qwen 3.5 397B-A17B (größtes Qwen, möglicherweise andere Patterns)
- Magistral Medium via Mistral API (sollte `<think>` Tags zeigen)
- llama.cpp lokal mit `--reasoning on` (würde explizite Tags provozieren)

---

## Offene Folgearbeiten

| Aufgabe | Status | Bemerkung |
|---|---|---|
| Modul-spezifische Reasoning-Slots (Option C) | offen | `reasoning_logic`, `code_quality`, `political_compass` mit Reasoning-Markierung |
| Probe-Logik-Hierarchie in `model_utils.py` docstring präzisieren | offen | Inline-CoT als primärer Trigger dokumentieren |
| Card-Felder `cot_marker_family` / `cot_tags_detected` | offen | feinere Granularität jenseits `thinking_probe_detected` boolean |
| Folge-Discovery für neue Modell-Familien | optional | siehe Liste oben |

**Tests:**

- `tests/test_thinking_probe_families.py` — 59 Tests (Multi-Prompt-Aggregation, _THINK_TAGS, _find_think_tags, identify_family, pick_representatives, aggregate_probe)
- `tests/test_thinking_probe_inline_cot.py` — 13 Tests (Signal-C-Heuristik + Signal-B Cold-Start-Guard)
- `tests/test_thinking_override.py` — 24 Tests (SSoT-Auflösungsmatrix, Override-Validierung, Audit-Trail)
- `tests/test_base_runner_thinking_budget.py` — 17 Tests (Runner-Consumer-Anbindung mit SSoT-Pfad)

**Gesamt-Suite:** 634/634 Tests grün (Stand 2026-06-10).
