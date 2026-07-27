# Data Schemas

Spezifikationen der zentralen Datenstrukturen. Hot-Context (systemPatterns.md) zeigt nur SSoT-Brücken-Funktionen; hier sind die Felder detailliert.

---

## Model Card (`benchmark_scores/model_cards/*.json`)

SSoT für: Preise, Modell-Identität (`model_id`), Thinking-Probe-Status, Tool-Use-Support, Lizenz-Tier, Context-Window, Parameter-Architektur, Knowledge-Cutoff.

### Pflichtfelder
| Feld | Typ | Zweck |
|---|---|---|
| `card_id` | str | Eindeutige ID (SSoT-Schema: `{base}--{shortcode}`) |
| `model_id` | str | Kanonische API-ID (SSoT für Cross-File-Mapping) |
| `model_version` | str | Format/Quant-Version |
| `display_name` | str | Menschenlesbarer Name |
| `vendor` | str | Hersteller/Provider |
| `card_status` | enum | `draft` / `minimal` / `complete` / `verified` |
| `weights_license_tier` | enum | `proprietary` / `restricted-weights` / `open-weights` |

### Preise (USD pro 1M Tokens, SSoT ab v4.0.0)
| Feld | Typ |
|---|---|
| `input_price_per_1m` | float |
| `output_price_per_1m` | float |

### Modell-Spezifikation
| Feld | Typ | Zweck |
|---|---|---|
| `parameter_architecture` | enum | `dense` / `moe` / `hybrid` |
| `params_total_b` | float \| null | Total-Parameter in Mrd. |
| `params_active_b` | float \| null | Aktive Parameter pro Token |
| `context_window_k` | int | Kontextfenster in 1K |
| `knowledge_cutoff` | str (ISO-8601) | Trainings-Daten-Cutoff |
| `architecture_tags` | list[str] | Manueller Tag-Override (z.B. `["Thinking", "Coder"]`) |

### Thinking-Probe (SSoT ab v3.5.8)
| Feld | Typ | Zweck |
|---|---|---|
| `thinking_probe_detected` | bool \| null | Empirisches Probe-Ergebnis |
| `thinking_probe_manual_override` | bool | Manuell gesetzt, ohne Probe |
| `thinking_probe_at` | str (ISO-8601) | Zeitpunkt der Probe |

### Thinking-Override (SSoT ab v4.7.1, optional)
```yaml
thinking_override:
  value: false                 # bool (Pflicht)
  reason: "..."                # str (Pflicht, nicht whitespace-only)
  active_until: "2026-12-31"   # str ISO-8601 (optional)
```

### Tool-Use-Support (Tri-State ab v4.x)
| Wert | Bedeutung |
|---|---|
| `true` | Empirisch verifiziert (mean P1 > 0) |
| `false` | Empirisch verifiziert (kein Tool-Call erfolgreich) |
| `"untested"` | Noch kein Tool-Use-Benchmark gelaufen |

`null` ist Legacy-Synonym für `"untested"`.

### Beispiele
- `qwen_qwen3_7-max.json` (Cloud, Free-Tier)
- `claude-sonnet-4-5-20250929.json` (proprietär, dated)
- `gemma-3-12b-it-q8.json` (open-weights, quantisiert)

---

## Provider Card (`benchmark_scores/provider_cards/*.json`)

SSoT für Provider-Metadaten (Sovereign Risk, GDPR-DPA, Chinese-NSL-Risk, Privacy Notes).

### 16 Pflichtfelder
| Feld | Typ | Zweck |
|---|---|---|
| `provider_id` | str | Eindeutige ID (z.B. `anthropic`, `openrouter`) |
| `name` | str | Display-Name |
| `region` | str | Hauptsitz-Region |
| `founded` | int | Gründungsjahr |
| `website` | str | URL |
| `logo_url` | str | Logo-Asset-URL |
| `overview` | str | Kurzbeschreibung |
| `deployment` | enum | `cloud` / `self-hosted` / `hybrid` |
| `pricing_model` | enum | `subscription` / `usage` / `tiered` |
| `is_cloud` | bool | Cloud-only? |
| `commercial_offering` | bool | Kommerziell verfügbar? |
| `api_reliability` | enum | `high` / `medium` / `low` |
| `community_ecosystem` | enum | `large` / `medium` / `small` / `none` |
| `licensing_terms` | str | Lizenz-Beschreibung |
| `compliance_certifications` | list[str] | z.B. `["GDPR", "SOC2"]` |
| `known_concerns` | list[str] | z.B. `["Chinese NSL risk"]` |

### Index
`_index.json` via `rebuild_provider_index()` nach jeder Card-Änderung neu bauen.

### Konsumenten
- `risk_calculator.py` (kein Duplikat-Parsing mehr)
- `generate_review.py` (card-status-basiert)
- `web_export.py:_collect_provider_cards()` → `provider_cards.json`

---

## Benchmark-CSVs

### `local_models_benchmark.csv`, `cloud_models_benchmark.csv`, `commercial_models_benchmark.csv`

Aggregierte Test-Logs, geschrieben von `UnifiedBenchmarkRunner.save_results()`.

