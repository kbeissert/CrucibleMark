# Progress

Letzte Releases + aktueller Stand. Vollständige Historie: `reference/decisions-log.md`.

### 2026-06-13 (Session 19) — Model Card Publish-Audit

**Ziel:** Überprüfung ob alle Model Cards ohne Falschinformationen publishbar sind.

**4 fehlerhafte Cards korrigiert (Commit 1dc07a5):**
- `google_gemma-4-31b-it.json`: `summary` behauptete "Weights nicht öffentlich zugänglich" → falsch für `restricted-weights`. `local_deployment_possible: false → true`. `known_limitations`: "Nur über Cloud-API" entfernt. `judge_context_hint`: "Cloud-only" entfernt.
- `magistral-small-latest.json`: `local_deployment_possible: false → true` (Apache 2.0, Weights auf HuggingFace).
- `deepseek_deepseek-v4-flash.json`: `local_deployment_possible: false → true`, Cloud-Only-Formulierungen entfernt.
- `deepseek_deepseek-v4-pro.json`: gleiche Fixes wie flash.

**`mistral-large-2411.json` geprüft (Commit 5e33133):**
- `restricted-weights` via HuggingFace-Check bestätigt (MRL-Lizenz, Weights öffentlich).
- Hardware-Hinweis ergänzt: `"Lokaler Betrieb erfordert über 300 GB GPU-VRAM (123B dense Modell)"` als erste `known_limitations`-Zeile (aus offiziellem HF Model Card).

**`verify_model_cards.py` ausgeführt + 2 Fixes (Commit fd4ebaf):**
- **Pricing-Fix:** 20 lokale Open-Weights-Modelle hatten `input_price_per_1m: null` / `output_price_per_1m: null`. Für lokale Modelle (kein API-Preis) korrekt: `0.0`. Betroffene: gemma-4 Quants (8 Varianten), hermes-3/4 (4 Varianten), qwen3-coder-lokal (3 Varianten), qwen3_5/3_6-lokal (4 Varianten), codestral-latest.
- **Script-Bug-Fix:** `verify_model_cards.py` Zeile `missing_in_cards = config_model_ids - all_model_ids` erzeugte 18 false-positive „fehlende Cards" weil provider_config Punkte nutzt (`qwen3.5-4b-q4`) und Card-`model_id`-Felder Unterstriche (`qwen3_5-4b-q4`). Fix: `_normalize(mid)` Funktion + normalisierter Set-Vergleich.

**Endstatus verify:**
- `✅ Alle 99 Konfigurationsmodelle haben Cards.`
- Verbleibende `⚠️` sind legitim: `params_total_b: null` (geschlossene Modelle), `thinking_probe_*: null` (neue ungeprüfte Modelle), `license_url: null` (proprietäre Modelle, kein einzelner URL).

---

### 2026-06-13 (Session 18) — Deployment-Badge-Refactoring (Two-Layer-Architektur)

**Kontext:** Scoreboard zeigte für lokale llamacpp-Modelle (`llamacpp`, `llamacpp_spark`) keinen Deployment-Badge — M4APL/SPRK waren Ollama-Ära-Artefakte ohne einheitliche „lokal"-Kategorie. User-Clarification: „lokal" = gesamtes Intranet (M4 MacBook Pro, DGX Spark, Gaming-PC RTX 4070), nicht nur Ollama.

**Architektur-Entscheidung:** Zweischichtiges System:
- **Layer 1 — Deployment-Category (Badge):** `LCL` / `API` / `OR` / `GR` / `CLD` — primärer Shortcode im Scoreboard
- **Layer 2 — Hardware-Profile (Detail/Tooltip):** `m4_macbook_pro_metal` / `dgx_spark_cuda` / `rtx4070_cuda` — gerätespezifischer Kontext

**`config/provider_config.yaml`:**
- Neuer Top-Level-Block `hardware_profiles` mit 3 Einträgen:
  - `m4_macbook_pro_metal`: Apple M4 Pro, 24 GB unified memory, Metal backend
  - `dgx_spark_cuda`: NVIDIA DGX Spark, GB10 Superchip, ~115 GB
  - `rtx4070_cuda`: NVIDIA RTX 4070, 12 GB VRAM, CUDA backend
- `deployment_category` zu allen Providern ergänzt: `api` (anthropic, openai, google, xai, mistral), `cloud` (groq, openrouter, ollama_cloud), `local` (ollama_local, llamacpp, llamacpp_spark)
- `llamacpp.short_code`: `M4APL` → `LCL`
- `llamacpp_spark.short_code`: `SPRK` → `LCL`

**`utils/model_utils.py`:**
```python
_PROVIDER_DEPLOYMENT_CATEGORY: dict[str, str] = {
    "anthropic": "api", "openai": "api", "google": "api", "xai": "api", "mistral": "api",
    "openrouter": "cloud", "groq": "cloud", "ollama_cloud": "cloud",
    "ollama": "local", "ollama_local": "local", "local": "local",
    "llamacpp": "local", "llamacpp_spark": "local", "llama_cpp": "local", "llamacpp_local": "local",
}

_PROVIDER_HARDWARE_PROFILES: dict[str, str] = {
    "llamacpp": "m4_macbook_pro_metal",
    "llamacpp_spark": "dgx_spark_cuda",
    "llama_cpp": "m4_macbook_pro_metal",
    "llamacpp_local": "m4_macbook_pro_metal",
}

def get_deployment_category(provider: str) -> str:
    return _PROVIDER_DEPLOYMENT_CATEGORY.get(str(provider).lower().strip(), "local")

def get_hardware_profile(provider: str) -> str | None:
    return _PROVIDER_HARDWARE_PROFILES.get(str(provider).lower().strip())
```
- `_PROVIDER_SHORTCODES`: `llamacpp` + `llamacpp_spark` + alle lokalen Varianten → `LCL`

**`scripts/leaderboard/__init__.py`:**
- Import: `get_deployment_category`, `get_hardware_profile`
- Step 10: 2 neue Spalten: `Deployment Category` + `Hardware Profile`

**`scripts/web_export.py`:**
- Import: `get_deployment_category`, `get_hardware_profile`
- `_build_leaderboard_entry()`: 3 neue Felder: `provider_code`, `deployment_category`, `hardware_profile`

**`docs/MODEL_CLASSIFICATION.md`:**
- Sektion „Provider-Kategorien" → „Provider-Kategorien & Deployment-Badges" komplett neu: Two-Layer-Tabelle, Hardware-Profile-Tabelle, Anleitung „Neue Hardware hinzufügen" (4 Schritte).

---

### 2026-06-12 (Session 17) — 4 SSoT-Robustness-Fixes

**Commits:** `e5799bb`, `3225a78`, `4aaf450`, `411e5e3` (alle gepusht). **Architektur-Prinzip etabliert:** `model_id` = einziger SSOT-Kommunikations-Anker.

