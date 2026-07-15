# CrucibleMark v5.1.0 — Coverage-aware Scoring, Daten-Intégrität & Dual-Thinking-Profile

> 277 Commits seit v4.6.1 — die umfangreichste Release-Reihe in der Projektgeschichte.
> Drei Achsen: **Scoring-Reform** (v5.0.0 + v5.1.0) · **Daten-Wurzelbehandlung** · **vLLM Dual-Thinking-Benchmarking**.

---

## ⚠️ Breaking Changes

Dieses Release enthält **zwei aufeinanderfolgende Breaking Changes** an der
Scoring-Logik. Total Scores, Rankings und `coverage_ratio` ändern sich.
Historische Leaderboards bleiben über Git-Tags reproduzierbar.

### v5.0.0 — Coverage-aware Scoring + ToolUse als 8. Modul (13.07.2026)

**Vorher (≤ v4.10.18):** `Total = Σ(present·weights) / Σ(present·weights)`
(Selbstnormalisierung — fehlende Module renormierten auf 0–100).

**Nachher (≥ v5.0):** `Total = Σ(present·weights) / Σ(present+missing+unknown)·weights`
— fehlende Modul-Daten reduzieren den Score (Malus im Nenner). Strukturell
incapable Modelle bleiben exempt. **Keine Benchmark-Re-Runs nötig** — die
Per-Asset-Daten lagen bereits in den CSVs.

**ToolUse als 8. Scoring-Modul:** `enable_scoring: true`, `module_weight: 1.0`,
`default_contribution: {routine: 0.5, reasoning: 0.5}`. `combined_score` fließt
in den Total Score ein. `capability_field: supports_tool_use` steuert die
Coverage-Klassifikation.

**6-Status-Taxonomie für jedes Modul:**

| Status | Bedeutung | Wirkung |
|---|---|---|
| `present` | Modul getestet + Daten gültig | normal |
| `missing` | Modul getestet, alle Rows error | Malus |
| `unknown` | `capability_field` fehlt in Card | Malus + WARNING-Log |
| `incapable` | `capability_field: false` | exempt (kein Malus) |
| `rolling_out` | < `deployment_threshold` (10%) Coverage | für alle ausgeschlossen |
| `not_deployed` | deaktiviert | für alle ausgeschlossen |

**Deployment-Schwelle:** Ein Modul gilt erst ab ≥10% der Modelle mit gültigen
Daten als deployed. Verhindert dass ein 3/110-Modul 107 Modelle bestraft.

**Neue Leaderboard-Spalte `coverage_ratio`** (gewichtete Test-Abdeckung 0.0–1.0):
- v5.0: 109× 1.0, 1× 0.87 (Llama 4 Scout, −13% durch ToolUse-Missing)
- v5.1: 107× 1.0, 3× 0.87

**Per-Modell `Tests Run`-Erwartung:** Incapable-Modelle bekommen `expected_assets`
um die incapable-Modul-Assets reduziert (z.B. 43/43 statt 43/49). `logical_count`
zählt nur gültige Status — Error-Rows nicht als "run" gewertet.

**Begleitender Fix:** `moduleweight` → `module_weight` (Typo in Config-YAML).
Mit `enable_scoring: true` wäre das Gewicht sonst `None` gewesen.

### v5.1.0 — Striktere Incapable-Klassifikation (14.07.2026)

**Design-Defekt in v5.0:** Ein Modell mit `supports_tool_use: false` wurde
pauschal als "incapable" (exempt) klassifiziert — **selbst wenn es getestet
wurde und alle Rows error waren**. Inversion des gewünschten Verhaltens:
getestet+durchgefallen = exempt (belohnt), teilweise durchgefallen = Malus
(bestraft).

**Fix:** `_classify_module_status` bekommt `attempted_set` aus `df_all`
(inkl. error-Rows). Ein Modell mit `capability_field: false` ist **nur dann**
incapable wenn es **0 Rows** für das Modul hat. Hat es ≥1 Row (auch error) →
"missing" (Malus). `_expected_assets_for_model` analog angepasst.

**Card-Korrekturen (Data Quality):**
- `command-a-plus-05-2026`: `supports_tool_use: false → true`
  (Cohere Command A+ ist `use_case_primary: "agentic"` — der `false`-Flag war
  Provider-Stabilitätsaussage, keine Kapabilität; 6 error-Rows vorhanden).
