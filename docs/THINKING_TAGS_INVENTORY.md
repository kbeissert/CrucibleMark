# Thinking-Tag-Inventar pro Modell-Familie

Automatisch generiert via `scripts/tools/discover_thinking_tags.py` — **read-only Discovery**, keine Card-Updates.

**Konsolidiert aus 3 Discovery-Wellen:**

- **M4 (MacBook Pro):** `docs/THINKING_TAGS_INVENTORY_M4.md` — 4 Modelle, Gemma/Hermes/Qwen/Qwen-Coder
- **Spark (DGX):** `docs/THINKING_TAGS_INVENTORY_SPARK.md` — 2 Modelle, Gemma 4 26B-A4B + Hermes 4.3 36B (Hybrid-Mode)
- **Cloud (OpenRouter):** `docs/THINKING_TAGS_INVENTORY_CLOUD.md` — 3 Modelle, DeepSeek/Kimi/NVIDIA

**Gesamt:** 9 Modelle, 27 Probes (3 Prompts × 9 Modelle), 0 Fehler.

**Lauf-Zeit:** ~12 min (M4: 4 min, Spark: 4 min, Cloud: 3 min, inkl. Server-Cold-Starts)

## Methodik

Pro Modell werden 3 Probe-Prompts gesendet:
- **math**: `Solve step by step: A train travels 120 km in 1.5 hours. What is its average speed in km/h? Show your reasoning.`
- **code**: `Sort this list step by step and explain your algorithm: [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]`
- **decision**: `Should an autonomous car swerve to avoid a pedestrian even if it risks the passenger's life? Think through the ethical considerations before answering.`

**Signal-Hierarchie** (Confidence):
- **high**: Bekannte Think-Tags in Antwort (`<think>`, `<|thinking|>`, `<reflection>`, ...)
- **medium**: `reasoning_tokens > 0` in Provider-Metadaten ODER Inline-CoT im content-Feld
- **low**: Kein Signal

**Aktuell bekannte Tag-Liste** (SSoT: `utils/model_utils._THINK_TAGS`):

```python
_THINK_TAGS = ['<think>', '<thinking>', '<thought>', '<|thinking|>', '<|reasoning|>', '<reasoning>', '<reason>', '<reflection>', '<analysis>', '<plan>', '<scratchpad>', '<solution>', '<cot>']
```

## Zentrale Befunde

1. **Kein einziges der 9 getesteten Modelle produziert explizite Think-Tags** im sichtbaren Content. Mögliche Ursachen:
   - llama.cpp-Modelle werden mit `enable_thinking: false` gestartet (Default `--reasoning off`)
   - OpenRouter strippt Reasoning-Tags aus dem Content (liefert nur `reasoning_tokens` Metadaten)
   - Bei DeepSeek V3.1 ist `reasoning_tokens=0` — V3.1 nutzt das alte Format ohne Reasoning-Tokens-Metadaten

2. **`reasoning_tokens` Metadaten funktionieren** für NVIDIA Nemotron 3 Ultra (46-444 Tokens) und Kimi K2 Thinking (355-4503 Tokens). Das ist **Signal B** in Aktion — auch wenn Tags fehlen, zeigt die Metrik, dass das Modell intern Reasoning betreibt.

3. **Inline-CoT (Signal C) funktioniert universell** — alle 9 Modelle produzieren Chain-of-Thought direkt im Content (Antworten 400-4619 chars, je nach Modell und Prompt). Heuristik: Antwort >200 chars + mind. 2 Berechnungs-Operatoren triggert.

4. **Konsequenz für die Probe-Logik:**
   - Signal A (Tags) hat sich als **wenig zuverlässig** erwiesen bei `enable_thinking: false` Konfiguration
   - Signal B (reasoning_tokens) ist **nur bei OpenRouter** verfügbar (OpenAI-kompatible Metadaten)
   - Signal C (Inline-CoT) ist die **einzige robuste Erkennung** über alle Provider hinweg — Heuristik kombiniert Response-Länge (>200 Zeichen) UND Operator-Dichte (≥2 Berechnungs-Operatoren), um reine Längen-False-Positives bei Instruction-Following-Modellen zu vermeiden (siehe `utils/model_utils._has_inline_cot`)
   - Empfehlung: Inline-CoT als primärer Trigger für `thinking_probe_detected` verwenden, Tags/Metadaten als Verstärkung

