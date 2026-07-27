# vLLM gx10 Konfigurations-Leitfaden

**Stand:** 2026-07-27 · vLLM 0.25.1
**Zielgruppe:** Lokaler Agent auf gx10 (ASUS GX10 / DGX Spark), der vLLM-Server und TOML-Konfigurationen verwaltet.
**Zweck:** Sicherstellen, dass vLLM-Upgrades und Modell-Konfigurationen korrekt durchgeführt werden, insbesondere für Thinking-Modelle.

> **Quelle der Wahrheit für CrucibleMark-Connector-Logik:** `docs/vllm-025-ornith-thinking-analysis.md` (Ornith-Root-Cause-Analyse) und `docs/ARCHITECTURE.md` (Dual-Thinking-Profile).

---

## 1. System-Übersicht

| Komponente | Pfad auf gx10 | Beschreibung |
|------------|---------------|--------------|
| vLLM-Venv | `~/venvs/vllm025/` | vLLM 0.25.1, nativ (kein Docker) |
| TOML-Modelle | `~/ai/shared/configs/vllm/models/` | Eine TOML pro Modell-Konfiguration |
| Chat-Templates | `~/ai/shared/configs/vllm/templates/` | Custom Jinja-Templates (nur Ornith) |
| Mods | `~/ai/shared/configs/vllm/mods/` | vLLM-Source-Patches |
| Start/Stop-Scripts | `~/ai/shared/scripts/vllm-start` / `vllm-stop` | Nativer Server-Start/Stop |
| Default-Env | `~/ai/shared/configs/vllm/default.env` | Umgebungsvariablen (MoE-Fallback etc.) |
| Metrics-Proxy | `metrics_proxy.server` | Routet `:4300→:3300` (Chat), `:4301→:3301` (Embed), authentifiziert jeden Request |

**Ports:** `:3300` Chat (Main), `:3301` Embed, `:4300`/`:4301` Proxy-Ports (Tailscale `100.89.110.0`).
**Auth:** Bearer-Token `sk-local-mg2026` (im Proxy, nicht im vLLM-Server selbst).

---

## 2. vLLM 0.25.1 — Bekannte Issues & Workarounds

### 2.1 `reasoning_content` → `reasoning` Feld-Umbenennung (ab vLLM 0.22.0)