- `openai_gpt-oss-20b`: `supports_tool_use: false → true`
  (GPT-OSS unterstützt Function Calling; 6 error-Rows).
- `deepseek-r1-distill-qwen-32b`: unverändert (0 Rows, legitime incapable).

### Score-Auswirkungen (verifiziert)

| Modell | v4.10.18 | v5.0.0 | v5.1.0 | Δ v5.1 |
|---|---|---|---|---|
| Command A+ | Rank 62 / 71.42 | Rank 62 / 71.42 | Rank 104 / 61.90 | **−42 Plätze** |
| GPT-OSS 20B | Rank 104 / 64.85 | Rank 104 / 64.85 | Rank 108 / 56.20 | **−4 Plätze** |
| Llama 4 Scout | Rank 110 / 55.17 | Rank 110 / 42.06 | Rank 110 / 42.06 | −13% in v5.0 |
| 106 present-Modelle | normal | +ToolUse | +ToolUse | ToolUse trägt bei |
| Invariante | R+R=T | R+R=T | R+R=T | 0 Verletzungen |

**Benchmark-CSVs (local/cloud/commercial) unverändert** — nur Leaderboard-CSVs
neu generiert. Keine Re-Runs.

---

## Architektur-Innovationen

### Dual-Thinking-Profile (vLLM)

**Problem:** Lokale Thinking-Modelle (Qwen3, Gemma 4, Ornith) liefen mit
`enable_thinking: false`; Cloud-Modelle (o1/o3/Claude/Gemini) mit Thinking ON
→ systematischer lokaler Handicap im Leaderboard.

**Lösung:** Ein vLLM-Container pro Modell bedient **zwei Benchmark-Profile
per Request** (`chat_template_kwargs.enable_thinking`). Kein Server-Neustart
beim Profil-Wechsel. Eine Card, zwei Leaderboard-Einträge.

- `_expand_thinking_profiles()` in ConfigValidator (nur `api_type=="vllm"`)
  generiert Thinking-Eintrag mit `card_model_id: {base_id}` und
  `chat_template_kwargs: {"enable_thinking": true}`.
- `vllm_base.swap_model()` entkoppelt via `_active_config`: gleiche `config:`
  → kein Swap, nur per-Request-Param-Wechsel (verifiziert: Standard 0.6s vs
  Thinking 8.8s).
- `card_model_id`-Redirect teilt Card zwischen Profilen — kein `TODO`-Placeholder,
  keine Drift-Card.
- `resolve_canonical_model_id` mit Redirect gibt Profile-eigene ID zurück
  (`{base}-thinking`), NICHT Card's `model_id` — sonst verschmelzen die
  CSV-Zeilen.

### Token-Overflow Root-Cause-Fix (Defense-in-Depth)

`outputs/.../benchmark_cost.csv` zeigte `Tokens Total` bis 1e+156 und
korrumpiertes `Benchmark Cost (USD)`. Zwei-Schicht-Fix:

**Root Cause:** `_coerce_dataframe_metrics()` (`data_loader.py`) coercete
`tokens_used` nicht zu numeric → `.groupby().sum()` auf String-Spalte
konkatenierte Per-Task-Strings (`"3620.03082.03082.0..."`) statt zu summieren.

**Fix:** 12 Spalten zu `pd.to_numeric(errors="coerce")` ergänzt:
`tokens_used`, `tokens_per_second`, `load_time`, `response_length`,
`max_score`, `total_score`, `token_limit_used`, `llm_judge_score`,
`llm_judge_latency_ms`, `judge_task_compliance`, `judge_output_quality`,
`judge_standard_adherence`.

**Ergebnis:** 89/89 `tokens_total` plausibel (37.700–209.700), 623/623
`tokens_per_module` plausibel, 0 Overflow.

**Defense-in-Depth:** `_sanitize_cost()` in `entry_builders.py` (Threshold
1 Mio. USD + `math.isfinite()`) bleibt als zweite Schicht.

### `thinking_mode` als Leaderboard-Spalte

Neue Sichtbarkeitsebenen für den Thinking-Runtime-Modus:

| Ebene | Wo | Quelle |
|---|---|---|
| **Audit-Log-Header** | `**Thinking Mode:** Thinking/Standard` | `save_audit_log(thinking_mode=…)` |
| **CSV-Spalte** | pro Task | `_resolve_thinking_mode()` aus model_cfg |
| **Leaderboard-Spalte** | zwischen Speed Profile und Total Score | aus CSV aggregiert |
| **Review-Prompt** | `{model_thinking_mode}` als hartes Datenfeld | aus CSV (nicht erraten) |