> **Wichtig (ab v4.10.1):** Reine Response-Länge ist KEIN CoT-Signal — die Inline-CoT-Heuristik kombiniert Länge mit Operator-Dichte. Das aktuelle Probe-Verfahren in `_has_inline_cot()` nutzt diese kombinierte Heuristik (`_INLINE_COT_LENGTH_THRESHOLD = 200` + `_INLINE_COT_MIN_OPS = 2` Berechnungs-Operatoren).

## Konsolidierte Pro-Ergebnis-Tabelle

| Familie | Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|---|
| Gemma | gemma-3-12b-it | llamacpp (M4) | ✅ | medium | Inline CoT (math, code, decision) | - |
| Hermes | hermes-3-8b | llamacpp (M4) | ✅ | medium | Inline CoT (math) | - |
| Qwen-Coder | qwen2.5-coder-7b | llamacpp (M4) | ✅ | medium | Inline CoT (math, code, decision) | - |
| Qwen | qwen3-14b | llamacpp (M4) | ✅ | medium | Inline CoT (math, code, decision) | - |
| Gemma | gemma-4-26b-a4b-q8 | llamacpp_spark | ✅ | medium | Inline CoT (math, code, decision) | - |
| Hermes | hermes-4.3-36b-q6 | llamacpp_spark | ✅ | medium | Inline CoT (math) | - |
| DeepSeek | deepseek-chat-v3.1 | openrouter | ✅ | medium | Inline CoT (math, code, decision) | - |
| Kimi | kimi-k2-thinking-20251106 | openrouter | ✅ | medium | reasoning_tokens=4503 | - |
| NVIDIA | nemotron-3-ultra-550b-a55b | openrouter | ✅ | medium | reasoning_tokens=444 | - |

**Erkennungsrate: 9/9 (100%)** — keine Fehler.

## Roh-Antworten (gekuerzt auf 300 chars/Prompt)

<details>
<summary>M4 — Gemma 3 12B Instruct (518-2568 chars pro Prompt)</summary>

### math (518 chars, tags=[], reasoning_t=0, inline_cot=True)
> Here's how to solve the problem step-by-step: **1. Understand the Concept of Average Speed** * Average speed is calculated by dividing the total distance traveled by the total time taken. * Formula: Average Speed = Total Distance / Total Time **2. Identify the Given Information** * Total Distance = 120 km * Total Time = 1.5 hours ...

### code (1086 chars)
> Okay, let's sort the list `[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]` using the **Bubble Sort** algorithm. I'll explain each step. **1. Understanding Bubble Sort** ...

### decision (2568 chars)
> Okay, let's break down this incredibly complex ethical dilemma. The question of whether an autonomous car should swerve to avoid a pedestrian, even at the risk of the passenger's life, is a cornerstone of the ethical debate surrounding self-driving vehicles ...
</details>

<details>
<summary>M4 — Hermes 3 8B (400-1795 chars)</summary>

### math (400 chars)
> To find the average speed of the train, we need to divide the total distance traveled by the total time taken. Given: - Distance traveled = 120 km - Time taken = 1.5 hours Average speed = Distance ÷ Time Step 1: Substitute the given values into the formula. Average speed = 120 km ÷ 1.5 hours ...

### code (1048 chars)
> To sort the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] using the Bubble Sort algorithm, we will repeatedly compare adjacent elements ...

### decision (1795 chars)
> This is a complex moral dilemma that highlights the "trolley problem" in the context of autonomous vehicles ...
</details>

<details>
<summary>M4 — Qwen 2.5 Coder 7B (552-2589 chars)</summary>