**Fix e5799bb — Hardware-Kontext SSOT (`system_context.py` + `generate_review.py`):**
- Symptom: Benchmark-Reviews für DGX-Spark-Modelle zeigten M4-MacBook-Hardware-Kontext statt DGX-Spark-Profil.
- Root Cause: `SystemContextManager` las `active_profile` aus Environment (= lokales Mac-System) statt Testsystem-Profil.
- Fix: `get_editor_prompt_injection(hardware_profile_key: str = "")` — neuer Parameter. Bei gesetztem Key: Profil-Lookup aus `benchmark_config.yaml → runner_environment.profiles`.
- Neue Hilfsfunktion `_get_hardware_profile_for_model(model_id, config)` in `generate_review.py`: Durchsucht alle Provider-Sektionen in `provider_config.yaml` nach `hardware_profile`-Key.
- 2 neue Profile in `benchmark_config.yaml`: `dgx_spark_cuda` (NVIDIA DGX Spark, GB10, ~115GB) + `m4_macbook_pro_metal` (Apple Silicon M4, 24GB).

**Fix 3225a78 — Tooluse-Reviews per-model Modus (`generate_review.py`):**
- Symptom: `--per-model-all-reviews` generierte keine Tooluse-Reviews.
- Root Cause: Tooluse-Leaderboard-IDs sind Ollama-Format (`gemma3:12b`) — können nicht auf Audit-Log-Slugs (CrucibleMark-Format) gemappt werden. Der per-model-Loop iteriert über Modell-IDs, findet kein Match.
- Fix: Tooluse-Schritt aus dem per-model-Loop herausgenommen → läuft nach dem Loop einmalig mit `tooluse_args.model = None` (= alle Modelle in einem Durchlauf).

**Fix 4aaf450 — Web-Export PC-Lookup (`scripts/web_export.py`):**
- Symptom: Political-Compass-Daten fehlten im Web-Export für Modelle, bei denen `raw_model_id` und Display-Name verschieden waren.
- Root Cause: `_lookup_pc_row` verwendete Display-Namen (`model_name`) für den Lookup in `political_compass_leaderboard.csv`. Die CSV enthält aber IDs ohne Vendor-Prefix (z.B. `qwen3.5-35b-a3b-q4`), nicht Display-Namen.
- Fix: `_pc_id = raw_model_id if raw_model_id and raw_model_id != "nan" else model_name`. `_pc_slug = slugify(_pc_id)`. PC-Lookup und PC-Leaderboard-Map-Lookup nutzen jetzt konsequent die ID.

**Fix 411e5e3 — Blacklist-Check in Tooluse-Reviews (`generate_review.py`):**
- Symptom: Tooluse-Reviews wurden für Modelle generiert, die auf der Webexport-Blacklist stehen.
- Root Cause: Guard 2 (`_run_tooluse_reviews`) las die Model Card zweimal, Blacklist-Check nutzte Slug statt `model_id`.
- Fix: Guard 2 lädt Model Card einmal (`card = _load_model_card(card_path)`), liest `model_id = card.get("model_id", slug)`, prüft `model_id in blacklist` (O(1)-Set-Lookup).

---

### 2026-06-12 — Vendor Cards vervollständigt (Commit a8acdd7)

**5 unvollständige Vendor Cards korrigiert und verifiziert:**
- `google.json`: display_name "Google DeepMind" → "Google AI", notable_models aktualisiert (Gemini 1.5 → Gemini 3.x/2.5/Gemma 4), data_residency gesetzt, description hinzugefügt, profile_verified
- `alibaba_cloud.json`: notable_models (Qwen → Qwen3.x), description hinzugefügt, profile_verified
- `alibaba_group_qwen_team.json`: notable_models (Qwen2.5 → Qwen3.x), description, gdpr_dpa_available "unknown"→false, profile_verified
- `alibaba_group_qwen_team_hauhaucs_community_fine_tune.json`: notable_models (Qwen3 Fine-Tunes), description, gdpr_dpa_available/eu_adequacy_decision "unknown"→false, profile_verified
- `google_deepmind_base_undix_community_distribution.json`: notable_models (Gemma 4 ergänzt), description, gdpr_dpa_available/eu_adequacy_decision "unknown"→false, profile_verified

**Alle 25 Vendor Cards jetzt profile_verified, bis auf `ara_apex_quant` und `unknown` (Platzhalter).**

---

### 2026-06-12 — Systematische Modellkarten-Korrektur (Commit 08845aa)

**Auslöser:** Bei Stichproben wurden fehlerhafte Metadaten in Modellkarten entdeckt (MiniMax M3, Claude Sonnet 4.6). Daraufhin wurden alle 98 Modellkarten systematisch per 5 paralleler Subagenten recherchiert und korrigiert.

**Korrigierte Karten (9 Dateien):**
- `gpt-4o-mini`: input_price 1.25 → 0.15, output_price 5.0 → 0.60 (offizieller OpenAI-Preis)
- `claude-sonnet-4-5-20250929`: context_window_k 1000 → 200 (Anthropic-Docs: 200k, nicht 1M)
- `gpt-5`: context_window_k 400 → 272 (LiteLLM/OpenAI: tatsächliches Limit)
- `gpt-5-mini`: input 0.75 → 0.25, output 4.5 → 2.0, ctx 200 → 272 (mit gpt-5.4-mini verwechselt)
- `gpt-5_4-mini`: context_window_k 128 → 272
- `gpt-5_4-nano`: context_window_k 400 → 272 (Texte in summary/strengths angepasst)
- `mistral-small-2603`: context_window_k 32 → 128 (Mistral Small 4 hat 128k)
- `qwen/qwen3-32b`: context_window_k 32 → 128 (32 war Modellgröße, nicht Kontextfenster)
- `qwen3.5:397b-cloud`: ctx 128 → 262, prices 0.6/3.6 → 0.39/2.34, local_deployment → true

**Recherche-Methode:** 5 Subagenten parallel (LiteLLM-Referenzdatei, offizielle API-Docs)

---

### 2026-06-12 — v4.9.4 Auto-Review Webexport-Blacklist Integration

**Commits:** TBD. **Tests:** Keine neuen Tests (Feature-Ergänzung in bestehendem Workflow).

**Hintergrund:** Modelle auf der Webexport-Blacklist benötigen kein Review, da sie nicht im Web-Export publiziert werden. Der Auto-Review-Modus sollte diese Modelle automatisch überspringen.

**Implementierung (`scripts/analysis/generate_review.py`):**

1. **Neue Funktion `_load_webexport_blacklist()` (Zeile 60-76):**
   - Liest `config/web_export_blacklist.yaml → blacklist`-Array
   - Returniert `set[str]` für O(1)-Lookup-Performance
   - Fehlertoleranz: Bei Ladefehlern wird leeres Set zurückgegeben (+ Warnung)

2. **Skip-Check in `_run_per_model_all_reviews()` (Zeile 732-735):**
   - `blacklist = _load_webexport_blacklist() if args.auto else set()`
   - Vor Review-Generierung: `if args.auto and slug in blacklist: print("⏩ ... Auf Webexport-Blacklist → Review wird übersprungen."); continue`

3. **Skip-Check in `_run_audit_reviews()` (Zeile 793, 810-814):**
   - Analog zur Per-Model-Funktion — Blacklist nur im `--auto`-Modus geladen und geprüft