`thinking_probe_detected` (Card) dokumentiert **Fähigkeit** (stabil).
`thinking_mode` (CSV) dokumentiert **Runtime-Konfiguration** (pro Lauf).
Klar getrennt.

### Cohere als nativer ToolUse-Connector

Vorher nur OpenAI/Anthropic-Pattern. Cohere jetzt mit dediziertem
ToolUse-Connector, Command A+ als Test-Modell. Cohere in
`classification_taxonomy.json → manufacturers.values` aufgenommen
(`jurisdiction: "CA"`).

---

## Framework-Refactoring (Sektionen A–M)

Systematische Zerlegung gegen die Architektur-Regeln aus `CLAUDE.md`.
**Verhaltenserhaltend** — keine Änderungen an Scoring/Token-Budget/Provider-Logik.

- **Sektion A:** `utils/model_utils.py` (Monolith) → 7 Submodule + Re-Export-Bridge
  (`model_card_io`, `model_id_base`, `model_id`, `model_size_class`,
  `model_thinking`, `model_token_budget`, `model_version`). Rückwärtskompatibel
  — alle bestehenden Imports funktionieren unverändert.
- **Sektion B:** Judge-Caching — Function-Attribute-Caching → Modul-Level-Singleton.
- **Sektion C:** 4 dead no-op `_extract_reasoning_tokens`-Stubs gelöscht;
  `vllm_base.py` Methoden-Extraktion.
- **Sektion D:** `scripts/web_export.py` → Package (`scripts/web_export/`
  mit `constants.py`, `entry_builders.py`, `filters.py`, `loader.py`, `main.py`,
  `top_level.py`). Einstieg: `python -m scripts.web_export`.
- **Sektion E+J:** `benchmark_auto.py` aufgespalten + Provider-Branch-Pitfall-Doku.
- **Sektion F:** Helper-SSoT — `utils/text_helpers.py` + `utils/io_helpers.py`
  eliminieren Duplikate über Web-Export, Card-Utils, Maintenance-Skripte.
- **Sektion G:** 18 raw `yaml.safe_load` → `ConfigValidator` in 15 Skripten.
- **Sektion H:** 27 historische Migrationsskripte → `scripts/legacy/`
  (von Lint excludiert).
- **Sektion I:** 131 `print()` → `logging` in Framework-Utils.
- **Sektionen K+L+M:** C901-Komplexitäts-Auflösung in ToolUse-Exporter, Report,
  Leaderboard, Review/Cleanup — **252 Verstöße → 0**.
- **711 auto-fixable Ruff-Verstöße** zusätzlich bereinigt.
- **`make lint` + `make test`** um `tests/` erweitert (Framework-Refactor Phase 0).

---

## Datenqualität & Web-Export

### Score-Vertrag & SSoT

- **`_SCORES_CONTRACT_KEYS` als SSoT:** Alle 10 (später 9) Modul-Keys IMMER
  vorhanden (auch null) — Contract-Re-Injection nach letztem `_strip_none()`-Pass.
- **`political_bias`-Phantom-Key entfernt:** Forward-Looking-Platzhalter für ein
  nie implementiertes Bias-Modul erzeugte `political_bias: null` in allen 88
  Modelle. Web erwartet 9 echte Module + `tooluse_combined` (Frontend), nicht 10.
  Political-Compass-Daten bleiben in `data.json.political_compass` (separate Section).
- **Card-Feld-Contract geschlossen:** `supports_tool_use_state` als Tri-State
  (`true`/`false`/null). `dual_profile` ersetzt `-thinking`-Suffix-Heuristik.

### Slug- & Type-Konsistenz

- **Slug-SSoT:** `slug = slugify(raw_model_id)` (nicht `model_name`).
  Eliminiert 5 Hybrid-Pair-Kollisionen (`gemma-4-31b` vs `-thinking`, …).
  `model_id` = stabile Identität (eindeutig pro CSV-Zeile), `model_name` =
  veränderlicher Display-Wert (von Thinking/Standard geteilt).
- **`normalize_pending()` Sentinel-Hardening:** `_PENDING_SENTINELS = frozenset(
  {"Pending", "—", "–", "", "n/a", "N/A", "NA", "null", "None", "none", "nan"})`.
  En-Dash (U+2013) ≠ Em-Dash (U+2014) als separate Codepoints.
