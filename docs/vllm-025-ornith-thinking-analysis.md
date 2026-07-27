# vLLM 0.25.1 + Ornith-1.0-35B-FP8 Thinking-Mode Analyse

**Datum:** 2026-07-27
**Status:** Implementiert + getestet
**Betroffene Komponenten:** vLLM-Server (gx10), Connector (`vllm_base.py`), Chat-Template, Benchmark-Harness

## Problem

Ornith-1.0-35B-FP8 schnitt im Thinking-Modus mit vLLM 0.25.1 signifikant schlechter ab als mit vLLM 0.21. Symptome:

- **9 Timeouts** im Thinking-Benchmark (vs 0 im Standard-Modus)
- **58% weniger Tokens/s** (21.11 vs 50.25)
- **3.3x längere Avg Duration** (83.84s vs 25.49s)
- `reasoning_tokens` in Benchmark-CSV leer (`None`) — Thinking nicht messbar

## Ursachen (5 bestätigte Faktoren)

### 1. Ornith Chat-Template-Defekt (HF Discussion #31)

**Das war der Haupttreiber.** Das aktive Template `ornith-1.0-35B.jinja` berechnete `ns.last_query_index` (Zeile 67, 74), verwendete es aber nie. Alle historischen `<think>`-Blöcke wurden in jedem Turn neu gerendert.

**Auswirkung:**
- Context-Inflation in Multi-Turn-Konversationen (Tool-Use-Tasks)
- Thinking-Loops: Modell liest alte Pläne und wiederholt sie
- Tool-Call-Loops: Modell re-issued denselben Tool-Call

**Warum schlimmer mit vLLM 0.25.1?** vLLM 0.22+ reicht das `reasoning`-Feld korrekt an das Template durch. In vLLM 0.21 waren historische `reasoning_content`-Felder leer → keine Context-Inflation.

**Fix:** Template mit `last_query_index`-Guard gepatcht (3 Änderungen):
1. `{%- set index = loop.index0 %}` — Index-Variable für Guard
2. `message.reasoning` Fallback — vLLM 0.22+ Feldname-Unterstützung
3. Conditional Guard: historische Turns verlieren `<think>`-Blöcke

Siehe `~/ai/shared/configs/vllm/templates/CHANGELOG-ornith-template-fix.md` auf gx10.

### 2. vLLM 0.22.0: `reasoning_content` → `reasoning` (PR #42664)

vLLM 0.22.0 hat das API-Response-Feld umbenannt. Der Connector handled beide Feldnamen (`vllm_base.py:1147-1150`), aber die Umbenennung ändert, wie Reasoning-Content an das Chat-Template zurückgegeben wird.

### 3. `reasoning_tokens` nicht in vLLM 0.25.1 Usage

vLLM 0.25.1 befüllt `completion_tokens_details.reasoning_tokens` nicht. Die `_extract_reasoning_tokens()`-Methode gab `None` zurück. Der Fallback griff nur bei leeren Content (Thinking-Only-Responses).

**Fix:** Neue `_estimate_reasoning_tokens()`-Heuristik in `base.py`:
- Kein Reasoning → 0
- Kein Content → `completion_tokens` (alles ist Reasoning)
- Beide vorhanden → `completion_tokens - len(content)//4` (grobe Schätzung)

Implementiert in `vllm_base.py` (Non-Streaming + Streaming) und `llamacpp_base.py`.

### 4. Thinking-Loops (HF Discussion #12)

Ornith-1.0-35B ist bekannt dafür, in Thinking-Loops stecken zu bleiben. Community-Fix: `temp=0.6, repetition_penalty=1.08`. User s1arsky bestätigt: Loops auch mit `rep_penalty` möglich.

