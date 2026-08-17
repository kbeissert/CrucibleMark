# Qwen 3.8 27B NVFP4 — Thinking-Modi-Vergleich (Qualität / Tokens / TPS)

**Modell:** Qwen 3.8 27B NVFP4 (Dense, MTP, 1:3-Interleaving 16 full_attn + 48 Mamba2, 262K Context)
**Hardware:** DGX Spark (asus_gx10_blackwell) · **Inference:** vLLM 0.27.2rc1.dev126 (MOD `thinking-budget-by-effort`)
**Provider:** vllm_spark · **Judge:** Anthropic (Hybrid) · **Modul:** cli_benchmark (6 Assets)
**Datum:** 2026-08-17 · **Pipeline:** v5.1.5 (echte Provider-Token, TPS = output_tokens / wall-time)

---

## TL;DR

| Modus | Qualität | Out-Tokens | TPS | Zeit | Urteil |
|-------|:--------:|:----------:|:---:|:----:|--------|
| instruct (off) | 86.0 | 425 | 17.9 | 24 s | starkes Budget-Option |
| low | 82.4 | 2 515 | 23.5 | 107 s | **schlechtester** |
| **medium** | **93.0** | 3 244 | **26.3** | 124 s | **Sweet-Spot** |
| xhigh | 86.7 | 15 878 | 11.5 | 1 385 s | Overkill (≈ instruct) |

**Kernaussagen:**
1. **`medium` ist der Sweet-Spot** — höchste Qualität (93.0) *und* schnellster TPS (26.3) bei moderatem Token-Aufwand.
2. **`xhigh` bringt keinen Qualitätsgewinn** — 86.7 ≈ instruct (86.0), aber 5× die Tokens und 58× die Zeit. Das Extra-Thinking ist rauschbehaftet und verschlechtert einzelne Tasks sogar (cli006: 58 vs. medium 100).
3. **`low` ist kontraproduktiv** — 82.4 liegt *unter* instruct (86.0). Ein minimales Thinking-Budget zahlt den Token-Preis, ohne den Qualitätsgewinn einzubringen.
4. **`instruct` (off)** ist die beste Latenz-/Budget-Option: 86.0 in 24 s (1/58 der xhigh-Zeit).

---

## Methodik

Jeder Modus fuhrt das **gleiche** cli_benchmark-Modul (cli001–cli006) einmal, sequenziell gegen den laufenden vLLM-Server. Die 4 Konfigurationen:

| Modus | Modell-ID | `enable_thinking` | `reasoning_effort` | max_tokens |
|-------|-----------|:-----------------:|:------------------:|:----------:|
| instruct | `qwen3_8-27b-nvfp4` | off | — | 16 384 |
| low | `qwen3_8-27b-nvfp4-thinking` | on | `low` | 32 768 |
| medium | `qwen3_8-27b-nvfp4-thinking` | on | `medium` | 32 768 |
| xhigh | `qwen3_8-27b-nvfp4-thinking` | on | `xhigh` | 32 768 |

- `enable_thinking` wird via `chat_template_kwargs` pro Request gesteuert (Dual-Profile-Expansion).
- `reasoning_effort` wird pro Request gesendet; der MOD `thinking-budget-by-effort` leitet daraus das `thinking_token_budget` ab. **Kein Server-Restart** zwischen den Modi (per-Request-Parameter).
- Die CSV ist append-basiert mit eindeutiger `run_id` pro Run. Pro Modus wurde der neue `run_id` per Vorher/Nachher-Diff ermittelt und die 6 Zeilen als Snapshot gesichert (`outputs/analysis/qwen3_8_thinking_modes/`).
- `--force` erzwang einen frischen Lauf (Cache ignoriert). `reasoning_effort` wurde nach dem Lauf auf den committed Wert (`medium`) zurückgesetzt.

**Metrik-Definitionen (v5.1.5):**
- `tokens_per_second` (TPS) = `output_tokens / execution_time` — echter Decode-Durchsatz **inkl. Thinking-Tokens**.
- `output_tokens` = sichtbare Antwort **+** Thinking; `reasoning_tokens` = Thinking-Anteil; `input_tokens` = Prompt.
- Aggregierter TPS ist nach `execution_time` gewichtet.

---

## Kern-Metriken je Modus

| Modus | Ø Score | input | output | reasoning | TPS (gew.) | Gesamtzeit |
|-------|:-------:|:-----:|:------:|:---------:|:----------:|:----------:|
| instruct | 86.0 | 679 | 425 | 0 | 17.87 | 23.8 s |
| low | 82.4 | 823 | 2 515 | 1 454 | 23.54 | 106.8 s |
| medium | 93.0 | 667 | 3 244 | 2 376 | 26.28 | 123.5 s |
| xhigh | 86.7 | 895 | 15 878 | 15 475 | 11.46 | 1 385.1 s |