**Scope:** Nur `--auto`-Modus betroffen (`make reviews-auto`). Manuelle Review-Aufrufe für einzelne Modelle ignorieren die Blacklist.

**Dokumentation:** `docs/AUDIT_AND_METAREVIEW.md` Sektion 2 um Webexport-Blacklist-Hinweis ergänzt.

---

### 2026-06-12 — v4.9.3 Vendor Card: description-Feld + editor_prompts-Fix

**Commits:** `871fa8c` (feat) + `2b4a433` (fix). **803/803 Tests grün.**

**Added — `config/card_template_vendor.yaml` v1.1.0:**
- Neues optionales Feld `description` (erstes optionales Feld, Position vor `card_subtype`):
  - `consumers: [web_export, review]`, `since: "v4.9.3"`
  - Constraints: `min_length: 240`, `max_length: 480`, `target_length: 360`
  - Pflicht-Hinweis: kurze, prägnante Beschreibung des Herstellers/der Community in 2–3 Sätzen
- Template-Version: `1.0.0` → `1.1.0`

**Fixed — `config/editor_prompts.yaml` prompt `provider_card_verification`:**
- `targets.directory`: `provider_cards/` → `vendor_cards/`
- Prompt-Text Schritt "Auftrag": `provider_cards/` → `vendor_cards/`
- Schritt 1 + Schritt 4: `provider_id` → `vendor_id`

**Tests:**
- `tests/test_card_template.py`: `test_provider_template_loads` Version-Assertion `"1.0.0"` → `"1.1.0"`

---

### 2026-06-12 — v4.9.1 Terminologie-Refactoring: Provider Cards → Vendor Cards

**Commit:** `570bc0f` — 50 Files geändert, 593 Insertionen, 481 Löschungen. **803/803 Tests grün.**

**Hintergrund:** Provider war doppelt belegt (API-Laufzeit UND Hersteller-Karte). Endgültige Trennung:
- `provider` = API-Laufzeit (Ollama, Anthropic, DGX Spark) — bleibt unverändert in allen Laufzeit-Dateien
- `vendor` = Hersteller-/Community-Profil-Karte — konsequent als "Vendor Card" benannt

**Phase 1 — Rename:**
- `benchmark_scores/provider_cards/` → `vendor_cards/` (17 JSON-Dateien)
- `config/card_template_provider.yaml` → `card_template_vendor.yaml`
- `utils/provider_card_template.py` → `vendor_card_template.py`
- `scripts/analysis/generate_provider_cards.py` → `generate_vendor_cards.py`
- `scripts/analysis/generate_provider_stats.py` → `generate_vendor_stats.py`
- `scripts/analysis/provider_card_status.py` → `vendor_card_status.py`
- `tests/test_provider_card_*.py` → `test_vendor_card_*.py` (3 Dateien)
- Vendor Card JSON: `provider_id` → `vendor_id` (alle 17 Dateien)

**Phase 2 — Content-Updates:**
- `config/card_template_vendor.yaml`: `card_type: "vendor"`, `name: vendor_id`
- `utils/card_template.py`, `utils/card_sync.py`: card_type `"provider"` → `"vendor"` (Literal, Checks)
- `scripts/analysis/validate_cards.py`, `sync_cards.py`, `generate_model_cards.py`: choices + card_type
- `Makefile`: Targets `vendor-cards`, `vendor-cards-status`, `vendor-cards-update`
- Docs: ARCHITECTURE, AUDIT_AND_METAREVIEW, CARD_MANAGEMENT, MAINTENANCE_LOG, THINKING_PROBE, USER_GUIDE, README
- `web_export.py`: `_collect_vendor_cards()`, output `vendor_cards.json`, `vendor_card_count` in meta

**Phase 3 — SSoT-Verknüpfung Taxonomy → Vendor Cards:**
- `config/classification_taxonomy.json → manufacturers`: `vendor_card_id` zu allen 13 Einträgen ergänzt
- `scripts/web_export.py`: `_build_vendor_card_id_lookup()` NEU → `vendor_card_ref` in jeder Modell-`data.json`
- `scripts/verify_model_cards.py`: `_load_vendor_card_id_map()` NEU + `🗂️`-Warnung wenn Vendor Card fehlt

**Test-Fixes:**
- `tests/test_card_template.py`: `profile_verified: True, profile_verified_at: "2026-01-01"` in Fixture (None ist Sentinel)
- `scripts/web_export.py`: `profile_verified` + `profile_verified_at` in model_card sub-dict ergänzt (waren als `web_export`-Consumer im Template markiert, fehlten im Sub-Dict)

**Bewusst NICHT umbenannt (Laufzeit-Provider-Konzept):**
- `config/provider_config.yaml`
- `utils/providers/`, `utils/provider_detection.py`, `utils/provider_health.py`, `utils/provider_selector.py`
- `provider`-Feld in Model Cards (`card.get("provider")`)

---

### 2026-06-12 (Session 16) — v4.9.0 Card-Datenpflege-System: Vendor-Kanonisierung + profile_verified + Editor-Prompt

**Scope:** Vollständiges Datenpflege-System für Model Cards und Provider Cards eingeführt. Drei Komponenten:

**1 — Vendor-Kanonisierung (Vorarbeit dieser Session):**
- `config/classification_taxonomy.json → manufacturers`: 13 kanonische Hersteller-Namen als SSOT
- `scripts/web_export.py _normalize_vendor()`: Normalisiert Vendor-Strings auf kanonische Namen (Aliase → Kanonisch)
- `scripts/verify_model_cards.py`: `🏭`-Warnungen bei nicht-kanonischen Vendor-Namen in Model Cards
- 16 Model Card JSONs mit Vendor-Korrekturen migriert (z.B. "Alibaba Cloud" → "Alibaba")

**2 — `profile_verified` / `profile_verified_at` für Model Cards:**
- `config/card_template_model.yaml`: 2 neue optionale Felder (seit v4.9.0) vor `heritage_ids`:
  - `profile_verified: bool` — True wenn inhaltliche Felder manuell recherchiert + verifiziert
  - `profile_verified_at: str | null` — ISO-8601-Datum der letzten Verifikation
- `scripts/verify_model_cards.py`: `🔍`-Warnungen wenn Feld fehlt oder `false`
- **119 Model Card JSONs** per `jq` bulk-migriert: `profile_verified: false`, `profile_verified_at: null`
- Scope der Verifikation: Alle inhaltlichen Felder **außer** Probe-Felder, ToolUse-Felder, Sampling-Parameter, `generated_at`, `card_status`, `heritage_ids`, `unknown`

**3 — `config/editor_prompts.yaml` — Prompt `model_card_verification`:**
- Strukturierter LLM-Prompt für redaktionelle Model-Card-Verifikation
- Glossar, 5-Schritt-Prozess, Was-verändern / Was-gesperrt-Tabelle, Qualitätskriterien
- `supports_tool_use` researchierbar, aber ToolUse-Benchmark-Override-Hinweis