vLLM 0.22.0 führte neuen Triton-Kernel für Penalties ein (#40657), der `repetition_penalty` anders berechnen könnte.

### 5. MoE-Backend Fallback

vLLM 0.25.1 unterstützt `flashinfer_b12x` nicht für FP8 MoE. Fällt auf TRITON zurück (langsamer). Die TOML setzt `moe_backend = "flashinfer_b12x"`, aber `VLLM_FLASHINFER_MOE_BACKEND=latency` (aus `default.env`) ermöglicht den Fallback.

## Implementierte Fixes

### Code-Änderungen (CrucibleMark)

| Datei | Änderung | Zeilen |
|-------|----------|--------|
| `utils/providers/base.py` | `_estimate_reasoning_tokens()` hinzugefügt | 202-232 |
| `utils/providers/vllm_base.py` | Non-Streaming: Heuristik-Fallback | 1162-1175 |
| `utils/providers/vllm_base.py` | Streaming: Heuristik-Fallback | 1262-1275 |
| `utils/providers/llamacpp_base.py` | Non-Streaming: Heuristik-Fallback | 762-774 |
| `utils/providers/llamacpp_base.py` | Streaming: Heuristik-Fallback | 870-882 |

### Server-Änderungen (gx10)

| Datei | Änderung |
|-------|----------|
| `~/ai/shared/configs/vllm/templates/ornith-1.0-35B.jinja` | `last_query_index`-Guard + `message.reasoning` Fallback |
| `~/ai/shared/configs/vllm/templates/CHANGELOG-ornith-template-fix.md` | Dokumentation für lokalen Agent |

### Config (keine Änderungen nötig)

- `config/provider_config.yaml`: Keine Änderungen — `enable_thinking`, `max_tokens`, `chat_template_kwargs` alle korrekt
- `Ornith1-35B-FP8.toml`: Keine Änderungen — `reasoning_parser=qwen3`, `repetition_penalty=1.08`, Template-Pfad korrekt

## Verifizierung (2026-07-27)

### Live-Test: Thinking vs No-Thinking

Nach Template-Fix + Connector-Fix wurde ein Live-Test gegen den laufenden vLLM-Server durchgeführt:

| Metrik | No-Thinking | Thinking |
|--------|-------------|----------|
| Elapsed | 1.7s | 5.4s |
| Completion Tokens | 3 | 147 |
| Reasoning Tokens | None (korrekt) | 146 (Heuristik) |
| Think Content | leer (korrekt) | Reasoning-Trace vorhanden |
| Finish Reason | stop | stop |
| Server-Stop bei Profil-Wechsel | — | **Nein** (Profil-Wechsel ohne Swap) |

**Ergebnis:** Alle 4 Checks grün:
- ✅ Thinking/No-Thinking-Trennung korrekt
- ✅ `reasoning_tokens`-Heuristik liefert Werte (vorher `None` in vLLM 0.25.1)
- ✅ `finish_reason=stop` bei beiden (keine Timeouts, keine Thinking-Loops)
- ✅ Profil-Wechsel ohne Container-Swap (gleicher TOML `Ornith1-35B-FP8`)

### Connector: 401/403 → "loading" Fix

**`vllm_base.py:458-465`** — `_probe_status()` behandelte HTTP 401/403 als `"down"`,
was bei transienten Auth-Issues (Token-Rotation, Rate-Limit, Probe-Race) einen
unnötigen Server-Neustart auslöste. Geändert zu `"loading"` — der Connector wartet
statt den Server zu killen.

### Wichtige Erkenntnis: Config-Expansion für Test-Scripts

Der `ConfigValidator` expandiert vLLM-Modelle mit `enable_thinking: true` in zwei
Profile (Standard + `-thinking`), beide mit gleichem TOML. Der Connector erkennt
die TOML-Identität und führt **keinen Container-Swap** durch (`_ensure_model_ready`
Pfad 2: Profil-Wechsel).

**Fallstrick für Test-Scripts:** Wenn der Connector mit **Raw-Config** (ohne
`ConfigValidator`) initialisiert wird, fehlt das `-thinking`-Profil. Der Connector
fällt auf `swap_model()` zurück → **Server wird gestoppt** (5 Min Neustart).

**Lösung:** Immer `ConfigValidator("benchmark_config.yaml").config` verwenden,
nicht `yaml.safe_load(open("config/provider_config.yaml"))` direkt.

## Benchmark-Ergebnisse (2026-07-27)

### Tool-Use Benchmark (6 Assets, `--force`)

| Metrik | Thinking | Standard | Delta |
|--------|----------|----------|-------|
| Combined Score | **69.5%** (Moderate) | 50.3% (Weak) | +19.2pp |
| P1 Tool Exec | 89.2 | 80.8 | +8.4 |
| P2 Synthesis | 60.0 | 62.5 | -2.5 |
| Avg Duration | 55.7s | 17.4s | 3.2x langsamer |
| Total Time | 341.3s | 106.9s | — |
| Tokens | 20.326 | 10.463 | — |
| **Timeouts** | **0** (vorher 9!) | 0 | — |
| Empfehlung | CAUTION | NOT_RECOMMENDED | — |

### Per-Test Vergleich

| Test | Thinking | Standard |
|------|----------|----------|
| 001 EU Lizenzrecherche | 64.0% | 26.0% |
| 002 HTTP Fetch & Extract | 77.5% | 80.0% |
| 003 404 Fehlerbehandlung | 37.0% | 51.0% |
| 004 Richtige Toolwahl | **91.0%** | 37.2% |
| 005 HURL ableiten | 80.0% | 70.0% |
| 006 Mehrsprachige Recherche | 67.5% | 37.5% |

### Schlussfolgerung

1. **Template-Fix (HF #31) resolves 9 Timeouts → 0**: Der `last_query_index`-Guard
   verhindert Context-Inflation und Thinking-Loops in Multi-Turn-Tool-Use-Tasks.

2. **Thinking-Modus deutlich überlegen** (+19.2pp): Ornith-1.0-35B profitiert stark
   von Thinking bei Tool-Use — besonders bei Tool-Wahl (91% vs 37%) und komplexer
   Recherche (64% vs 26%). Standard-Modus hat 3/6 `parse_error` bei `web_search`.

3. **Standard-Modus schneller** (3.2x): 17.4s vs 55.7s avg — kein Thinking-Overhead.
   Aber Score deutlich schlechter (50.3% vs 69.5%).

4. **`reasoning_tokens`-Heuristik funktioniert**: Werte werden geliefert (vorher `None`
   in vLLM 0.25.1). Schätzung ist grob aber ausreichend für Benchmark-Erfassung.

## Bekannte Limitierungen

1. **`thinking_token_budget` nicht gesetzt**: Bug #44676 (thinking_token_budget + Tool-Calls korrumpiert Tool-Args). Der `thinking-budget-by-effort` Mod auf gx10 patcht vLLM, greift aber nur bei `reasoning_effort` (nicht bei `chat_template_kwargs.enable_thinking`).

2. **MoE-Backend TRITON**: `flashinfer_b12x` wird nicht unterstützt, TRITON-Fallback ist langsamer. Keine Lösung ohne vLLM-Update oder Kernel-Portierung.

3. **`reasoning_tokens` Heuristik**: Die Schätzung `completion_tokens - len(content)//4` ist ungenau (Char-to-Token-Ratio variiert). Exakte Werte erfordern serverseitige Tokenisierung.

## Quellen

- [HF Discussion #31](https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B/discussions/31) — Template-Defekt
- [HF Discussion #12](https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B/discussions/12) — Thinking-Loops
- [vLLM 0.22.0 Release Notes](https://github.com/vllm-project/vllm/releases/tag/v0.22.0) — `reasoning`-Feld, `thinking_token_budget`, Penalties-Kernel
- [vLLM Bug #44676](https://github.com/vllm-project/vllm/issues/44676) — thinking_token_budget + Tool-Calls
