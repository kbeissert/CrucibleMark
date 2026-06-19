# System Patterns

Architektur-Regeln + aktuelle SSoT-Brücken (One-Liner). Details: `reference/data-schema.md`, `reference/pitfall-diagnoses.md`.

---

## 🛑 4 Architektur-Regeln

1. **Separation of Concerns:** Measurement = autonom/ausfallsicher. Publishing = strikt offline.
2. **SSOT/DRY/SRP:** Eine Funktionalität = ein Modul. Fail-Fast ohne versteckte Fallbacks (`ValueError` bei falscher Config). Import statt Duplikation.
3. **Config-Driven, No Magic Numbers:** Alle Regeln/Zahlen/Limits in YAML. CC ≤ 12 (`ruff.toml` C901).
4. **Anti-God-Script:** Logische Submodule auslagern, Haupt-Skript bleibt schlank.

---

## SSoT-Brücken (One-Liner + Datei)

| Brücke | SSoT-Speicherort | Hot-Aufruf |
|---|---|---|
| **Token-Budget** | `benchmark_config.yaml → token_budgets` + `token_budgets_reasoning_models` | `resolve_token_budget()` → `min(budget, provider_num_predict)` |
| **Thinking** | Card `thinking_probe_detected` + optional `thinking_override` (Provider-Card) | `resolve_effective_thinking()` Priorität: Override > Probe > None |
| **Model-Identität** | Card `model_id` ist einziger Identifier | `resolve_canonical_model_id()` (5-Level-Lookup) |
| **Model-ID als Kommunikations-Anker** | Card `model_id` / `raw_model_id` | Alle CSV-/Leaderboard-Lookups via `model_id`. `raw_model_id` lesen, dann `slugify()` für Format-Matching. NIEMALS Display-Name für Lookups verwenden. |
| **Card-ID-Pipeline** | `{base}--{shortcode}` Schema | `build_card_id()`, `resolve_unique_card_id()` |
| **Card-First CSV-Senke** | `result_manager.save_results()` | `enforce_card_first()` (Draft wenn fehlt, KEIN Hard-Fail) |
| **Hardware-Profile (Review-Kontext)** | `provider_config.yaml → <provider>.hardware_profile` → `benchmark_config.yaml → runner_environment.profiles` | `_get_hardware_profile_for_model()` in `generate_review.py`; `get_editor_prompt_injection(hardware_profile_key=...)` |
| **Modell-Kategorie** | Card `weights_license_tier` | `get_model_category()` (3 Tiers: `proprietary`/`restricted-weights`/`open-weights`) |
| **Provider-Shortcodes** | `_PROVIDER_SHORTCODES` + `short_code` in Config | `API`/`OR`/`GR`/`LCL` — alle lokalen Provider (ollama, llamacpp, llamacpp_spark) → `LCL` |
| **Deployment-Category** | `_PROVIDER_DEPLOYMENT_CATEGORY` in `model_utils.py` + `deployment_category` in `provider_config.yaml` | `get_deployment_category(provider)` → `"api"` / `"cloud"` / `"local"` |
| **Hardware-Profile (Deployment-Badge)** | `_PROVIDER_HARDWARE_PROFILES` in `model_utils.py` + `hardware_profiles` in `provider_config.yaml` | `get_hardware_profile(provider)` → `"m4_macbook_pro_metal"` / `"dgx_spark_cuda"` / `"rtx4070_cuda"` / `None` |
| **Sampling-Defaults** | `providers.local.config.llama_cpp_defaults` | 7 Parameter, Pro-Modell-Override schlägt Default |
| **1-Klasse-pro-Hardware** | `LlamaCppBaseClient` + Subklassen | Auto-Registry via `__init_subclass__` mit `PROVIDER_NAMES` |
| **Tri-State Tool-Use** | Card `supports_tool_use`: `true`/`false`/`"untested"` | `normalize_supports_tool_use()` Helper |
| **Card-Research MCP Tool-Use** | `manage_model_cards.py` → MCP Server `:8765` (JSON-RPC 2.0 HTTP POST) | `--tooluse` + `--mcp-url`; `_call_mcp_tool()` POST `tools/call`; `_parse_tool_call()` extrahiert `{"tool_call": {...}}`; `_extract_tool_content()` liest Transcript |

**Code-Beispiele und Felder:** `reference/data-schema.md`. Pitfalls: `reference/pitfall-diagnoses.md`.

---

## Thinking-Override-Schema

```yaml
thinking_override:
  value: false                 # bool (Pflicht)
  reason: "Cost-Benchmark: CoT-Suppression"   # str (Pflicht)
  active_until: "2026-12-31"   # ISO-8601 (optional)
```

Aktivierung: `value` bool, `reason` nicht whitespace-only, `active_until` in der Zukunft.

---

## Konventionen