**Dokumentation aktualisiert:**
- `docs/CARD_MANAGEMENT.md`: 3 neue Sektionen (Vendor-Kanonisierung, profile_verified-Workflow, Editor-Prompts) + Feldzahl-Update ("38 Pflicht, 18 Optional inkl. profile_verified")
- `memory-bank/activeContext.md`: Session-16-Eintrag

**Verifikation:** Alle 119 Model Card JSONs migriert, Template konsistent mit Provider Card Schema (profile_verified bereits auf Provider Cards vorhanden). `verify_model_cards.py` gibt korrekte `🔍`-Warnungen aus.

### 2026-06-12 (Session 15) — v4.8.6 Robustness-Fixes: Judge-Coverage, Draft-Card-Warning, ToolUse P1/P2 SSoT

**3 Robustness-Fixes implementiert (52/52 Tests grün):**

**Fix 1 — Judge-Skip-Coverage (`scripts/leaderboard/score_calculator.py::_aggregate_basic_stats()`):**
- Judge-Skip-Zeilen (`judge_prog.str.contains("skip")`) vor der Coverage-Formel herausgefiltert.
- Verhindert falsches 98%-Coverage wenn absichtlich übersprungene Antworten (z.B. kurze Refusals) in die Berechnung einfließen.

**Fix 2 — Draft-Card-Warning (`scripts/leaderboard/__init__.py`):**
- Nach `_model_name_ssot()`: `print()` + `logger.warning()` wenn `Model Name == "TODO"`.
- Macht auto-erstellte Draft-Cards (`ensure_card()`) sofort im Leaderboard-Lauf sichtbar — kein stilles Weiterlaufen mit unvollständigen Daten.

**Fix 3a — `update_model_card_tooluse_fields()` erweitert (`utils/model_utils.py`):**
- Neue Parameter `p1_score: float | None` und `p2_score: float | None`.
- Schreibt `tooluse_score_p1`/`tooluse_score_p2` direkt in Card JSON (atomarer Write mit `card_sync.py`-Muster).

**Fix 3b — `finalize_model()` persistiert P1/P2 in Card (`scripts/core/tooluse_exporter.py`):**
- Ruft `update_model_card_tooluse_fields()` mit `p1_score=_p1_mean`, `p2_score=_p2_mean` auf nach Live-Run.
- Scores aus Live-Runs werden dauerhaft in der Card gespeichert, nicht nur im Leaderboard-CSV.

**Fix 3c — `_aggregate_asset_rows()` bevorzugt Card-Werte (`scripts/core/tooluse_exporter.py`):**
- Return-Dict: `"p1_score"` und `"p2_score"` prüfen zuerst `card.get("tooluse_score_p1/p2")` als `float`.
- Fallback auf `_fmt_score(_mean(p1_scores))` nur wenn Card-Wert fehlt oder kein Float.
- Verhindert dass `make tooluse-leaderboard` (= `aggregate_from_benchmark_csvs()`) manuell validierte Scores überschreibt.

**Dokumentation synchronisiert:**
- `docs/MAINTENANCE_LOG.md`: v4.8.6-Eintrag mit allen 3 Fixes
- `docs/TOOLUSE_MODULE.md`: Card-Score-Felder (`tooluse_score_p1`/`p2`) in SSoT-Tabelle ergänzt
- `docs/SCORING_METHODOLOGY.md`: Judge-Skip-Filterhinweis unter "Core Metriken" ergänzt
- `README.md`, `PROJECT_STATUS.md`, `REF_TODO.md`: Versionsbadge + Abschluss-Eintrag auf v4.8.6 aktualisiert

**Verifikation:** 52/52 Tests grün (Teilsuite). Kein Funktions-Regressionsrisiko — alle Änderungen sind defensive Zusatz-Logik (Filter + Fallbacks), kein Verhalten geändert wenn keine Skip-Zeilen / kein Draft / keine Card-Score-Felder vorhanden.

### 2026-06-11 (Session 13) — Signal-B Cold-Start-Fix + gemma-4-26B-A4B Card finalisiert

**Signal-B Cold-Start-Fix (Option C):**
- `utils/model_utils.py` `_probe_single()`: Signal-B-Branch mit Cold-Start-Guard — `reasoning_tokens > 0` + leerer Output → `detected=False, confidence="low"` statt fälschlich `detected=True`.
- `tests/test_thinking_probe_inline_cot.py`: 2 neue Tests (Cold-Start empty + whitespace-only). 13/13 Tests grün.
- `docs/THINKING_PROBE.md`: Signal-B-Tabelle und Testanzahl aktualisiert (11 → 13).
- Hintergrund: gemma-4-26B-A4B-it-qat-ud-q4 Probe lieferte 2/3 Probes mit 0-chars-Output + reasoning_tokens=512 → Cold-Start-Fehlerkennung. Fix verhindert Fehlklassifikation.

**gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert:**
- ToolUse-Benchmark gelaufen (DGX Spark, MCP live): P1=88.33, P2=63.33, Combined=75.12 — Empfehlung: PRODUCTION (kein Hallucination-Flag).
- Card: `supports_tool_use: true`, `tooluse_tested_at: 2026-06-11T17:49:32Z`, `tooluse_score_p1: 88.33`, `tooluse_score_p2: 63.33`, `tooluse_recommendation: "PRODUCTION"`, `card_status: "complete"`.
- Nebenbeobachtung: `tooluse_exporter.finalize_model()` hat `update_model_card_tooluse_fields()` still-silently nicht in die Card geschrieben (Ausnahme auf DEBUG-Level abgefangen). Manueller Fallback via direktem Python-Call war nötig.

**Verifikation:** 72/72 Thinking-Probe-Tests grün.

### 2026-06-11 (Session 12 cont.) — Small-Model-Token-Budget + Card-Fixes

**Anlass:** Systematische Truncations bei `documentation_quality_005` für Gemma-4-12B GGUF-Modelle (token budget exhaustion). Zusätzlich: 2 neue Draft-Cards mit TODO-Placeholdern + fehlenden Sampling-Keys blockierten Tests.

**Small-Model-Token-Budget-Feature:**
- `benchmark_config.yaml`: Neuer Block `token_budgets_small_models` mit erhöhten Budgets für Small-Modelle:
  - `documentation_quality: 8000`, `code_quality: 8000`, `ux_writing: 5000`, `content_transformation: 5000`, `cli_benchmark: 5000`
- `utils/model_utils.py` `resolve_token_budget()`: Neuer Branch nach `thinking_optional`-Check — greift nur für **nicht-reasoning** Modelle der Size-Classes Nano/Edge/Desktop/Workstation. Erhöhtes Budget überschreibt Standard-Budget nur wenn `_small_budget > tokens`.
- `utils/scoring/judge_evaluator.py`: Injiziert `small_model_token_context`-Dict in Judge-kwargs wenn Small-Modell (nicht-reasoning) + erhöhtes Budget aktiv.
- `utils/scoring/llm_judge/judge_prompt_builder.py`: Nimmt `small_model_token_context` entgegen → fügt Prompt-Note ein: Judge soll Komplettheits-Lücken nicht bestrafen.