### math (552 chars)
> To find the average speed of the train, we can use the formula: Average Speed = Total Distance / Total Time Given: - Total Distance = 120 km - Total Time = 1.5 hours Now, let's plug these values into the formula ...

### code (975 chars)
> Sure, I'll sort the list using the Bubble Sort algorithm, which is a simple sorting algorithm that repeatedly steps through the list, compares adjacent elements, and swaps them if they are in the wrong order ...

### decision (2589 chars)
> The question of whether an autonomous car should swerve to avoid a pedestrian, even if it risks the passenger's life, is a complex ethical dilemma that involves balancing various factors. Here are some key considerations: 1. **Safety and Responsibility** ...
</details>

<details>
<summary>M4 — Qwen 3 14B (578-4619 chars)</summary>

### math (578 chars)
> To find the **average speed** of the train, we use the formula: Average Speed = Total Distance / Total Time ### Step 1: Identify the given values - Total Distance = 120 km - Total Time = 1.5 hours ### Step 2: Plug the values into the formula ...

### code (1872 chars)
> Sure! Let's walk through the process of **sorting** the list: ### Original List: ``` [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] ``` ## Step 1: Choose a Sorting Algorithm We'll use the **Bubble Sort** algorithm for this explanation ...

### decision (4619 chars) — die längste Antwort im ganzen Lauf
> The question of whether an autonomous car should swerve to avoid a pedestrian even if it risks the passenger's life is a deeply complex ethical dilemma that involves multiple philosophical, legal, and societal considerations. Here's a structured analysis of the key ethical considerations involved ...
</details>

<details>
<summary>Spark — Gemma 4 26B-A4B (949-2465 chars)</summary>

### math (949 chars)
> To find the average speed of the train, follow these steps: ### 1. Identify the given information From the problem, we know: * **Total Distance ($d$):** $120\text{ km}$ * **Total Time ($t$):** $1.5\text{ hours}$ ### 2. State the formula ...

### code (1268 chars)
> To sort this list, I will use the **Bubble Sort** algorithm. ### The Algorithm: Bubble Sort **How it works:** Bubble Sort works by repeatedly stepping through the list, comparing adjacent elements, and swapping them if they are in the wrong order ...

### decision (2465 chars)
> The question of whether an autonomous vehicle (AV) should prioritize the lives of its passengers or pedestrians is a modern iteration of the "Trolley Problem," a classic thought experiment in ethics ...
</details>

<details>
<summary>Spark — Hermes 4.3 36B (439-1068 chars, Hybrid-Mode mit --ctx-size 16384)</summary>

### math (439 chars)
> To find the average speed of the train, we need to divide the distance traveled by the time taken. Given: - Distance traveled: 120 km - Time taken: 1.5 hours Step 1: Set up the equation for average speed. Average speed = Distance ÷ Time ...

### code (1068 chars)
> To sort the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] using the Bubble Sort algorithm, we will repeatedly compare adjacent elements and swap them if they are in the wrong order ...

### decision (1058 chars)
> This is a complex ethical dilemma with no easy answer. Some key considerations: - Autonomous cars could potentially save many lives overall compared to human drivers, but this specific scenario pits one life against another ...
</details>

<details>
<summary>Cloud — DeepSeek V3.1 (666-2412 chars, reasoning_tokens=0)</summary>

### math (666 chars)
> Alright, let's go step-by-step. --- **Step 1: Identify the given values** - Distance traveled: 120 km - Time taken: 1.5 hours --- **Step 2: Recall the formula for average speed** Average speed = Total distance / Total time ...

### code (1306 chars)
> Let's sort the list step by step using the **Insertion Sort** algorithm. Insertion Sort works by building a sorted portion of the list and inserting each unsorted element into its correct position in the sorted part ...

### decision (2412 chars)
> This is one of the core ethical dilemmas in autonomous vehicle (AV) programming, often called the "trolley problem" in modern form ...
</details>

