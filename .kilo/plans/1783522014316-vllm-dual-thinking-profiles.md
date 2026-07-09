# Plan: vLLM Dual-Thinking-Profile (Schnell + Thinking)

## Ziel
Ein vLLM-Container pro Modell bedient **zwei Benchmark-Profile** per-Request:
- **Standard-Profil** (`{id}`) — kein Thinking, Standard-Chat-Template
- **Thinking-Profil** (`{id}-thinking`) — Reasoning aktiv via per-Request `chat_template_kwargs`

Beide zeigen auf dieselbe TOML / denselben Container. Der Unterschied ist **nur ein per-Request-Parameter** — kein Server-Neustart beim Profil-Wechsel. Eine Model-Card pro Modell; zwei separate Leaderboard-Einträge.

## Geklärte Entscheidungen

1. **Swap-Erkennung config-basiert** — der Connector vergleicht `config:` (TOML), nicht die Profil-ID. Zwei Einträge mit gleicher `config:` → kein `swap_model`, nur per-Request-Param-Wechsel.
2. **Config-Key `enable_thinking`** — Expansion-Trigger im model_cfg (bool). Nicht `reasoning` (kollidiert mit Modul-Key `--module reasoning` und Score-Gewicht).
3. **Suffix `-thinking`** — generierte Thinking-ID = `{original_id}-thinking` (intern kanonisiert `{...}-thinking`). Konsistent mit `enable_thinking`, `thinking_probe_detected`, `thinking_mode`.
4. **Card-Zuordnung via `card_model_id`-Feld** — der generierte Thinking-Eintrag trägt `card_model_id: {original_id}`; `_find_card`/`resolve_canonical_model_id` nutzen dieses Feld für Card-Lookup. Deterministisch, kein Suffix-Stripping-Heuristik. CSV `model_id` bleibt `{...}-thinking` (eindeutiger Leaderboard-Eintrag).
5. **`max_tokens` via Provider-Default `thinking_max_tokens` + Override** — Provider-Level-Default im `vllm_spark`-Block, pro Modell via `thinking_max_tokens:` überschreibbar. Generierter Thinking-Eintrag übernimmt diesen Wert.
6. **Expansion im Config-Merge** (`config_validator.py:_load_config`, nach `config["providers"] = providers`) — einmalig, alle downstream-Konsumenten sehen zwei Einträge transparent.

## Affected Boundaries / Dateien

- `utils/config_validator.py` — neue Methode `_expand_thinking_profiles(providers)`, aufgerufen in `_load_config` nach Merge, vor `_check_duplicate_model_ids`.
- `utils/providers/vllm_base.py` — Swap-Entkopplung: `_active_config`-Tracking + config-basierter Vergleich in `_ensure_model_ready`/`start_server`/`swap_model`. KEINE neue `enable_thinking`-Mapping-Logik (per-Request-Steuerung läuft transparent über `chat_template_kwargs`, bereits in `_VLLM_EXTRA_BODY_KEYS` Whitelist `vllm_base.py:79`).
- `utils/model_utils.py` — `_find_card`/`resolve_canonical_model_id`: nutzen `card_model_id`-Feld aus model_cfg, falls vorhanden, für Card-Lookup.
- `config/provider_config.yaml` — `thinking_max_tokens`-Default im `vllm_spark`-Block; `enable_thinking: true` an Ornith-Standard-Eintrag.
- Tests: `tests/test_vllm_spark_provider.py` (Swap config-basiert), neu `tests/test_config_thinking_expansion.py` (Expansion-Logik), `tests/test_card_model_id_lookup.py` (Card-Zuordnung).
- **Remote (nicht im Git):** `~/ai/shared/configs/vllm/models/Ornith1-35B-FP8.toml` — `--default-chat-template-kwargs` entfernen.

## Implementierungsschritte

### 1. Config-Expansion (`config_validator.py`)
- Neue Methode `_expand_thinking_profiles(providers)`:
  - Iteriert nur Provider mit `api_type == "vllm"` (KRITISCH: llama.cpp hat `enable_thinking` als Server-Flag mit anderer Semantik — `provider_config.yaml:371` — NICHT expandieren).
  - Für jeden model_cfg-Eintrag mit `enable_thinking: true`:
    - Original-Eintrag: konsumiere `enable_thinking` (entferne den Key), setze explizit `chat_template_kwargs: {"enable_thinking": False}`.
    - Generiere Thinking-Eintrag: `id: {original_id}-thinking`, `name: {name} Thinking`, `config:` identisch, `card_model_id: {original_id}`, `chat_template_kwargs: {"enable_thinking": True}`, `max_tokens: {thinking_max_tokens}`, erbt alle anderen Sampling-Werte (temperature/top_p/top_k).
  - `thinking_max_tokens`-Quelle: model_cfg `thinking_max_tokens` > provider `thinking_max_tokens` > Fehler (kein Hardcoding).
- Aufruf in `_load_config` nach Zeile 60 (`config["providers"] = providers`), vor `_check_duplicate_model_ids`.

### 2. vLLM-Connector Swap-Entkopplung (`vllm_base.py`)
- Neues Instance-Attribut `_active_config: str | None`.
- In `start_server`/`_ensure_model_ready`: beim Successful-Set von `_active_model` zusätzlich `_active_config = self._config_arg(model_id)`.
- `_ensure_model_ready` (`vllm_base.py:1000`): neuer Pfad vor `swap_model` — wenn `self._active_config == self._config_arg(new_model)` UND `_is_healthy()` → **kein Swap**, nur `_resolve_sampling` (per-Request) wechselt automatisch. Re-validate via `_is_model_ready` mit `_server_model_name`.
- `swap_model` (`vllm_base.py:962`): bleibt unverändert für echte Modell-Wechsel (ungleiche `config:`).
- Backward-compat: `_active_config is None` → bisheriges Verhalten (bestehende Single-Profile-Modelle unverändert).