**Pitfall erkannt (gemma-4-12b):** `thinking_probe_detected=True` → nutzt bereits 12000-Token-Reasoning-Budget → NOT betroffen vom Small-Model-Branch. Small-Model-Budget nur für echte Instruct-Modelle ohne Reasoning.

**Card-Fixes (2 neue Draft-Cards):**
- `anthropic_claude-haiku-4-5.json`: Vollständig ausgefüllt basierend auf `claude-haiku-4-5-20251001.json` — `weights_license_tier: proprietary`, Sampling-Keys ergänzt, `card_status: complete`.
- `gemma-3-12b-it-spark.json`: Vollständig ausgefüllt basierend auf `gemma-3-12b-it.json` — `weights_license_tier: restricted-weights`, Sampling-Keys ergänzt, `card_status: complete`. Probe-Ergebnis (`thinking_probe_detected: true`, medium confidence) beibehalten.

**Config-Änderungen:**
- `config/provider_config.yaml`: Gemma 3 12B IT Q4_K_M + Q8_0 für DGX Spark aktiviert (auskommentierte Einträge reaktiviert als `gemma-3-12b-it-spark` + `gemma-3-12b-it-q8-spark`).
- `config/web_export_blacklist.yaml`: 5 Modelle blacklisted — `qwen3-coder-next-q8`, `qwen3_5-35b-a3b-q8`, `qwen3_5-4b-q6`, `gemma-4-12b-it-ud-q4_k_xl`, `gemma-4-12b-it-ud-q8`.

**Sonstiges:**
- `outputs/audit_logs/gpt-5.4-nano/` → `gpt-5_4-nano/` umbenannt (`_safe_name`-Konformität, Test `test_audit_logs_dirs_use_safe_name`).

**Verifikation:** **801/801 Tests grün** (vorher 2 Failures: taxonomy_placeholder + sampling_defaults).


### 2026-06-11 (Session 12) — LLM Judge Coverage Audit + Cleanup

**Anlass:** User-Auftrag: Leaderboard auf vollständige Test-Abdeckung und LLM Judge Coverage prüfen, fehlerhafte Einträge identifizieren und für Re-Test bereinigen.

**Analyse:**
- Ausgangslage: 9 Modelle mit LLM Judge Coverage < 100%, 2 Modelle mit Tests Run < 43
- Judge-applicable Modules (aus `benchmark_config.yaml`): `code_quality`, `ux_writing`, `documentation_quality`, `content_transformation`, `cultural_intelligence`, `cli_benchmark`, `reasoning`
- tooluse001-006 + political_compass: kein Judge erwartet → keine Coverage-Relevanz

**Ursachen für Coverage-Lücken (3 Kategorien):**
1. **status=error** — Request timed out / Test execution failed (hermes, gemma-q6, glm-5-20260211)
2. **status=success / finish_reason=error** — widersprüchliche Flags (magistral-small reasoning_metacog_002–005, qwen3.5-397b tooluse001)
3. **success/no-judge** — Modell lief erfolgreich, aber Judge-Phase hat das Asset nicht evaluiert (ux_writing_002/003/005, documentation_quality_004/005, code_quality_001, cultural_intel_003/005, reasoning_metacog_001)

**Besonderer Fall glm-5-20260211:** 21 stale Error-Rows aus 3 vollständig fehlgeschlagenen Runs (code_quality/02462f0118de, reasoning/ae40611153b3, ux_writing/c5d141923b7e) — neuere erfolgreiche Runs existierten bereits, aber Altlasten zogen Coverage auf 95% runter.

**Cleanup:**
- **46 Einträge entfernt** aus 3 CSVs (12 local, 26 cloud, 8 commercial)
- Backups: `*.bak_judge_cleanup_20260611_073204`
- Leaderboard neu generiert: Coverage **100% bei allen 94 Modellen**

**Offene Re-Tests (10 Modelle mit Tests Run < 43):**
| Modell | Tests Run | Fehlende Assets |
|---|---|---|
| hermes-4.3-36b-q6 | 37/43 | code_quality_001, doc_003/004, wcag_audit, security_audit |
| magistral-small-latest | 38/43 | reasoning_metacog_001–005 |
| gemma-4-12b-it-ud-q6_k_xl | 39/43 | ux_writing_002/003/005, asset_001_error_messages, asset_5b |
| gpt-5_5 | 41/43 | code_quality_001, documentation_quality_004 |
| z-ai/glm-5-20260211 | 41/43 | cultural_intel_003/005 |
| gemma-4-12b-it-ud-q8_k_xl | 42/43 | ux_writing_002 |
| qwen/qwen3.5-397b-a17b | 42/43 | cultural_intel_005, tooluse001 |
| gemma-4-12b-it-ud-q4_k_xl | 42/43 | documentation_quality_005 |
| z-ai/glm-4.7 | 42/43 | cultural_intel_003 |
| magistral-medium-latest | 42/43 | ux_writing_002 |

**Pitfall erkannt:** `cultural_intel_003` und `cultural_intel_005` fehlt systematisch bei mehreren Modellen (glm-4.7, glm-5-20260211, qwen3.5-397b-a17b) → möglicherweise spezifische Asset-Probleme in diesen cultural_intelligence-Aufgaben, die Judge-Evaluation verhinderten. Beim Re-Run beobachten.


### 2026-06-10 (Session 10) — CHANGELOG-Abschluss + Pricing-Update + Commit

**Anlass:** Memory Bank aktualisieren, uncommittete Änderungen committen, Workspace aufräumen.

**Analyse:** 25 modifizierte Dateien + 1 ungetrackte Datei (`scripts/update_model_pricing.py`). CHANGELOG hatte v4.7.9–v4.8.2 aber keine Einträge für ToolUse-NaN-Fix (Session 7), Backup-Audit (Session 9) oder Pricing-Update.

**Ergänzte CHANGELOG-Versionen:**
- **v4.8.3** — ToolUse P1/P2 NaN-Bug (unified_runner flat-column, tooluse_exporter fallback, run_score_benchmark CRUCIBLE_DELEGATE_PARENT, mcp_config idle_timeout=0)
- **v4.8.4** — Backup-System-Audit (cleanup_reviews SSoT, test_backup_targets Lücke, BACKUP_STRATEGY.md Abschnitt 4.3)
- **v4.8.5** — Pricing-Update (update_model_pricing.py NEU, 11 Modellkarten: gpt-4o-mini, gpt-5, gpt-5-mini, grok-3/mini, magistral-medium/small, mistral-large-2411/2512, mistral-medium-3-5, qwen3-coder-next-q8)

**Nicht-Bug-Befunde:** `update_model_pricing.py` war ungetrackt (nicht temporär — legitimes Wartungsskript zum Committen).

**Verifikation:** CHANGELOG vollständig v4.7.9–v4.8.5. Alle Dateien committed.


### 2026-06-10 (Session 9) — Backup-System-Audit + SSoT-Fixes

**Anlass:** Prüfung ob Backup-Skripte mit den refaktorierten Skript-Funktionen (Phase 27) übereinstimmen.