<details>
<summary>Cloud — Kimi K2 Thinking (652-2547 chars, reasoning_tokens=355-4503!)</summary>

### math (652 chars, reasoning_t=355)
> Here is the step-by-step solution: **Step 1: Identify the formula for average speed.** Average speed is calculated by dividing the total distance traveled by the total time taken. Average Speed = Total Distance / Total Time ...

### code (2547 chars, reasoning_t=4503 — Maximum des ganzen Laufs!)
> I'll sort this list using **Insertion Sort**, which is intuitive like sorting playing cards in your hand. Here's the step-by-step process: ### Algorithm Explanation Insertion Sort builds a sorted portion from left to right ...

### decision (2361 chars, reasoning_t=806)
> This is one of the most challenging ethical questions in autonomous vehicle design, with no consensus answer. Here are the key considerations: **Core Ethical Tensions:** 1. **Utilitarian vs. Deontological Ethics**: A utilitarian approach would minimize total lives lost ...
</details>

<details>
<summary>Cloud — NVIDIA Nemotron 3 Ultra (746-792 chars, reasoning_tokens=46-444)</summary>

### math (746 chars, reasoning_t=46)
> **Step 1: Identify the formula for average speed.** The formula for average speed is: Average Speed = Total Distance / Total Time **Step 2: Identify the given values.** * Total Distance = 120 km * Total Time = 1.5 hours ...

### code (770 chars, reasoning_t=265)
> I will use the **Merge Sort** algorithm. It is a classic "Divide and Conquer" algorithm that is stable, efficient ($O(n \log n)$), and very intuitive to visualize step-by-step. --- ### **Algorithm: Merge Sort** **Core Concept:** 1. **Divide:** Recursively split the list in half ...

### decision (792 chars, reasoning_t=444 — Maximalwert)
> This is the central dilemma of algorithmic ethics in transportation, often framed as a modern "trolley problem." There is no universal consensus, but the ethical landscape can be mapped through several competing frameworks. **Utilitarianism (Consequentialism)** From a strict utilitarian view ...
</details>

## Cross-Family-Statistik (konsolidiert)

| Familie | Modelle | Thinking erkannt | Anteil | Bevorzugter Signal-Typ |
|---|---|---|---|---|
| Gemma | 2 | 2 | 100% | Inline CoT |
| Hermes | 2 | 2 | 100% | Inline CoT |
| Qwen | 1 | 1 | 100% | Inline CoT |
| Qwen-Coder | 1 | 1 | 100% | Inline CoT |
| DeepSeek | 1 | 1 | 100% | Inline CoT |
| Kimi | 1 | 1 | 100% | reasoning_tokens |
| NVIDIA | 1 | 1 | 100% | reasoning_tokens |
| **Total** | **9** | **9** | **100%** | Mixed |

## Empfehlungen

1. **Probe-Logik-Hierarchie beibehalten:** Signal A (Tags) → Signal B (reasoning_tokens) → Signal C (Inline-CoT). Tags sind primäres Signal wenn vorhanden, aber die Heuristik muss funktionieren auch wenn Tags fehlen.

2. **Inline-CoT-Schwelle evtl. anpassen:** Aktuell 200 chars + 2 Ops. Qwen 3 14B produzierte 4619 chars bei decision — Heuristik triggert. Gemma 3 12B produzierte 518-2568 chars — auch Trigger. Aber: kurze, direkte Antworten (z.B. "80 km/h") sollen KEIN False-Positive sein. Aktuelle Schwelle ist OK.

3. **OpenRouter-Spezialfall:** `reasoning_tokens` ist ein wertvolles sekundäres Signal, aber nur bei manchen Modellen verfügbar. Probe sollte es als "Booster" für Confidence nutzen, nicht als Hard-Fail.

4. **DeepSeek V3.1** zeigte `reasoning_tokens=0` — entweder das Modell nutzt das nicht (V3.1 ist eine reguläre LLM-Variante, nicht R1), oder OpenRouter liefert es nicht für V3.1. Bei V4 / R1 wäre das anders zu erwarten.