- **Type-Konsistenz:** `parse_compact_number()` ("83.7K"→83700), `parse_percent()`
  ("100%"→100.0), `parse_int()` ("2"→2). Zahlen als Zahlen im JSON,
  Formatierung in der Darstellungsschicht.
- **`audit_log_count`-Semantik:** Zählt jetzt NUR Audit-Logs für exportierte
  Modelle (vorher: alle Verzeichnisse inkl. tote/blacklisted) — 5071 → 3676.
- **Emoji-Variation-Selectors:** `_EMOJI_RE` um U+FE0F (VS16), U+FE0E (VS15),
  U+200D (ZWJ) erweitert. `"⏱️ Interactive"` → `"Interactive"` statt `"️ Interactive"`.
- **Review-Prosa-Drift-Fix (zweischichtig):** Meta-Reviewer-Prompt verbietet
  Zahl-Zitate + `_strip_metric_lines()` entfernt Metrik-Zeilen aus Audit-Logs
  BEVOR sie den LLM-Prompt erreichen. 19.912 Metrik-Zeilen entfernt.

### Web-Export-Bug-Fixes (3 Hochpriorisierte)

1. **`provider_landscape_review.md`-Fallback war No-Op** — beide Pfade waren
   identisch (`comparisons_path.parent / "reviews"` == `comparisons_path`).
   Fix: beide Pfade unabhängig von `root_dir` prüfen.
2. **Warning-Spam für geskippte Modelle** — Card-Warning wurde VOR Skip-Prüfung
   geloggt, 30+ irrelevante WARNINGS pro Lauf. Fix: Warning in `_process_leaderboard`
   NACH Skip-Prüfung.
3. **Non-atomic Markdown writes (4 Stellen)** — `atomic_write_json` als SSoT.

---

## Card- & Vocabulary-Bereinigung

- **`model_version`-Pollution-Migration:** 31 Cards hatten Quant/Format-Tokens
  (`Q8_0 GGUF`, `FP8`, `NVFP4`) und interne Variant-Namen in `model_version`.
  Neues Feld `model_variant` + `quantization_format` als SSoT. 33 Cards +
  1498 CSV-Zeilen migriert.
- **Community-Fine-Tuner aus `vendor` → `community`:** `Mia-AiLab`, `llmfan46`,
  `HauhauCS` (finetune_uncensored) korrekt klassifiziert.
- **Vocabulary-Cleanup:** `Dense` + `Tool-Use` Tags deprecated→null
  (redundant mit `parameter_architecture` bzw. `supports_tool_use`). 4 Cards bereinigt.
- **SUFFIX-SSoT für Card-Filenames:** `{base}--{shortcode}.json` als alleiniger
  Schreibpfad. Read-Reihenfolge: SUFFIX → legacy PREFIX → unprefixed. 13 Karten
  umbenannt, 2 Auto-Duplikate gelöscht.

---

## Bias-Reviews (inhaltsbezogen)

- **WordSmith Gemma 4 (Standard + Thinking):** „Wolf im Schafspelz" — Shift 1,81 /
  1,01, Polarity-Flip-Rate 23,08% / 24,36%. Card-Fix: `origin_country=null→USA`,
  `developer_jurisdiction=null→US`.
- **Grok 4.20 (Reasoning):** PC-Bias-Review + Standard-Review + ToolUse-Narrative.
- **qwen3_6-27B-thinking:** PC-Daten + Bias-Review nachgeholt (2026-07-12).
- **GLM 5.2:** Komplett neues Modell mit PC + Bias-Review + Review + ToolUse-Narrative
  (Score 74.06).

### Known Limitation

**8 Modelle ohne Political Compass** (akzeptiert, deferralbar — kein Bias-Review
möglich): `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`,
`Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`,
`qwable-3_6-35b-q5`, `qwen3_6-27B`. Kein PC-Daten → kein Bias-Review (by Design).

---

## Blacklist

- **Ornith 1.0 35B SPRK/llama.cpp:** Blacklisted (schwächer als FP8-thinking).
- **K2.7 Code:** Aus Blacklist entfernt.
- **Blacklist-Restructure:** Slug-SSoT + `normalize_pending`-Hardening +
  `kept_overrides`-Gruppen (NVFP4/Wordsmith, Uncensored/Abliterated,
  Cross-Provider-Reference, Best-Quant-Wins, Thinking-Variants) als
  dokumentierte Audit-Trail.