**Schlüssel-Spalten:**
| Spalte | Typ | Zweck |
|---|---|---|
| `model` | str | Kanonische `model_id` (nach `enforce_card_first()`) |
| `model_version` | str | Format/Quant-Version |
| `asset_id` | str | Test-Asset-Identifier (z.B. `code_quality_001`) |
| `timestamp` | str (ISO-8601) | UTC-Zeitstempel |
| `score` | float | Test-Score (0-100) |
| `total_tokens` | int | Token-Verbrauch |
| `reasoning_tokens` | int | Reasoning-Tokens (nur bei OpenRouter) |
| `token_limit_cutoff` | bool | Budget erreicht? |
| `score_contributions` | JSON | ToolUse-Subscores (P1/P2/Combined) |

### `benchmark_leaderboard.csv` (Compact)

Generiert aus den 3 Detail-CSVs. Spalten:
- `Model Name` = `display_name` aus Card
- `Model ID` = kanonische `model_id`
- `Code Quality`, `CLI Badge`, `Reasoning`, `UX Writing`, ... = Modul-Scores
- `Hardware Profile` (nur in Detailed)
- `model_id_raw` (nur in Detailed)

### `political_compass_leaderboard.csv`

Autarkes PC-Format mit `vanilla_*` / `forced_*` Spalten. Geschrieben von `PoliticalCompassResultManager.save_leaderboard_csv()`.

### `tooluse_leaderboard.csv`

Generiert aus 3 Detail-CSVs mit `aggregate_from_benchmark_csvs()`. Spalten:
- `p1_score`, `p2_score`, `combined_score` — aus **flachen CSV-Spalten** (neue Rows ab post-commit d82996f) ODER Fallback auf `score_contributions`-JSON (Legacy-Rows vor d82996f)
- `mcp_mode` (`mock` / `live`)
- `mcp_latency_s`, `call1_time_s`, `call2_time_s`, `total_time_s`
- `tool_call_valid` (bool), `hallucination_flag` (bool)
- `total_tokens` (Summe aller 6 Test-Runs)
- Sovereignty Gap = local_avg − all_avg

**Wichtig:** `score_contributions`-Feld ist seit Writer-Redesign (d82996f) leer in neuen Rows.
Flache Spalten (`p1_score` etc.) sind das neue SSoT für ToolUse-Metriken in der CSV.

---

## Provider-Config-Felder

### `config/provider_config.yaml` (per Provider)
| Feld | Typ | Zweck |
|---|---|---|
| `context_window` | int | Globaler Context-Window-Default |
| `num_predict` | int | Max-Output-Tokens-Cap |
| `parallel` | int | Parallele Slots im llama-server |
| `server_ready_timeout_sec` | int | Timeout für Cold-Start |
| `existing_server_ready_timeout_sec` | int | Timeout für Adopt-Pfad |
| `server_ready_poll_sec` | int | Poll-Intervall |

### Per-Modell-Overrides (in `providers.<local>.<provider_key>.models[].*`)
| Feld | Typ | Überschreibt |
|---|---|---|
| `context_length` | int | `context_window` |
| `parallel` | int | `parallel` |
| `enable_thinking` | bool | Default-Thinking-Verhalten |
| `num_gpu_layers` | int | GPU-Layer-Anzahl |

---

## Score-Format (`scripts/analysis/scoring.py`)

- **Scale:** Konfigurierbar (3/5/10), Default 5
- **Felder im Result-JSON:** `llm_judge_score`, `llm_judge_reasoning`
- **Module-Weight-System:** `module_weight` in `config.yamls`, Selbstnorm
- **`is_complete()` Prüfung:** `judge_parse_success is not None` (nicht `judge_score`)

---

## Token-Budget-Schema (`benchmark_config.yaml`)

```yaml
token_budgets:                    # Standard-Modelle
  cultural_intelligence: 500
  ux_writing: 3500
  content_transformation: 3500
  documentation_quality: 6000
  code_quality: 6000
  cli_benchmark: 4000

token_budgets_reasoning_models:   # Reasoning-Modelle (erhöhtes Gesamtkontingent)
  cultural_intelligence: 4000
  ux_writing: 8000
  content_transformation: 8000
  documentation_quality: 12000
  code_quality: 65536             # Kein Cap für grosse Reasoning-Ketten
  cli_benchmark: 16000
  # Kein Eintrag für "reasoning" / "reasoning_metacog" — bleibt unbegrenzt
```

**Aktualisiert 2026-06-10** (war veraltet: ux_writing=17500, code_quality=12000).

**Resolve-Pipeline:** `_raw_budget` → `resolve_token_budget()` → `min(budget, provider_num_predict)` → an Server.

---

## Heartbeat-Config (`benchmark_config.yaml`, ab v4.7.4)

```yaml
heartbeat:
  enabled: true              # Komplett ausschalten (CI-Runs, kurze Tests)
  interval_seconds: 120      # 60=Original, 120=Default (maximale Ruhe)
```

**Defensiv-Fallback-Hierarchie:**
1. Block fehlt → `(True, 60.0)` (backward-compat)
2. Block ist kein Dict → `(True, 60.0)`
3. `interval_seconds` nicht-numerisch → `60.0`
4. `interval_seconds <= 0` → `60.0`