**Analyse-Ergebnis:** Makefile und Kern-Skripte korrekt. 3 Abweichungen gefunden:

1. **`scripts/maintenance/cleanup_reviews.py`** — importierte `REVIEWS_KEEP_PER_CATEGORY` aus `utils/backup_targets.py` (SSoT) **nicht**. Hardcoded `[1:]` in 3 `to_delete.extend()`-Aufrufen. Fix: Import hinzugefügt, `[1:]` → `[REVIEWS_KEEP_PER_CATEGORY:]`.

2. **`tests/test_backup_targets.py`** — Test-Lücke: `audit_logs_legacy_backup_*` fehlte in der `required`-Menge von `test_build_tar_excludes_contains_critical_patterns`. Fix: Pattern ergänzt.

3. **`docs/BACKUP_STRATEGY.md` Abschnitt 4.3** — Zeigte vereinfachtes, veraltetes Makefile-Recipe:
   - Falscher Skript-Pfad: `cleanup_runs.py --keep` statt `make clean-runs` (→ `clean.py --runs`)
   - Fehlende tar-Excludes (`.DS_Store`, `audit_logs_legacy_backup_*`, `audit_logs_spurious_archive`, `audit_logs.zip`, `model_cards_backup_*.tar.gz`, `model_cards_spurious_archive`, `outputs/temp/session_*.json`)
   - Fehlende Post-Backup-Schritte: `clean-bak`, `clean-reviews FORCE=1`, `prune-orphans FORCE=1`
   - Neuer Hinweis: Exclude-Liste muss synchron mit `build_tar_excludes()` gehalten werden

**Verifikation:** 28/28 Tests grün (`test_backup_targets.py` + `test_cleanup_reviews.py`).

**Nicht-Bug-Befund:** Makefile hatte `--exclude='tooluse_unreachable_*.json'` bereits — frühere Analyse war durch abgeschnittene Search-Ergebnisse fehlerhaft.


### 2026-06-10 (Session 7) — ToolUse P1/P2-NaN-Bug + Memory-Bank-Update

**Anlass:** qwen3-coder-next-q8 zeigte nach erfolgreichem ToolUse-Lauf (6/6 Tests, live MCP) `P1=NaN`, `P2=NaN`, `mcp_mode=mock` im Leaderboard. Combined-Score (74.62) war korrekt.

**Root Cause:** `_aggregate_asset_rows()` in `scripts/core/tooluse_exporter.py` las P1/P2 aus `score_contributions`-Feld. Seit Writer-Redesign (post-commit d82996f) schreibt `_build_result_envelope()` in `unified_runner.py` dieses Feld NICHT mehr → bei neuen CSV-Zeilen leer. Combined hatte separaten Fallback via `total_score`, P1/P2 hatten keinen → NaN.

**Drei Fixes:**
1. **`scripts/core/unified_runner.py` `_build_result_envelope()`:** ToolUse-Felder als flache CSV-Spalten aus `exec_result.data` promoten (Duck-Typing: `"p1_score" in exec_result.data`). Felder: `p1_score`, `p2_score`, `combined_score`, `mcp_mode`, `tool_call_valid`, `tool_call_attempts`, `mcp_latency_s`, `call1_time_s`, `call2_time_s`, `total_time_s`, `call1_tokens`, `call2_tokens`, `hallucination_flag`.
2. **`scripts/core/tooluse_exporter.py` `_aggregate_asset_rows()`:** Flat-Column-Fallback nach `score_contributions`-Parsing; Boolean-Konvertierung; `mcp_mode`-Fallback via `row.get("mcp_mode") == "live"`.
3. **`benchmark_scores/tooluse_leaderboard.csv`:** Direkt-Patch für qwen3-coder-next-q8 (p1=90.00, p2=59.17, combined=74.62, mcp_mode=live, hallucination_flag=true). Sovereignty Gap neu berechnet: +0.40.

**Verifikation:** `benchmark_leaderboard.csv` neu generiert → Tool Execution: 90.00 | Synthesis Quality: 59.17 | Tool Use Score: 74.62 ✅

**Weitere Fixes dieser Session (CRUCIBLE_DELEGATE_PARENT + MCP):**
- `scripts/run_score_benchmark.py`: `CRUCIBLE_DELEGATE_PARENT` darf nur von `run_tooluse_benchmark.py` gesetzt werden — wurde zu früh gesetzt, MCP wurde nie gestartet
- `cruciblemark-mcp/config/mcp_config.yaml`: `idle_timeout_seconds: 0` (deaktiviert), damit GGUF-Modelle (Ladezeit bis 420s) nicht disconnecten
- `benchmark_config.yaml`: `token_budgets.cultural_intelligence: 500→1000` (Gemma-4-12B + NVIDIA Nemotron hatten Score=0)

**Memory-Bank-Update (diese Session):**
- `reference/pitfall-diagnoses.md`: P1/P2-NaN-Abschnitt
- `reference/data-schema.md`: `tooluse_leaderboard.csv` — Flat-Column-Schema dokumentiert, `score_contributions`-Deprecation vermerkt
- `systemPatterns.md`: 4 neue Pitfall-Einträge (`score_contributions` deprecated, `not in dict`-Pitfall, CRUCIBLE_DELEGATE_PARENT, MCP idle_timeout)
- `activeContext.md`: Letzte Änderungen + qwen3-coder-next-q8 als abgeschlossen markiert


### 2026-06-10 (Code-Review-Session) — 3 Bugfixes in unified_runner.py

**Anlass:** Vollständige Codeanalyse des Benchmarksystems nach Überarbeitungen.

**Gefundene + behobene Bugs (alle in `scripts/core/unified_runner.py`):**

1. **Double-Get `self.local_csv` (Zeile 88-93):** `config.get("output", {}).get("output", {})` — doppelter Key führte dazu, dass `local_models_csv`-Pfad nie aus der Config gelesen wurde. Fallback-Wert stimmte zufällig überein → kein sichtbarer Fehler, aber Config-Änderungen würden ignoriert. Fix: inneres `.get("output", {})` entfernt.

2. **`_probe_llamacpp_server` immer falsches Modell:** `getattr(self, "model", "")` → immer `""` (kein solches Attribut). Fix: `current_model`-Parameter addiert, `_local_memory_reset` reicht das laufende Modell durch. Betrifft Memory-Reset-Probe zwischen Tests bei llamacpp_spark.

3. **`calculate_score_contributions` mit falscher Eingabe:** `calculate_score_contributions(score, asset_cfg)` wo `score = exec_result.data` kein `percentage`-Feld hat → `routine_contribution = 0.0` und `reasoning_contribution = 0.0` immer. Fix: `calculate_score_contributions(result, asset_cfg)` — verwendet `result["percentage"]` (Regex-Score), wird bei Hybrid-Scoring korrekt durch `judge_evaluator.py` überschrieben.

**Nicht-Bug-Befund:** Judge-Applicability für reasoning-Modul war KEIN Bug — `load_active_benchmarks` setzt `benchmark_info["id"] = registry_key = "reasoning"`, passend zu `applicable_modules`.