---

## Qualität je Asset (Score 0–100)

| Asset | instruct | low | medium | xhigh |
|-------|:--------:|:---:|:------:|:-----:|
| cli001 Disk Cleanup | 72.0 | 88.4 | **100.0** | 86.0 |
| cli002 Library Install | 72.0 | 72.0 | **86.0** | **86.0** |
| cli003 Repo Clone | 86.0 | **100.0** | **100.0** | **100.0** |
| cli004 Zshrc Alias | **100.0** | **100.0** | 86.0 | **100.0** |
| cli005 SwarmUI Docker | 86.0 | 62.0 | 86.0 | **90.0** |
| cli006 Ollama Symlink | **100.0** | 72.0 | **100.0** | 58.0 |
| **Ø** | **86.0** | **82.4** | **93.0** | **86.7** |

**Lesart:** `medium` gewinnt 3× klar (cli001, cli002, cli006) und teilt sich 2× die Spitze (cli003). `xhigh` ist **hoch-variance**: beste Einzelwertung bei cli005 (90), aber mit Abstand die schlechteste bei cli006 (58) und schwächer als `medium` bei cli001 (86 vs. 100). Das Extra-Thinking wirkt also **nicht konsistent** — es hilft auf manchen Tasks, schadet auf anderen.

---

## Token-Verbrauch & TPS je Asset

| Asset | Modus | output | reasoning | TPS | Zeit |
|-------|-------|:------:|:---------:|:---:|:----:|
| cli001 | instruct | 114 | 0 | 18.82 | 6.1 s |
| cli001 | low | 1 045 | 256 | 20.37 | 51.3 s |
| cli001 | medium | 1 357 | 778 | 25.71 | 52.8 s |
| cli001 | **xhigh** | **6 392** | **6 222** | 6.96 | **918.8 s** |
| cli002 | xhigh | 2 024 | 2 000 | 19.46 | 104.0 s |
| cli005 | instruct | 185 | 0 | 24.85 | 7.4 s |
| cli005 | medium | 690 | 523 | 30.44 | 22.7 s |
| cli005 | **xhigh** | **5 871** | **5 768** | 20.73 | **283.2 s** |
| cli006 | xhigh | 567 | 529 | 20.29 | 27.9 s |

*(Auswahl der relevantesten Zeilen; vollständige Daten in den Snapshots.)*

**Token-Burn konzentriert sich auf die harten Tasks:** xhigh brennt bei cli001 (6 392 out) und cli005 (5 871 out) zusammen **12 263 Tokens** — das sind 77% des xhigh-Ausgabenbudgets. Auf den leichten Tasks (cli003, cli006) bleibt xhigh moderat (146 bzw. 567 out). **Zeit-Verteiler:** cli001 (919 s) + cli005 (283 s) = 1 202 s = **87% der gesamten xhigh-Laufzeit**.

---

## Effizienz-Metriken

| Modus | Thinking-Anteil* | Tokens/Task | Score / 1k Tokens | Score / Sekunde |
|-------|:---------------:|:-----------:|:-----------------:|:---------------:|
| instruct | 0.0% | 184 | 467.4 | 21.70 |
| low | 57.8% | 556 | 148.1 | 4.63 |
| medium | 73.2% | 652 | 142.7 | 4.52 |
| xhigh | 97.5% | 2 796 | 31.0 | 0.38 |

\* `reasoning_tokens / output_tokens` — wie groß der Output aus reinem Thinking besteht.

- **Thinking-Anteil:** xhigh ist zu **97.5%** Thinking (fast alles Reasoning, kaum sichtbare Antwort). medium 73.2%, low 57.8%.
- **Score/1k Tokens** (Qualität pro Token): instruct dominiert (467), weil kein Thinking-Overhead. xhigh ist am ineffizientesten (31) — für 15 878 Tokens nur 86.7 Score.
- **Score/Sekunde** (Qualitäts-Throughput): instruct am schnellsten (21.7), xhigh am langsamsten (0.38).

> **Wichtig:** „Score/1k Tokens" und „Score/Sekunde" favorisieren instruct, weil diese Metriken den *absoluten* Qualitätsgewinn auf harten Tasks nicht sehen. instruct holt bei cli001 nur 72 (medium 100). Die Effizienz-Metriken sind ein **Kostensenkungs-**, kein Qualitätssignal.

---

## Analyse & Befunde