5. **Weitere Discovery-Läufe sinnvoll für:**
   - DeepSeek V4 Pro / R1 (sollte `<reasoning>` Tags zeigen)
   - GLM 5 (sollte `<think>` Tags zeigen)
   - Qwen 3.5 397B (größtes Qwen, möglicherweise andere Patterns)
   - GPT-OSS 120B via Groq (`<|reasoning|>` Tags erwartet)
   - Magistral Medium via Mistral API (sollte `<think>` Tags zeigen)

**Status:** Aktuelle Probe-Infrastruktur funktioniert zuverlässig. Discovery-Wellen M4 + Spark + Cloud (9 Modelle) zeigen universell Inline-CoT; Tags sind nirgendwo sichtbar (Provider-stripped oder `--reasoning off`).

---

## SSoT-Auflösung: Card + Override (ab v4.7.1)

**Architektur (Option C):** Die Thinking-Probe ist die **Single Source of Truth** (SSoT). Ein optionaler `thinking_override` in `config/provider_config.yaml` ist ein expliziter Escape-Hatch mit Pflicht-Begründung und optionalem Expiry-Datum.

### Auflösungs-Priorität

```
resolve_effective_thinking(model_card, provider_model_cfg)
  → 1. aktiver thinking_override?  → (override_value, "override")
  → 2. Card thinking_probe_detected? → (card_value, "card_probe")
  → 3. nichts                       → (None, "none")
```

### Override-Schema (in `config/provider_config.yaml`)

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

**Aktivierungs-Regeln** (in `utils/model_utils._is_override_active()`):
- `value` muss `true` oder `false` sein (bool, Pflicht)
- `reason` ist Pflicht (Whitespace-only zählt als leer)
- `active_until` (optional): wenn gesetzt, muss in der Zukunft liegen
- Bei Inaktivität: Card-Probe gewinnt automatisch

### Begründung

- **Discovery-Fund:** `enable_thinking: false` ist empirisch unzuverlässig (Inline-CoT wird trotzdem produziert). Config-Override nur als **expliziter** A/B-Use-Case, nicht als Default.
- **Card-First-Property:** Probe-Ergebnisse sind empirisch robust (9/9 Modelle erkannt). Card ist SSoT.
- **Audit-Trail:** Jede Override-Anwendung wird geloggt: `[ThinkingOverride] model_id: override active (value=…, reason=…)`.
- **Auto-Expiry:** `active_until` verhindert ewige Drift zwischen Card und Config.

### Use-Cases

| Szenario | Empfehlung |
|---|---|
| Standard-Benchmark | Card-Probe (kein Override) |
| Cost-Benchmark (CoT aus, fairer Speed-Vergleich) | Override `value: false` mit `reason` + `active_until` |
| A/B-Test Thinking vs. Non-Thinking | Override + verschiedene `active_until`-Daten |
| Provider-API hat eigene reasoning-Steuerung | Override als Brücke, bis Probe automatisch erkennt |
| Alte Probe-Daten (z.B. >30 Tage) | Re-Probe via `make probe-thinking MODEL=…` |

### Konsumenten

- `scripts/tools/probe_thinking.py` schreibt Card-Felder
- `utils/model_utils.resolve_effective_thinking()` löst effektives Flag auf
- Geplant: `utils/base_runner.py` für Token-Budget-Anpassung (Reasoning-Modelle)
- Geplant: `benchmark_modules/*/test.py` für modul-spezifische Reasoning-Slots

**Tests:** `tests/test_thinking_override.py` (24 Tests inkl. SSoT-Auflösungsmatrix).
**Card-Felder:** `thinking_probe_detected`, `thinking_probe_evidence`, `thinking_probe_confidence`, `thinking_probe_at` (Pflicht); `cot_marker_family`, `cot_tags_detected` (Optional, ab v4.7.1).
**Provider-Config:** `thinking_override` (Optional, ab v4.7.1).