- **Naming:** BEM (CSS) / snake_case (Python) / kebab-case (YAML-Keys)
- **Commits:** Conventional Commits (feat/fix/chore/docs)
- **Doku:** Deutsch für Kommentare/Docs, Englisch für Code
- **Linter:** Pylance + Pylint + Ruff, ≥ 9.5/10 für Core-Module
- **Tests:** pytest `-v --tb=short`, Fixtures in `conftest.py`
- **Type-Hints:** immer, mypy-kompatibel
- **Errors:** Niemals bare `except:`, `logging.exception()`, Custom Exceptions

---

## Pitfalls (Goldene Regeln, Kurz-Liste)

- **Race-Condition:** NIEMALS während laufendem Benchmark Core-Module modifizieren
- **Python 3.14 `sys.path`:** `ROOT_DIR = Path(__file__).resolve().parent.parent.parent` vor Package-Imports
- **Provider-Inferenz:** `model_id` muss Slash-Form (z.B. `nvidia/nemotron-3-ultra`) für exakten Config-Lookup haben
- **Mypy `pandas.isna()`:** None-Check vor `str(val).strip()` — sonst `"nan"`-Strings
- **`assertIsNotNone()` reicht Pylance nicht:** expliziter Cast-Kommentar
- **Pylint W0611:** Jeder neu hinzugefügte Import muss sofort verwendet werden
- **`score_contributions` deprecated:** Seit Writer-Redesign (d82996f) leer in neuen CSV-Rows → NICHT als einzige Datenquelle für ToolUse-Metriken verwenden. Neue Pattern: Flat-Columns (`p1_score` etc.) direkt in Zeile.
- **`not in dict` ≠ Wert fehlt:** `ensure_card()` setzt alle Felder auf `None` → `key not in d` ist `False` trotz fehlendem Wert. Immer `d.get(key) is None` prüfen.
- **CRUCIBLE_DELEGATE_PARENT:** Darf nur von `run_tooluse_benchmark.py` gesetzt werden — nie von `run_score_benchmark.py`. Sonst wird MCP nie gestartet und alle ToolUse-Tests schlagen fehl.
- **MCP `idle_timeout_seconds: 0`** deaktiviert den Timeout — nötig für GGUF-Modelle (Ladezeit bis 420s).
- **Display-Name ≠ Model-ID für Lookups:** PC-Leaderboard, Tooluse-Leaderboard, Blacklist — immer `raw_model_id` aus der Card verwenden. `slugify(raw_model_id)` für Format-Anpassungen. Display-Namen sind UI-only.
- **Tooluse-Leaderboard-IDs sind Ollama-Format** (`gemma3:12b`, `qwen3:14b`) — nicht CrucibleMark-IDs. Im per-model-Review-Loop können sie nicht auf Audit-Log-Slugs gemappt werden → Tooluse-Schritt muss nach dem Loop mit `model=None` separat laufen.
- **Hardware-Profil-Lookup:** `provider_config.yaml → <provider>.hardware_profile` ist der SSoT-Key. Nie aus `active_profile` oder Environment ableiten — das ist das Test-System, nicht das Hardware-Profil des getesteten Modells.
- **PC-Ghost-Model durch Datum-Normalisierung (2026-06-13):** `base_runner.py` normalisiert Modell-IDs via `re.sub(r'-\d{8}$', '', model_id)` für den Leaderboard-Skip-Check. Wenn ein alter undatierter PC-Leaderboard-Eintrag (`z-ai/glm-5`) existiert, trifft `z-ai/glm-5-20260211` darauf → false-positive Skip, kein neuer PC-Run. Fix: `--force`-Flag beim PC-Benchmark-Re-Run. Danach alten `k.A.`-Entry aus `political_compass_results.csv` manuell löschen.
- **Vendor-Card-Generator erzeugt Duplikate (2026-06-13):** `generate_vendor_cards.py` prüft nicht auf bestehende Karten mit ähnlichem Namen. Auto-generierte Karten (`alibaba_cloud.json`, `alibaba_group_qwen_team.json`) kollidierten mit dem kanonischen `alibaba.json` — alle 3 mit identischer `api_base_url`. Symptom: mehrfache Vendor-Einträge im Web-Export. Fix: Orphan-Dateien löschen + `card_subtype: "community"` für Community-Cards setzen + Community-Filter in `web_export.py`.
- **Card-Research Tool-Use: max. 3 Runden (2026-06-19):** `Researcher._research_tooluse_one()` hat einen Hard-Cap von 3 Tool-Call-Runden. Verhindert Endlosschleifen bei kaputtem Modell (das nie mit `{"findings": ...}` antwortet). Wenn 3 Runden ohne finale Answer erreicht → Fehler, Lock bleibt offen, nächster Lauf nimmt Card im Resumption-Pfad.

Whenever a task involves refactoring, unexpected behavior, or
architecture changes: automatically load reference/pitfall-diagnosis.md before proposing any solution.


## Context Loading Rules
Before starting any task, check the task type and load accordingly:
- Refactoring / debugging / architecture review
  → load reference/pitfall-diagnosis.md
- Template or frontend work
  → load reference/data-schema.md
- New feature from roadmap
  → load reference/feature-specs.md
- "Why did we..." questions
  → load reference/decisions-log.md
Default: load nothing from reference/ unless task matches above.