**Memory-Bank-Update:** `reference/data-schema.md` Token-Budget-Tabelle synchronisiert (war veraltet).

**Tests:** 785/785 grün (keine Regression). 1 pre-existing SyntaxWarning in `utils/model_utils.py:89` (unverändert).


### 2026-06-10 (Session 5) — Draft-Card-Pitfall im Leaderboard behoben

**Symptom:** Neue Modelle (z.B. `gemma-4-12b-it-ud-q8_k_xl`) erschienen im Leaderboard mit `Model Name="TODO"`, `Version="k.A."` und falschem `Type="Open Weights"` (statt Restricted).

**Root Cause:** `make benchmark` erstellt via `ensure_card()` automatisch eine Draft-Card mit `display_name="TODO"`, `model_version=null`, `card_status="draft"`. `make leaderboard` liest diese Felder 1:1 aus der Card (SSoT) und gibt die Platzhalter aus. `make model-cards` regeneriert nur das Template — befüllt keine Felder.

**Fix:** `gemma-4-12b-it-ud-q8_k_xl.json` manuell befüllt (analog `q6_k_xl.json`), Card-Index rebuildet, `make leaderboard` neu ausgeführt. Rank 50 zeigt jetzt korrekten Display Name, Version `4 (Q8_K_XL GGUF)/M4APL`, Type `Restricted Weights`.

**Lessons:**
- `make leaderboard` funktioniert korrekt — die Card-SSoT-Architektur macht keine Halluzinationen
- Der "TODO" im Output war 1:1 die Draft-Card
- `make model-cards` ist irreführend benannt — der Befehl erstellt nur Templates, NICHT vollständige Cards
- **Detection:** `grep "TODO" benchmark_scores/benchmark_leaderboard.csv` findet betroffene Einträge
- Pitfall-Diagnose ergänzt in `reference/pitfall-diagnoses.md`

**Tests:** 57/57 grün in `test_generate_model_cards` + `test_card_template` + `test_card_first_probe_trigger`.


### 2026-06-10 (Session 4) — generate_model_cards.py an Validate-Konvention angeglichen

**Scope:** Strukturelle und stilistische Anpassung des Card-Generators an die Architekturregeln, die in `validate_cards.py` (Phase 24, a74c367) etabliert wurden. Keine funktionalen Änderungen am `ensure_card()`-Verhalten.

**Was geändert wurde:**
- **`scripts/analysis/generate_model_cards.py` (119 → 332 Zeilen):**
  - Sektionen-Reihenfolge: Konstanten → Dataclasses → Helper → Public API → Format-Funktionen → main() (analog `validate_cards.py`)
  - Neue Dataclasses `CardCreationIssue` + `CardCreationReport` mit strukturiertem `action` (`created`/`rebuilt`/`skipped`/`failed`) und `is_success`-Logik
  - Helper-Funktionen mit Underscore-Prefix: `_is_helper_file`, `_read_existing_card`, `_resolve_target_path`, `_build_creation_plan`, `_execute_creation`, `_prompt_for_model_id`
  - Public API: `create_card()`, `create_all()` (analog `validate_card`, `validate_all`)
  - Format-Funktionen: `format_text_report()`, `format_json_report()`
  - CLI-Konsolidierung: `--card-type`, `--model-id`, `--provider`, `--force`, `--interactive`, `--json` (statt verstreutem `--model`, `--update`, `--yes`, `--dry-run`)
  - **`--update` Flag entfernt** — duplikativ zu `sync_cards.py`, SRP-Verstoß. User-Hinweis im Modul-Docstring.
  - **Provider-Card-Erstellung** gibt sauber Exit 2 mit klarer Fehlermeldung zurück (war vorher stillschweigend out-of-scope)
  - Exit-Code-Logik: 0=OK, 1=Issue, 2=Programmfehler — dokumentiert im Docstring
- **`utils/card_template.py`:** Neue SSoT-Funktionen `cards_dir()` + `rebuild_card_index()` (vorher nur `rebuild_provider_index()` für Provider, jetzt symmetrisch für beide Typen). `JSONDecodeError` wird wie in `provider_card_template.py` mit `logger.warning` geschluckt (nicht fatal).
- **`tests/test_generate_model_cards.py` (NEU, 25 Tests):** Deckt `_is_helper_file`, `_build_creation_plan`, `CardCreationReport`-Issue-Logik, `create_card` (create/skip/rebuild/provider-Pfad), Format-Reporter (text/json), `cards_dir`/`rebuild_card_index` SSoT ab.
- **`docs/CARD_MANAGEMENT.md`:** CLI-Beispiele aktualisiert (TODO — folgt in Folge-Session)

**Tests:** **726/726 grün** (vorher 701, +25 neue). Ruff clean. Mypy keine neuen Fehler (2 pre-existing in `utils/model_utils.py:1754-1757` unverändert).

**Lessons:**
- `_index.json` lokal zu rebuilden war bisher Duplikat-Logik zu `rebuild_provider_index()`. Auslagerung als SSoT in `utils/card_template.py` ist vorbildlich für künftige SSoT-Brücken.
- Mix aus `print()` und `logger.*()` im alten Skript war inkonsistent — `logger` für Dev-Output, `print()` nur für finale User-Output ist die klare Linie.
- `--update` (Sync) im Create-Skript war ein historischer Workaround — durch saubere SRP-Trennung entfällt die Verlockung, beides zu vermischen.


## v4.7.4 (2026-06-10) — Heartbeat-Configurable

**Scope:** Hardcodiertes 60s-Heartbeat-Intervall aus `unified_runner.py` in `benchmark_config.yaml` verlagert.

- `_get_heartbeat_config()` mit Defensiv-Fallback (Block fehlt/nicht-Dict/non-numeric/≤0 → `(True, 60.0)`)
- `enabled=false` → `heartbeat_thread = None` Sentinel für `finally`-Block
- 17 neue Tests (`test_unified_runner_heartbeat.py`): Defaults, explicit, partial, zero/negative, non-numeric, non-dict, disabled-thread
- Doku: `docs/BENCHMARK_SCRIPT_OVERVIEW.md §6` "Runtime Feedback (Heartbeat)"
- 603/603 Tests grün
- **Details:** `reference/heartbeat-v474-detail.md`

## v4.7.3 (2026-06-10) — Thinking-SSoT-Auflösung + Doku-Sync

**Scope:** SSoT-Auflösung für Thinking-Erkennung (Card-Probe + Override), Runner-Consumer-Anbindung via `provider=` kwarg, Doku-Sync.

- `utils/model_utils.resolve_effective_thinking()` — SSoT-Auflösung (Override > Card-Probe > None) mit Audit-Trail
- `_is_override_active()` — Override-Validierung (bool, reason-Pflicht, active_until-UTC)
- `resolve_token_budget(..., *, provider=None)` — neuer kwarg
- `base_runner.py:121` reicht `provider=provider` durch
- 24 + 17 = 41 neue Tests, **634/634 grün in 2.11s**
- Doku: 6 Dateien aktualisiert (THINKING_PROBE.md NEU, CHANGELOG, ARCHITECTURE, CARD_MANAGEMENT, CLAUDE.md Pitfall, Memory-Bank)
- **Lessons:** `docs/THINKING_PROBE.md` war im v4.7.2-CHANGELOG angekündigt, fehlte aber → beim Schreiben als NEU markieren