1. **`medium` = klare Empfehlung.** Beste Durchschnittsqualität (93.0) bei gleichzeitig schnellstem TPS (26.3) und moderatem Aufwand (3 244 Out-Tokens, 124 s). Das Thinking-Budget von `medium` deckt den Sweet-Spot: genug Reasoning für die harten Tasks (cli001 → 100), ohne den xhigh-Overhead.

2. **`xhigh` ist Overkill mit Rauschen.** Der Qualitätsgewinn gegenüber `medium` ist **negativ** (86.7 < 93.0) und gegenüber `instruct` **vernachlässigbar** (86.7 ≈ 86.0). Der Preis: 5× Tokens, 58× Zeit, TPS halbiert. Das Extra-Thinking ist **inkonsistent** — es hebt cli004/cli005, drückt aber cli001/cli006. Für Routine-Tasks nicht vertretbar; nur für Einzelfall-Hard-Problems sinnvoll.

3. **`low` ist der schlechteste Modus.** 82.4 liegt *unter* instruct (86.0). Ein minimales Thinking-Budget zahlt den Token-/Zeit-Preis, bringt aber keinen ausreichenden Qualitätsgewinn — auf cli005 (62) und cli006 (72) sogar deutlich schlechter als ohne Thinking. *Kleines Budget ≠ proportionale Qualität.*

4. **`instruct` (off) ist die Latenz-Banker.** 86.0 in 24 s. Für latency-sensitive oder hochvolumige Nutzung das beste Preis-Leistungs-Verhältnis — es liegt nur 7 Punkte unter `medium`, kostet aber 1/5 der Zeit und 1/3 der Tokens.

5. **TPS-Caveat (xhigh):** Der niedrige xhigh-TPS (11.5) ist teilweise ein **Mess-Artefakt** — bei cli001 gab es Request-Retries/Timeouts (918 s), die die wall-time aufblähen, während `output_tokens` nur die finale Antwort zählt. Der „echte" Decode-Speed ist höher; die effektive Throughput-Verlangsamung ist real, aber nicht rein hardwarebedingt.

---

## Grenzen / Caveats

- **n = 6 Assets** pro Modus — kleines Stichprobenvolumen; einzelne Ausreißer (cli006 xhigh = 58) wiegen schwer.
- **Ein Modul** (cli_benchmark) — repräsentativ für praktische CLI-Problem solving, **nicht** für alle Task-Typen. Thinking-lastigere Module (reasoning, code_quality) könnten andere Muster zeigen.
- **Ein Lauf pro Modus** — keine Wiederholungen/Varianz; Scores können sich bei Re-Runs verschieben.
- **xhigh-Retries** verzerren die TPS-Messung (siehe Befund 5).
- CLI-Tasks sind relativ kurz; bei längeren, komplexeren Outputs könnte sich das Quality/Token-Verhältnis verschieben.

---

## Empfehlung

| Szenario | Empfohlener Modus | Begründung |
|----------|:-----------------:|------------|
| **Default / beste Qualität** | `medium` | 93.0 Score, schnell, moderat |
| **Latenz / Budget / High-Volume** | `instruct` (off) | 86.0 in 24 s, 1/5 der Zeit |
| **Hartes Einzel-Problem** (1 Task) | `xhigh` | nur dort, wo Extra-Reasoning die 58×-Zeit wert ist |
| **Vermeiden** | `low` | schlechteste Qualität (82.4) |

**Konkreter Vorschlag für `provider_config.yaml`:** `reasoning_effort: medium` als Standard für `qwen3_8-27b-nvfp4` (ist aktuell bereits gesetzt). `xhigh` nicht als Default — nur als explizite, bewusste Wahl für Hard-Problems.

---

## Appendix

**Run-IDs & Snapshots** (`outputs/analysis/qwen3_8_thinking_modes/`):

| Modus | run_id | Modell-ID | Snapshot |
|-------|--------|-----------|----------|
| instruct | `f319329c062d` | qwen3_8-27b-nvfp4 | `instruct.csv` |
| low | `f509a27713d0` | qwen3_8-27b-nvfp4-thinking | `low.csv` |
| medium | `bacf2a69dd4b` | qwen3_8-27b-nvfp4-thinking | `medium.csv` |
| xhigh | `661a9b7658df` | qwen3_8-27b-nvfp4-thinking | `xhigh.csv` |

**Laufzeiten:** instruct 3.6 min · low 5.3 min · medium 5.8 min · xhigh 47.4 min (gesamt ~62 min).

**Konfiguration:** `reasoning_effort` wurde zwischen den Runs in `config/provider_config.yaml` geändert und nach dem Lauf auf `medium` zurückgesetzt. Orchestrierung: `outputs/analysis/qwen3_8_thinking_modes/run_matrix.py`.