- **184 alte Reviews** bereinigt (Maintenance).
- **qwopus-Cards + Reviews** entfernt.

---

## Modell-Inventar (Inventar — kein Release-Höhepunkt)

11 neue Modelle hinzugefügt, ToolUse-Unterstützung für NVIDIA Nemotron Nano 30B
aktiviert. Details siehe `model_cards/`. Die Modell-Erweiterung ist nicht der
Release-Höhepunkt — siehe Scoring-Reform oben.

---

## Provider & Infrastructure

- **vLLM Spark Connector (`VSPK`):** Lokales CUDA-Backend für asusGX10.
  `base_url=http://192.168.1.191:3300/v1` direkt. 14 Tests.
- **Cohere:** Nativer ToolUse-Connector (siehe Architektur-Innovationen).
- **OpenRouter Full Migration:** Card-Manager umgestellt, `api_key` entfernt.
  Free-Tier-Support + canonical ID alias mappings.
- **vLLM Extensions-Whitelist:** `_VLLM_EXTRA_BODY_KEYS` (top_k, min_p,
  repetition_penalty, chat_template_kwargs, guided_*, bad_words, stop_token_ids).
  Geschlossen gegen Mapping-Drift.
- **Per-Modell Sampling-Config:** 4 VSPK-Modelle erhalten Sampling aus Card
  (Google: 1.0/0.95/64, Qwen3.6: 0.6/0.95/20).

---

## Testing & Quality

- **Test-Suite-Wachstum:** 1316 (v4.10.18) → **1346** (v5.0, +26 neue) → **1350 passed**
  (v5.1, +4 neue), 22 skipped, 0 failed.
- **Ruff:** 0 violations (`make validate` exit 0).
- **C901:** 252 → 0 Komplexitäts-Verstöße.
- **Neue Tests:**
  - `test_score_calculator_coverage.py` (+30): Status-Klassifikation,
    Deployment-Threshold-Boundary, Invarianten, coverage_ratio, end-to-end.
  - `test_model_cards_tool_use_evidence.py` (NEU).
  - `test_web_export_field_coverage.py` um `coverage_ratio` ergänzt.
- **Conftest:** `CARD_DIR`-Isolation per Test.
- **Makefile:** `install`/`install-dev` Targets, PHONY-Synchronisation.

---

## Documentation Overhaul

Vollständige Neustrukturierung der Projektdokumentation.

| Dokument | Status |
|---|---|
| `USER_GUIDE.md` | Komplette Neustrukturierung |
| `SETUP_GUIDE.md` | Konfig-Hierarchie + v5.0-Änderungen |
| `SCORING_METHODOLOGY.md` | Aggregation + Coverage-aware Scoring |
| `ARCHITECTURE.md` | Judge/Trennung, sequenzielle Modell-Abarbeitung, Coverage-Sektion |
| `BENCHMARK_MODULES.md` | Komplette Modul-Doku |
| `POLITICAL_COMPASS_KONZEPT.md` | Konzeptionelle Überarbeitungen |
| `REF_TODO.md` | Referenz-Todo neu (NEU) |
| `GLOSSAR.md` | Terminologie-Sammlung (NEU) |
| `SCORING_METHODOLOGY_WEB.md` | Web-Export-spezifische Scoring-Doku (NEU) |
| `docs/Blog-Entwürfe/` | Konsolidiert (vormals verstreut) |
| Memory Bank | Sessions 44–64 dokumentiert |

---

## Verifikation

- `ruff check`: 0 violations.
- `make validate`: exit 0.
- `pytest tests/`: 1350 passed, 22 skipped, 0 failed.
- Leaderboard: 110 Modelle, Invariante `Routine+Reasoning=Total` 0 Verletzungen.
- Web-Export: 88 Modelle, 0 Vendor-Warnungen, 9 Score-Keys, 366 Eleventy-Files,
  0 Errors.
- Benchmark-CSVs (local/cloud/commercial) unverändert — nur Leaderboard-CSVs
  neu generiert.

---

**Vollständiger Changelog:** Siehe [CHANGELOG.md](CHANGELOG.md) und [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Commits seit v4.6.1:** 277 — `git log v4.6.1..v5.1.0 --oneline`