## Offene Tasks

- [ ] **[BACKLOG] Reasoning-Aware-Benchmark (Option C)** — zurückgestellt 2026-06-10
  - Re-Aktivierungs-Bedingung: Sobald Uri-Vergleich um "Reasoning-Fairness" erweitert werden soll
  - `force_off` via `thinking_override.value=false` bereits implementiert; `force_on` fehlt
  - **Details:** `reference/decisions-log.md` (Reasoning-Backlog-Sektion)

- [ ] **5 echte Test-Lücken schließen** (Phase 8 Befund)
  - Kimi K2.6 (40/43), DeepSeek V4 Pro (42/43), Qwen 3.5 397B A17B (40/43), MiniMax M2.7 (42/43), GLM-4.7 (42/43)
  - Fix: `make benchmark-auto` (Auto-Bench-Fill-Logik)

- [ ] **PC-Re-Run fortsetzen** — 31 Modelle ohne gültigen Leaderboard-Eintrag (letzter Lauf abgebrochen, Exit 130)

- [x] **Qwen-Retest nach `--reasoning off` Fix** — 7 Modelle erfolgreich re-gerunnt (2026-06-07/08). Zombie-Eintrag `asset_001_wcag_audit` / `qwen3_5-35b-a3b-q8` bereinigt (2026-06-10). Alle 13 lokalen Qwen-Modelle zeigen 43/43 im Leaderboard.

- [x] **5 weitere ToolUse-Sanierungen** — abgeschlossen (2026-06-10, Session 8)
  - deepseek/deepseek-v4-pro, gemini-3_5-flash, mistral-large-2512, mistral-small-2603, nousresearch/hermes-4-405b: bereits gültige `live`-Daten mit korrekten Flat-Columns ✅
  - deepseek-r1:8b: mock-Zeile + Korrupte Zeilen 2–5 + gpt-5_5 (6 Errors) aus `tooluse_leaderboard.csv` gelöscht → Re-Run durch User nötig
  - `benchmark_leaderboard.csv` neu generiert — gpt-5_5 zeigt korrekt `–,–,–` für ToolUse

- [x] **heritage_ids-Fallback** in `generate_review.py` + `web_export.py` — **Commit 81b8cd4**

- [ ] **Re-Run magistral-small / magistral-medium** (FORCE=1) für reasoning_logic, ux_writing, code_quality / documentation_quality

- [ ] **language_consistency** als eigene CSV-Spalte im Leaderboard (Erweiterung)

- [ ] **ct_005 Phase-2** Body-Word-Parser (fragile Extraktion, nicht zeitkritisch)

- [ ] **Phase 4: Finale E2E Systemtests und CI/CD Review**

- [ ] **LLM Judge: Batch-Mode** (Phase 3.5)

- [ ] **Leaderboard-Refactoring Phase 9–12** (Asset→Category-Registry, SSoT-`expected_assets`, ehrliches `is_complete`, candidates-Slugify, Integration-Tests) — auf User-Freigabe warten

### 2026-06-10 (Session 2) — Card-First-Probe Bug + q6_k_xl 5B-Sanierung

**Bug-Fix in `scripts/core/unified_runner.py`:** `_read_card_probe_state` Zeile 186 prüfte `"thinking_probe_detected" not in loaded`, aber `ensure_card()` erzeugt Draft-Cards mit explizit `None`-Wert. Fix: `loaded.get("thinking_probe_detected") is None` (1 Zeile).

**Effekt:** Gemma-4-12B-Modelle (und alle Draft-Card-Modelle) bekommen beim nächsten Lauf automatisch eine echte Thinking-Probe → 5x-Reasoning-Budget aktiviert (8192 → 40960 Tokens).

**Tests:** 7 neue Unit-Tests in `tests/test_card_first_probe_trigger.py` (alle 4 Probe-States: null/missing/True/False + 3 Edge-Cases). 75/75 Tests grün in angrenzenden Test-Dateien. Ruff clean, Mypy keine neuen Fehler.

**CSV-Sanierung:** `benchmark_scores/local_models_benchmark.csv` — 1 fehlerhafte Zeile entfernt (asset_5b_complex_reasoning_chains für gemma-4-12b-it-ud-q6_k_xl, Status=error, "Test execution failed"). Backup: `local_models_benchmark.csv.backup_q6_5b_fix_20260610_092347`. 22 → 21 Zeilen für q6_k_xl. Alle anderen 21 Werte (code_quality, cli, reasoning_001/5a/5c/5d/5e, metacog_001-005) bleiben erhalten.

**Pitfall-Diagnose:** `memory-bank/reference/pitfall-diagnoses.md` — neue Sektion „Card-First-Probe wird durch `null`-Wert in Draft-Card umgangen (2026-06-10)".


### 2026-06-10 (Session 3) — Test-Isolation via conftest.py

**Root-Cause:** Zwei Worker-Tests riefen `worker.main()` direkt auf und monkeypatchten `CARD_DIR` nicht → `discover_models()`, `enforce_card_first()` und Card-Lookups in `UnifiedBenchmarkRunner` griffen via `CARD_DIR = Path("benchmark_scores/model_cards")` auf den ECHTEN Ordner zu. `ensure_card()` legte für unbekannte Test-Model-IDs (`m1`, `m2`, `True`) Stub-Karten als Leichen an.

**Fix:**
- Neue Datei `tests/conftest.py` mit `autouse=True`-Fixture `_isolate_card_dir`:
  - `monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)` für jeden Test
  - Custom-Marker `pytest.mark.uses_real_cards` für Opt-Out (z.B. `test_resolve_canonical_model_id.py` mit glob-fallback Card-Alias)
  - Marker-Registrierung via `pytest_configure()` → keine `PytestUnknownMarkWarning`
- `tests/test_resolve_canonical_model_id.py` mit `pytestmark = pytest.mark.uses_real_cards` markiert
- Bestehende Fixtures (`test_enforce_card_first.py`, `test_id_ssot_invariants.py`, `test_benchmark_auto_untested_tooluse.py`) patchen dasselbe Attribut auf `tmp_path` — identische Konvention, kein Konflikt (monkeypatch restauriert am Ende alle setattrs auf den Originalwert)

**Verifikation:** 4 betroffene Tests grün, voller Test-Run 15 failed, 900 passed — exakt gleiche Failures mit und ohne `conftest.py` (0 Regressionen, 15 pre-existierend: 14 MCP-network + 1 audit-logs safe-name). `ls benchmark_scores/model_cards/ | grep -E "^(m1|m2|True)\.json"` ist nach Test-Run LEER.

**Pitfall-Diagnose:** `memory-bank/reference/pitfall-diagnoses.md` — neue Sektion „Test-Card-Leichen in `benchmark_scores/model_cards/` durch unautouse-Fixture (2026-06-10)".