### 3. Card-Lookup via `card_model_id` (`model_utils.py`)
- `_find_card` und `resolve_canonical_model_id`: akzeptieren optional `provider_model_cfg`/`model_cfg`-Dict; nutzen `card_model_id`-Feld, falls vorhanden, als Card-Lookup-Basis. Fallback: bisheriges Verhalten (ID-basiert).
- Konsumenten, die model_cfg zur Verfügung haben (`find_model_in_provider_cfg`-Caller, Connector), reichen es durch. Achtung: nicht alle `_find_card`-Caller haben model_cfg → reiner Optional-Parameter, keine Pflicht.

### 4. Config-Einträge (`provider_config.yaml`)
- `vllm_spark`-Block: `thinking_max_tokens: 32768` als Provider-Default.
- Ornith-Standard-Eintrag: `enable_thinking: true` ergänzen (Trigger).
- Beispiel resultierend (nach Expansion):
  ```yaml
  # Standard-Profil (generiert nach Expansion, kein enable_thinking mehr):
  - id: ornith-1.0-35B-FP8
    config: Ornith1-35B-FP8
    chat_template_kwargs: {"enable_thinking": false}
    max_tokens: 8192
    ...
  # Thinking-Profil (generiert):
  - id: ornith-1.0-35B-FP8-thinking
    config: Ornith1-35B-FP8          # ← identisch → kein Swap
    card_model_id: ornith-1.0-35B-FP8 # ← eine Card
    chat_template_kwargs: {"enable_thinking": true}
    max_tokens: 32768                 # ← thinking_max_tokens
    ...
  ```

### 5. Remote-TOML anpassen (manuell auf GX10, nicht im Git)
- `Ornith1-35B-FP8.toml`: `--default-chat-template-kwargs '{"enable_thinking":false}'` entfernen. Sonst ist Thinking serverseitig fixiert und per-Request-Steuerung inkonsistent. Per-Request `chat_template_kwargs` gewinnt zwar, aber sauberer ohne Server-Default.

### 6. Tests
- `test_config_thinking_expansion.py`: Expansion generiert 2 Einträge aus 1; Original verliert `enable_thinking`, bekommt `chat_template_kwargs:false`; Thinking-Eintrag hat korrekte id/card_model_id/max_tokens; `api_type != vllm` wird NICHT expandiert (llama.cpp-Regression); fehlendes `thinking_max_tokens` → Fehler.
- `test_vllm_spark_provider.py`: Profil-Wechsel (gleiche `config:`) → kein `swap_model`-Aufruf; echter Modell-Wechsel (ungleiche `config:`) → `swap_model`; backward-compat (`_active_config is None`).
- `test_card_model_id_lookup.py`: `card_model_id`-Feld → Card gefunden; fehlendes Feld → bisheriges Verhalten.

## Validation
- `pytest -v --tb=short` — neue + bestehende Tests grün.
- `make validate` (Lint) exit 0.
- Backward-compat: bestehende vLLM-Modelle ohne `enable_thinking` → keine Expansion, unverändertes Verhalten (Volltest).
- Live-Smoketest (manuell): Ornith Standard-Profil → `reasoning: null` (kein Thinking); Thinking-Profil → `reasoning`-Feld befüllt. Profil-Wechsel ohne Container-Neustart (Logs prüfen: kein `swap_model`/`vllm-stop`).

## Risiken / Edge Cases
- **`api_type`-Filter zwingend** — ohne ihn würde llama.cpp's `enable_thinking: true` (Server-Flag, `provider_config.yaml:371`) fälschlich expandiert. Test deckt das ab.
- **`_check_duplicate_model_ids` nach Expansion** — darf die generierte `{id}-thinking` nicht als Duplikat des Originals flaggen (verschiedene IDs → OK; sicherstellen, dass kein anderes Modell zufällig `{id}-thinking` heißt).
- **`benchmark_auto.py` / `vllm_batch.py`** gruppieren aktuell nach model_id für Session-Management → würden Container für Standard und Thinking getrennt starten. Folgearbeit (out-of-scope für diesen Plan): Gruppierung nach `config`, sodass beide Profile in einer Container-Session ablaufen. Bis dahin: manuelle Reihenfolge (Standard-Run, dann Thinking-Run ohne Server-Stop dazwischen) oder `-thinking` zuerst.
- **Audit-Log-Dirs** — zwei Dirs (`{id}/` + `{id}-thinking/`) via `_safe_name`, profil-spezifisch. Keine Änderung nötig (gewollt: Reasoning-Content unterscheidet sich).

## Out-of-scope (später)
- **Leaderboard/CSV `thinking_mode`-Spalte** (Phase 3 der strategischen Initiative, `progress.md:57-64`) — zwei Profile erzeugen zwei Leaderboard-Einträge automatisch (via zwei CSV-IDs); Best-of-Both-Logik und `thinking_mode`-Spalte kommen später.
- **`benchmark_auto.py`/`vllm_batch.py` config-Gruppierung** — siehe Risiken; Container-Session-Optimierung für beide Profile.
- **Web-Export** — welcher der beiden Leaderboard-Einträge exportiert wird (Blacklist-Anpassung).
- **`reasoning_effort`-Abstufung (medium/high)** — Ornith-Template (Qwen3.5-MoE) unterstützt `enable_thinking` nur als bool (`chat_template.jinja:145`). Keine Abstufung möglich. Falls künftige Templates `thinking_budget` unterstützen, späterer Follow-up.