vLLM 0.22.0 hat das API-Response-Feld `reasoning_content` zu `reasoning` umbenannt (PR #42664).

**Auswirkung:**
- Der CrucibleMark-Connector handled beide Feldnamen (`vllm_base.py:1147-1150`, `base.py:241`).
- **Custom Chat-Templates** müssen `message.reasoning` (neu) UND `message.reasoning_content` (alt) prüfen — sonst wird historisches Thinking in Multi-Turn-Konversationen nicht gerendert.

**Template-Check (für Custom-Templates):**
```jinja
{# FALSCH (nur alter Feldname): #}
{% if message.reasoning_content %}

{# RICHTIG (beide Feldnamen): #}
{% if message.reasoning_content or message.reasoning %}
```

**Betroffen:** Nur Modelle mit Custom-Templates (aktuell: Ornith). Hersteller-Templates (Qwen3, Gemma4) werden von vLLM gepatcht und sind i.d.R. kompatibel.

### 2.2 `reasoning_tokens` nicht in vLLM 0.25.1 Usage

vLLM 0.25.1 befüllt `completion_tokens_details.reasoning_tokens` **nicht** zuverlässig.

**Workaround (Connector-Seite):** `_estimate_reasoning_tokens()`-Heuristik in `base.py:202-232` schätzt Reasoning-Tokens aus `completion_tokens - len(content)//4`. Dies ist ein Fallback — exakte Werte erfordern serverseitige Tokenisierung.

**TOML-Auswirkung:** Keine. Der `reasoning_parser` muss trotzdem korrekt gesetzt sein (siehe §3), damit vLLM Thinking-Content überhaupt separiert.

### 2.3 `thinking_token_budget` + Tool-Calls = Bug (#44676)

vLLM 0.25.1 hat einen Bug: `thinking_token_budget` in Kombination mit Tool-Calls korrumpiert die Tool-Argumente.

**Workaround:** `thinking_token_budget` NICHT in TOML oder `extra_args` setzen. Thinking wird ausschließlich über `chat_template_kwargs: {"enable_thinking": true}` pro Request gesteuert.

**Mod `thinking-budget-by-effort`:** Patcht vLLM, um `thinking_token_budget` aus `reasoning_effort` abzuleiten. Greift nur bei `reasoning_effort`-Parameter, **nicht** bei `chat_template_kwargs.enable_thinking`. Daher sicher — kein Konflikt mit dem Workaround.

### 2.4 MoE-Backend: `flashinfer_b12x` → TRITON-Fallback

vLLM 0.25.1 unterstützt `flashinfer_b12x` nicht für FP8 MoE. Fällt auf TRITON zurück (langsamer).

**Workaround:** Env-Var `VLLM_FLASHINFER_MOE_BACKEND=latency` in `default.env` aktiviert den Fallback automatisch. Keine manuelle Aktion nötig.

**Betroffen:** FP8 MoE-Modelle (Ornith). NVFP4 MoE-Modelle (Qwen 3.6 35B-A3B, Gemma 4 26B) können ebenfalls betroffen sein — bei Performance-Problemen `moe_backend` in TOML prüfen.

### 2.5 Thinking-Loops (modellspezifisch)

Einige Modelle bleiben im Thinking-Modus in Loops stecken (wiederholen denselben Reasoning-Schritt).

**Betroffen:** Ornith-1.0-35B (HF Discussion #12). Community-Fix: `repetition_penalty=1.08`.

**Nicht betroffen:** Qwen3-, Gemma4-Modelle (Hersteller-Templates, keine Loop-Neigung in Benchmarks beobachtet).

---

## 3. TOML-Konfigurations-Checkliste pro Modell-Familie

Jede TOML unter `~/ai/shared/configs/vllm/models/` muss folgende Felder korrekt setzen:

### 3.1 Ornith 1.0 35B FP8 (`Ornith1-35B-FP8.toml`)

| Feld | Sollwert | Begründung |
|------|----------|------------|
| `reasoning_parser` | `qwen3` | Ornith nutzt Qwen3-Reasoning-Format |
| `repetition_penalty` | `1.08` | Thinking-Loop-Mitigation (HF #12) |
| `chat_template` | Pfad zu `ornith-1.0-35B.jinja` | Custom-Template mit `last_query_index`-Guard (HF #31 Fix) |
| `moe_backend` | `flashinfer_b12x` | Fällt auf TRITON zurück (§2.4) — kein Fix verfügbar |
| `thinking_token_budget` | **NICHT SETZEN** | Bug #44676 (§2.3) |
| `extra_args` | `--default-chat-template-kwargs {"enable_thinking":false}` | Default: kein Thinking. Pro-Request via Connector aktivierbar. |

**Template-Status:** Gepatcht am 2026-07-27. Siehe `~/ai/shared/configs/vllm/templates/CHANGELOG-ornith-template-fix.md`.

### 3.2 Qwen 3.6 27B Dense (`Qwen3.6-27B.toml`)

| Feld | Sollwert | Begründung |
|------|----------|------------|
| `reasoning_parser` | `qwen3` | Qwen3-Reasoning-Format |
| `chat_template` | **NICHT SETZEN** (Built-in) | Qwen3 nutzt Hersteller-Template, vLLM-patcht kompatibel |
| `repetition_penalty` | `1.0` (Default) | Keine Loop-Neigung beobachtet |
| `thinking_token_budget` | **NICHT SETZEN** | Bug #44676 (§2.3) |
| `extra_args` | `--default-chat-template-kwargs {"enable_thinking":false}` | Default: kein Thinking |

**Benchmark-Erkenntnis:** Thinking-Modus ist -6,08pp schlechter als Standard (77,83% vs 71,75%). Dies ist ein echtes Modellverhalten (Overthinking bei Tool-Use), **kein Konfigurations-Bug**. Keine TOML-Änderung ändert das.

### 3.3 Qwen 3.6 35B-A3B MoE (`Qwen3.6-35B-NVFP4.toml`)

| Feld | Sollwert | Begründung |
|------|----------|------------|
| `reasoning_parser` | `qwen3` | Qwen3-Reasoning-Format |
| `chat_template` | **NICHT SETZEN** (Built-in) | Hersteller-Template |
| `repetition_penalty` | `1.0` (Default) | Keine Loop-Neigung beobachtet |
| `moe_backend` | `flashinfer_b12x` | NVFP4 MoE — TRITON-Fallback möglich (§2.4). Bei Performance-Problemen prüfen. |
| `thinking_token_budget` | **NICHT SETZEN** | Bug #44676 (§2.3) |
| `extra_args` | `--default-chat-template-kwargs {"enable_thinking":false}` | Default: kein Thinking |

**Benchmark-Erkenntnis:** Thinking-Modus ist +5,42pp besser als Standard (68,00% vs 62,58%). MoE profitiert von Thinking.

### 3.4 Gemma 4 Familie (`Gemma-4-26B.toml`, `Gemma-4-31B.toml`, `Gemma-4-31B-Wordsmith-NVFP4.toml`)

| Feld | Sollwert | Begründung |
|------|----------|------------|
| `reasoning_parser` | `deepseek_r1` | Gemma 4 nutzt `<channel|>`-Tokens, separiert via `--reasoning-format deepseek` |
| `chat_template` | **NICHT SETZEN** (Built-in via `--jinja`) | Google-Template, vLLM-patcht kompatibel |
| `repetition_penalty` | `1.0` (Default) | Keine Loop-Neigung beobachtet |
| `moe_backend` | `flashinfer_b12x` (nur 26B MoE) | 31B ist Dense — kein MoE-Backend nötig |
| `thinking_token_budget` | **NICHT SETZEN** | Bug #44676 (§2.3) |
| `extra_args` | `--jinja`, `--reasoning-format deepseek`, `--default-chat-template-kwargs {"enable_thinking":false}` | `<channel|>`-Separation + Default kein Thinking |

**Benchmark-Erkenntnis:** Thinking schadet bei Gemma 4 Dense-Modellen (-0,75 bis -9,50pp). Gemma 4 26B (MoE) leicht negativ (-3,37pp). Thinking ist für Gemma 4 Tool-Use nicht empfohlen.

### 3.5 Hermes 4 Familie (`Hermes4-70B.toml`, `Hermes4.3-36B.toml`) — aktuell deaktiviert

| Feld | Sollwert | Begründung |
|------|----------|------------|
| `reasoning_parser` | `hermes` (oder `deepseek_r1` falls `hermes` nicht verfügbar) | NousResearch-Format |
| `chat_template` | **NICHT SETZEN** (Built-in) | Llama-3.1-Architektur, Hersteller-Template |
| `repetition_penalty` | `1.0` (Default) | Keine Loop-Neigung bekannt |
| `thinking_token_budget` | **NICHT SETZEN** | Bug #44676 (§2.3) |
| `extra_args` | `--default-chat-template-kwargs {"enable_thinking":false}` | Default: kein Thinking |

**Hinweis:** Hermes 4.3 36B braucht ~40 Min/Test mit Thinking (32K Budget). Benchmark-Verschiebung auf Home-Intranet geplant.

---

## 4. Upgrade-Checkliste (vLLM-Version-Update)

Wenn vLLM auf gx10 geupgraded wird (z.B. 0.25.1 → 0.26.0), folgende Punkte prüfen:

### 4.1 Vor dem Upgrade

- [ ] **Release Notes lesen** — besonders Breaking Changes zu `reasoning_parser`, `chat_template_kwargs`, `thinking_token_budget`, MoE-Backend
- [ ] **Bug-Tracker prüfen** — Status von #44676 (`thinking_token_budget` + Tool-Calls). Falls gefixt: `thinking_token_budget` kann aktiviert werden, Mod `thinking-budget-by-effort` wird obsolet.
- [ ] **`reasoning`-Feldname** — prüfen, ob weitere Umbenennungen stattgefunden haben. Connector handled `reasoning` + `reasoning_content`, aber neue Feldnamen erfordern Connector-Update.
- [ ] **MoE-Backend** — prüfen, ob `flashinfer_b12x` jetzt unterstützt wird. Falls ja: `moe_backend` in TOMLs bleibt `flashinfer_b12x`, TRITON-Fallback entfällt.
- [ ] **Mods-Kompatibilität** — `thinking-budget-by-effort` Mod gegen neue vLLM-Version neu anwenden/prüfen.

### 4.2 Nach dem Upgrade

- [ ] **Smoke-Test** — `vllm-start --config Qwen2.5-0.5B` (kleinstes Modell), `/v1/models` via Proxy abfragen.
- [ ] **Thinking-Probe** — `make probe-thinking MODEL=<model> PROVIDER=vllm_spark` für jedes Thinking-Modell. Erwartet: `reasoning`-Feld befüllt, `finish_reason=stop`.
- [ ] **Template-Verifikation** — Custom-Templates (Ornith) auf `message.reasoning`-Handling prüfen. Multi-Turn-Test mit Thinking: historische `<think>`-Blöcke dürfen nicht neu gerendert werden.
- [ ] **`reasoning_tokens` in Usage** — prüfen, ob vLLM jetzt `completion_tokens_details.reasoning_tokens` befüllt. Falls ja: Connector-Heuristik wird automatisch obsolet (Fallback greift nur bei `None`).
- [ ] **MoE-Performance** — Benchmark-Lauf (6 Assets) mit Ornith Thinking. Avg Duration vergleichen mit vLLM 0.25.1-Baseline (55,7s). Bei signifikanter Verbesserung: `flashinfer_b12x` vermutlich jetzt unterstützt.
- [ ] **Tool-Use-Benchmark** — Subset-Lauf (6 Assets, `--force`) für mindestens ein Dense- und ein MoE-Modell. Timeouts = 0 erwartet.

### 4.3 Rollback

Falls das Upgrade Probleme verursacht:
```bash
# vLLM 0.25.1 wiederherstellen
~/venvs/vllm025/bin/vllm --version  # prüfen
# Bei Bedarf: altes Venv reaktivieren oder neu erstellen
```

---

## 5. Template-Verifikations-Checkliste

Für jedes Modell mit Custom-Template (aktuell nur Ornith):

1. **`message.reasoning` Fallback** — Template muss beide Feldnamen prüfen:
   ```jinja
   {% if message.reasoning_content or message.reasoning %}
   ```
2. **`last_query_index`-Guard** — Historische Turns verlieren `<think>`-Blöcke (verhindert Context-Inflation):
   ```jinja
   {%- if loop.index0 < ns.last_query_index %}
   ```
3. **`preserve_thinking`-Support** — Optionaler Kwarg, um historisches Thinking zu behalten (für Debugging):
   ```jinja
   {%- if not chat_template_kwargs.get('preserve_thinking', false) %}
   ```
4. **Multi-Turn-Test** — 3+ Turns mit Tool-Use, Thinking aktiv. Prüfen:
   - Keine Context-Inflation (Token-Count stabil)
   - Keine Thinking-Loops (`finish_reason=stop`, nicht `length`)
   - Keine Tool-Call-Loops (gleicher Tool nicht wiederholt)

---

## 6. Aktive Mods

| Mod | Pfad | Zweck | Trigger |
|-----|------|-------|---------|
| `thinking-budget-by-effort` | `~/ai/shared/configs/vllm/mods/thinking-budget-by-effort/` | Setzt `thinking_token_budget` aus `reasoning_effort` | Nur bei `reasoning_effort`-Parameter (nicht bei `chat_template_kwargs.enable_thinking`) |

**Wichtig:** Dieser Mod ist sicher, weil CrucibleMark `enable_thinking` via `chat_template_kwargs` steuert, nicht via `reasoning_effort`. Der Mod greift nicht im normalen Benchmark-Betrieb.

---

## 7. Thinking-Modus: Modell-spezifische Empfehlung

Basierend auf Benchmark-Ergebnissen (vLLM 0.25.1, Tool-Use, 6 Assets):

| Modell | Arch | Standard | Thinking | Delta | Empfehlung |
|--------|------|----------|----------|-------|------------|
| Ornith 1.0 35B FP8 | MoE | 50,3% | 69,5% | **+19,2pp** | Thinking empfohlen |
| Qwen 3.6 35B-A3B | MoE | 62,6% | 68,0% | **+5,4pp** | Thinking empfohlen |
| Gemma 4 31B | Dense | 69,4% | 68,7% | -0,8pp | Standard (marginal) |
| Gemma 4 26B | MoE | 72,3% | 68,9% | -3,4pp | Standard |
| Qwen 3.6 27B | Dense | 77,8% | 71,8% | **-6,1pp** | Standard |
| Gemma 4 31B Wordsmith | Dense | 75,0% | 65,5% | **-9,5pp** | Standard |

**Muster:** Thinking hilft MoE-Modellen (Ornith, Qwen 35B-A3B), schadet Dense-Modellen (Qwen 27B, Gemma 31B). Ausnahme: Gemma 4 26B (MoE) — Thinking leicht negativ.

**Konsequenz für TOML:** Keine Änderung. Die `enable_thinking: true` in `provider_config.yaml` erzeugt beide Profile (Standard + Thinking). Der Benchmark entscheidet, welches Profil besser abschneidet. Die Card dokumentiert das empfohlene Profil via `tooluse_recommendation`.

---

## 8. Debugging — Häufige Probleme

### 8.1 Timeouts im Thinking-Benchmark

**Ursachen:**
1. Template-Defekt (Context-Inflation) — `last_query_index`-Guard prüfen (§5)
2. Thinking-Loops — `repetition_penalty` erhöhen (1.05–1.10)
3. `thinking_token_budget` gesetzt + Tool-Calls — aus TOML entfernen (§2.3)

**Diagnose:** `make probe-thinking MODEL=<model> PROVIDER=vllm_spark` — `finish_reason` prüfen. `length` = Token-Limit erreicht (Loop oder Budget). `stop` = normal.

### 8.2 `reasoning_tokens` leer in Benchmark-CSV

**Erwartet** in vLLM 0.25.1 — Connector-Heuristik liefert Schätzwerte. Falls `None` in CSV: Connector-Code prüfen (`base.py:202-232`, `vllm_base.py:1168-1181`).

### 8.3 Server-Neustart bei Profil-Wechsel

**Ursache:** Connector fällt auf `swap_model()` zurück statt Profil-Wechsel. Passiert, wenn Config nicht via `ConfigValidator` geladen wurde (Raw-`yaml.safe_load`).

**Lösung:** Test-Scripts müssen `ConfigValidator("benchmark_config.yaml").config` verwenden, nicht `yaml.safe_load(open("config/provider_config.yaml"))`.

### 8.4 HTTP 401/403 vom Proxy

**Erwartet** bei transienten Auth-Issues (Token-Rotation, Rate-Limit). Connector behandelt 401/403 als `"loading"` (kein Server-Kill). Bei dauerhaftem 401/403: Proxy-Token `sk-local-mg2026` in `provider_config.yaml` und Proxy-Config prüfen.
