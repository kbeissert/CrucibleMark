# Generalized Coverage Scoring + ToolUse Integration — v5.0

## Kontext

ToolUse ist als achtes Benchmark-Modul implementiert, aber mit `enable_scoring: false`
vom Total Score ausgeschlossen. Die Score-Berechnung basiert weiterhin auf den
ursprünglichen 7 Modulen. ToolUse soll als vollwertiges Scoring-Modul integriert
werden, ohne dass Benchmarks neu ausgeführt werden müssen — die Per-Asset-Daten
liegen bereits in den Benchmark-CSVs (654 Rows, `percentage` = combined_score).

Ein Audit (GLM-5.2) identifizierte zwei Probleme:
1. **Redundanz** in den Web-Frontend-Profilformeln (`agentic_execution`,
   `agentic_creative`) — `combined_score` wird alongside p1/p2 verwendet.
2. **Fehlende Datenstatus-Differenzierung** — Modelle ohne ToolUse-Daten werden
   nicht zwischen "missing" (ungetestet) und "incapable" (strukturell unfähig)
   unterschieden.

Ein Folge-Audit (Claude Sonnet 5) identifizierte ein strukturelles Problem:
Die bestehende Renormalisierungslogik in `score_calculator.py` (v3.4.3
"selbstnormalisierendes Modulgewichtungs-System") normalisiert den Total Score
nur über die tatsächlich getesteten Module. Modelle mit unvollständiger
Modul-Abdeckung werden auf 0–100 skaliert, als hätten sie alle Module absolviert.
Der ToolUse-spezifische Malus aus dem ersten Plan war nur ein Spezialfall — die
Coverage-Logik muss generalisiert auf alle Scoring-Module angewendet werden.

## Diagnose: Symptom-Quelle (Schwäche 1 aus Kritik)

**Frage:** Welches konkrete Modell stand mit unvollständiger Modul-Abdeckung weit
oben im Ranking?

**Empirische Antwort:** Keines — im Backend-Total-Score existiert das Symptom
nicht. Verifiziert gegen `benchmark_leaderboard_detailed.csv`:

- Alle 110 Modelle haben vollständige Scores für alle 7 Scoring-Module (0 Lücken)
- Top-20-Modelle: alle haben 43/43 Tests Run
- 3 Modelle mit <43/43 Tests (Gemma 4 26B-A4B: 42/43, Gemma 4 31B Creative:
  42/43, Hermes 4.3 36B: 38/43) — alle auf Rang 69-84, nicht oben
- 4 ToolUse-betroffene Modelle: Ränge 68, 103, 106, 107 — alle untere Hälfte

**Das Symptom existiert in den Web-Frontend-Agentic-Profilen** — dort sind
`agentic_execution`/`agentic_creative` Standalone-Mini-Scores aus p1/p2/
combined_score, ohne Ankerung an Total Score oder Gesamt-Abdeckung. Modelle mit
Total Score 66-69 (z.B. OpenAI o1: Rang 101, Xiaomi MiMo V2.5: Rang 86) rangieren
in den Agentic-Profilen in den Top 10.

**Scope-Entscheidung (Nutzer):** Dieser Plan behandelt ausschließlich die
Backend-Total-Score-Formel (`score_calculator.py` / CSV-Output). Die
Agentic-Profil-Ankerung ist ein separates Web-Frontend-Thema und wird hier nicht
entschieden. Task 8 reduziert sich auf reine Redundanz-Bereinigung
(`tooluse_combined` entfernen), ohne Änderung der Profil-Ranking-Logik.

**Bedeutung für den Plan:** Die Backend-Änderungen sind architektonisch korrekt
und future-proof, beheben aber kein aktuell beobachtetes Backend-Symptom. Die
einzigen aktuellen Score-Änderungen entstehen durch ToolUse-Integration
(4 Modelle betroffen).

## Formel

### Bisher (v3.4.3 — selbstnormalisierend)

```
Total Score(m) = Σ_{i ∈ present} (score_i × w_i) / Σ_{i ∈ present} w_i
```

Nenner umfasst nur Module mit Daten → Renormalisierung auf 0–100 unabhängig
von Modul-Subset.

### Neu (v5.0 — Coverage-aware)

```
Total Score(m) = Σ_{i ∈ present} (score_i × w_i) / Σ_{i ∈ present ∪ missing ∪ unknown} w_i
```

### Status-Taxonomie (6 Zustände)

| Status | Zähler | Nenner | Bedeutung |
|---|---|---|---|
| `present` | ✓ | ✓ | Modell hat ≥1 gültige Row (status ∈ `_VALID_STATUSES`) |
| `missing` | ✗ | ✓ | Keine gültigen Rows, Modul anwendbar, `capability_field` ≠ false |
| `unknown` | ✗ | ✓ | Keine gültigen Rows, `capability_field` in Model Card **ganz fehlt** (nicht explizit false) |
| `incapable` | ✗ | ✗ | `capability_field` ∈ `{False, "false", "not_applicable"}` in Model Card |
| `not_deployed` | ✗ | ✗ | Modul hat für **kein** Modell gültige Daten |
| `rolling_out` | ✗ | ✗ | Modul hat gültige Daten für **< deployment_threshold** der Modelle (aber > 0) |

**`unknown` vs `missing` — Unterschied:** Beide werden scoring-technisch gleich
behandelt (Nenner ohne Zähler = Malus). `unknown` generiert zusätzlich eine
WARNING-Logmeldung, weil das Fehlen des `capability_field` auf eine pflegebedürftige
Model Card hindeutet. So rutscht ein fälschlich als "missing" bestraftes Modell
nicht unbemerkt durch.

**`rolling_out` vs `not_deployed` — Unterschied:** Beide werden aus dem Nenner
ausgeschlossen. `rolling_out` generiert eine INFO-Logmeldung. Ein Modul mit nur
3/110 Modellen mit Daten würde sonst 107 Modelle hart bestrafen — die
Deployment-Schwelle verhindert das.

### Deployment-Schwelle (Schwäche 2 aus Kritik)

Ein Scoring-Modul gilt als `deployed` wenn `deployed_count / total_model_count >=
deployment_threshold` (Default: 0.10 = 10%) — die Schwelle ist **inklusiv** (≥).

- **≥ Threshold (inklusiv):** `deployed` → missing/unknown-Modelle werden bestraft.
  Bei 110 Modellen und Threshold 0.10: ab 11/110 (11/110 = 0.10 = genau Threshold → deployed).
- **> 0 aber < Threshold:** `rolling_out` → aus Nenner ausgeschlossen für alle,
  INFO-Log: "Module X has data for N/110 models (< threshold), treating as
  rolling_out — excluded from scoring"
- **= 0:** `not_deployed` → aus Nenner ausgeschlossen für alle

Konfigurierbar in `benchmark_config.yaml`:
```yaml
leaderboard:
  deployment_threshold: 0.10  # 10% der Modelle müssen Daten haben
```

Aktuelle Daten: Alle 7+1 Scoring-Module haben ≥96% Coverage → alle `deployed`.
Die Schwelle ist future-proofing für neue Module.

### Invariante

`Routine Score + Reasoning Score = Total Score` bleibt erhalten, weil:

1. Der Malus addiert `expected_w_routine` zu `total_weight_routine` und
   `expected_w_reasoning` zu `total_weight_reasoning`
2. `total_weight_global = total_weight_routine + total_weight_reasoning` wächst
3. `Routine Score = sum_routine / total_weight_global` (sinkt)
4. `Reasoning Score = sum_reasoning / total_weight_global` (sinkt)
5. `Total Score = (sum_routine + sum_reasoning) / total_weight_global` (sinkt)
6. `Routine + Reasoning = (sum_routine + sum_reasoning) / total_weight_global = Total` ✓

**WICHTIG:** `Routine Score` und `Reasoning Score` werden in
`_calculate_group_scores()` mit dem ursprünglichen `total_weight_global`
berechnet. Der Malus muss diese Werte NACH Modifikation der Gewichte
neu berechnen, sonst bricht die Invariante.

## Entscheidungen

| Entscheidung | Wert | Begründung |
|---|---|---|
| `enable_scoring` | `true` | ToolUse ist eine Kernfähigkeit, kein Bias-Diagnosemodul |
| `module_weight` | `1.0` | Vollwertige Evaluationsdimension (Fix: `moduleweight` → `module_weight`) |
| `default_contribution` | `{routine: 0.5, reasoning: 0.5}` | Neutraler Split — combined_score enthält p1/p2-Gewichtung bereits intern |
| `capability_field` | `supports_tool_use` | Config-getriebene incapable-Erkennung via Model Card |
| Coverage-Logik | Generalisiert | present/missing/unknown/incapable/rolling_out/not_deployed für ALLE Scoring-Module |
| Incapable-Behandlung | Exempt (aus Nenner entfernt) | Strukturell nicht anwendbar → nicht bestrafen |
| Missing-Behandlung | Malus (im Nenner, nicht im Zähler) | Sollte getestet worden sein → inkomplette Evaluation bestrafen |
| Unknown-Behandlung | Malus + WARNING-Log | Wie missing, aber mit Warnung wegen fehlendem capability_field |
| Not-deployed-Behandlung | Excluded (für alle Modelle) | Modul mit 0 Daten für alle → noch nicht Teil des Benchmarks |
| Rolling-out-Behandlung | Excluded (für alle Modelle) + INFO-Log | Modul mit < Threshold Coverage → Bestrafung wäre unverhältnismäßig |
| `deployment_threshold` | `0.10` (10%) | Konfigurierbar; verhindert dass ein Modul mit 3/110 Daten 107 Modelle bestraft |
| coverage_ratio | Neue Spalte | Transparenz über Test-Abdeckung (gewichtet) |
| Tests Run | Per-Modell expected | Incapable-Modelle: expected ohne ToolUse-Assets |
| Version | v5.0.0 | Major-Bump für Scoring-Formeländerung |
| Web-Frontend Task 8 | `tooluse_combined` entfernen, p1/p2 rebalancieren | Reine Redundanz-Bereinigung — keine Änderung an Profil-Ranking-Logik |
| Web-Frontend Profil-Ankerung | **Out of Scope** | Separates Web-Frontend-Projekt; wird zu späterem Zeitpunkt entschieden |

## Datenlage

### Modul-Abdeckung (verifiziert gegen Benchmark-CSVs)

| Modul | enable_scoring | module_weight | Assets | Modelle mit Daten |
|---|---|---|---|---|
| Code Quality Audit | true | 1.0 | 5 | 110/110 |
| CLI Badge | true | 0.5 | 6 | 110/110 |
| Logical Reasoning | true | 1.0 | 11 | 110/110 |
| UX Writing & Microcopy | true | 1.0 | 5 | 110/110 |
| Documentation Quality | true | 1.0 | 5 | 110/110 |
| Content Transformation | true | 1.0 | 6 | 110/110 |
| Cultural Intelligence | true | 1.0 | 5 | 110/110 |
| Political Bias | false | — | 9 | 64/110 (nicht scoring) |
| Tool Execution | false→true | 0.0→1.0 | 6 | 106/110 |

### ToolUse-spezifischer Status (nach Aktivierung)

- **106 Modelle present**: gültige ToolUse-Rows (status ∈ _VALID_STATUSES)
- **1 Modell missing**: `meta-llama/llama-4-scout-17b-16e-instruct` — `supports_tool_use: true`, aber alle 6 Rows haben status="error" → penalized (~13%)
- **3 Modelle incapable**: `openai/gpt-oss-20b`, `command-a-plus-05-2026`, `deepseek-r1-distill-qwen-32b` — `supports_tool_use: false` → exempt

**Hinweis zu incapable-Modellen:** gpt-oss-20b und command-a-plus haben Rows
in den Benchmark-CSVs (alle status="error"), deepseek-r1-distill hat gar keine
ToolUse-Rows. Alle drei haben `supports_tool_use: false` in der Model Card und
werden als incapable klassifiziert — unabhängig davon ob error-Rows existieren.

### Erwartete Score-Auswirkungen

- **106 present-Modelle**: ToolUse trägt normal zum Score bei (±abhängig von Performance)
- **1 missing-Modell** (llama-4-scout): ~13% Score-Reduktion (1.0 / 7.5 Gewicht)
- **3 incapable-Modelle**: Keine Strafe — Score = 7-Module-Normalisierung (ToolUse aus Nenner entfernt)

## Implementierung — Python Backend

### Task 1: ToolUse-Modulkonfiguration aktivieren

**Datei:** `benchmark_modules/tooluse/config.yaml`

```yaml
integration:
  leaderboard:
    enable_scoring: true              # WAR: false
    module_weight: 1.0               # WAR: moduleweight: 0.0 (Typo-Fix)
    default_contribution:            # NEU
      routine: 0.5
      reasoning: 0.5
    capability_field: supports_tool_use  # NEU — Model-Card-Feld für incapable-Erkennung
    custom_csv: tooluse_leaderboard.csv
    columns:                         # unverändert — Display-Enrichment bleibt
      - id: p1_score
        label: "Tool Execution"
        ...
```

Kommentar im YAML aktualisieren: "Kein Einfluss auf Total Score" → "Vollwertiges
Scoring-Modul (v5.0) — combined_score fließt als percentage in Total Score ein."

**Hinweis:** `moduleweight` → `module_weight` ist ein Bugfix. Der Code in
`_build_modules_config()` liest `lb_config.get("module_weight")` — der aktuelle
Key `moduleweight` (ohne Unterstrich) wird ignoriert, weshalb `module_weight`
aktuell `None` zurückgibt. Da `enable_scoring: false` ist, hat das bisher keine
Auswirkung. Mit `enable_scoring: true` MUSS der Key korrekt sein.

### Task 1b: Deployment-Threshold konfigurierbar

**Datei:** `benchmark_config.yaml` (oder relevante Config-Stelle)

```yaml
leaderboard:
  deployment_threshold: 0.10  # 10% der Modelle müssen gültige Daten haben
```

In `_build_modules_config()` oder `calculate_scores()` einlesen und an
`_get_deployed_scoring_modules()` durchreichen. Default-Wert 0.10 falls nicht
konfiguriert.

### Task 2: `_build_modules_config` erweitern

**Datei:** `scripts/leaderboard/__init__.py`

`capability_field` zum `mod_entry`-Dict hinzufügen:

```python
mod_entry = {
    "name": display_name,
    "enabled": True,
    "enable_scoring": enable_scoring,
    "default_contribution": default_contrib,
    "module_weight": lb_config.get("module_weight"),
    "assets_count": assets_count,
    "path": mod_path_val,
    "benchmarks": mod_int_config.get("benchmarks", []),
    "display_test_count": lb_config.get("display_test_count"),
    "capability_field": lb_config.get("capability_field"),  # NEU
}
```

### Task 3: Generalisierte Coverage-Status-Klassifikation

**Datei:** `scripts/leaderboard/score_calculator.py`

#### 3a: Incapable-Modell-Erkennung (generalisiert)

```python
_INCAPABLE_CACHE: dict[str, set[str]] | None = None

def _get_incapable_models(modules_config: dict[str, Any]) -> dict[str, set[str]]:
    """
    Returns {category_name: set_of_model_ids} for modules where specific
    models are structurally incapable.

    Uses capability_field from module config to check model cards.
    A model is "incapable" for a module if the card's capability_field
    is explicitly False, "false", or "not_applicable".

    A model is "unknown" if capability_field is configured for the module
    but the field is ABSENT from the model's card (not explicitly false,
    just not present). Unknown models are NOT included in this map —
    they are detected separately in _classify_module_status().

    Lazy-cached at module level.
    """
```

- Iteriert über alle Scoring-Module mit `capability_field` gesetzt
- Lädt Model Cards aus `benchmark_scores/model_cards/*.json`
- Für jedes Modul: sammelt `model_id`s bei denen `card[capability_field]` ∈ `{False, "false", "not_applicable"}`
- Gibt `{category_name: {model_id, ...}}` zurück
- Lazy-Cached wie `_PRICE_LOOKUP`

#### 3b: Deployed-Module-Erkennung (mit Threshold)

```python
def _get_deployed_scoring_modules(
    df_success: pd.DataFrame,
    modules_config: dict[str, Any],
    total_model_count: int,
    deployment_threshold: float = 0.10,
) -> tuple[set[str], set[str]]:
    """
    Returns (deployed_modules, rolling_out_modules).

    - deployed: ≥ deployment_threshold × total_model_count models have
      valid data → missing/unknown models penalized
    - rolling_out: > 0 but < threshold → excluded from denominator for all,
      INFO-logged
    - not_deployed (0 data): excluded from denominator for all (not returned)

    This prevents a module tested on only 3/110 models from penalizing
    the other 107.
    """
```

- Filtert `modules_config` auf `enable_scoring=True`
- Für jedes Modul: zählt Modelle mit ≥1 gültiger Row
- `deployed_count / total_model_count >= threshold` → deployed
- `0 < deployed_count / total_model_count < threshold` → rolling_out (INFO-Log)
- `deployed_count == 0` → not_deployed (implizit excluded)
- Rückgabe: `(deployed_set, rolling_out_set)`

#### 3c: Modul-Status pro Modell (mit unknown)

```python
def _classify_module_status(
    model_id: str,
    category: str,
    df_success: pd.DataFrame,
    incapable_map: dict[str, set[str]],
    modules_config: dict[str, Any],
) -> str:
    """
    Returns 'present', 'missing', 'unknown', or 'incapable' for a given
    model+module.

    - 'present': model has ≥1 valid row for this category
    - 'incapable': no valid rows AND model in incapable_map[category]
      (capability_field explicitly false in card)
    - 'unknown': no valid rows AND capability_field configured for module
      AND field ABSENT from model's card (not explicitly false)
      → WARNING-Log: "Model X has no capability_field '{field}' in card
         for module Y — treating as missing with warning"
    - 'missing': no valid rows AND not incapable AND not unknown
      (capability_field not configured, or field present and not false)
    """
```

**Unknown-Detection-Logik:**
1. Prüfe ob `capability_field` in `modules_config[category]` gesetzt ist
2. Wenn ja: lade Model Card für `model_id`
3. Wenn `capability_field` als Key NICHT in der Card existiert → `unknown`
4. Wenn `capability_field` existert und ist `False`/`"false"`/`"not_applicable"` → `incapable`
5. Wenn `capability_field` existert und ist `True`/`"true"` → `missing` (capable aber keine Daten)

### Task 4: Generalisierter Coverage-Malus

**Datei:** `scripts/leaderboard/score_calculator.py`

```python
def _compute_expected_module_weights(
    mod_data: dict[str, Any],
) -> tuple[float, float]:
    """
    Computes the total routine/reasoning weights a fully-present module
    would contribute to the denominator.

    Uses the same scale logic as _module_scale():
      scale = module_weight / config_weight_sum
      expected_w_routine = scale × Σ(routine_contributions)
      expected_w_reasoning = scale × Σ(reasoning_contributions)

    When all assets use default_contribution, this simplifies to:
      expected_w_routine = module_weight × default_routine / (default_routine + default_reasoning)
      expected_w_reasoning = module_weight × default_reasoning / (default_routine + default_reasoning)

    For module_weight=None: scale=1.0, weights = Σ(contributions).
    """
```

```python
def _apply_coverage_malus(
    result: pd.DataFrame,
    df_success: pd.DataFrame,
    modules_config: dict[str, Any],
    deployment_threshold: float = 0.10,
) -> pd.DataFrame:
    """
    v5.0: Generalized Coverage Malus.

    For each model, identifies missing/unknown scoring modules (deployed but
    no valid data for this model, and not incapable). Adds their expected
    weights to the denominator without numerator contribution.

    Incapable modules are excluded from the denominator entirely.
    Not-deployed and rolling_out modules are excluded for all models.

    Also computes coverage_ratio = Σ(present weights) / Σ(present + missing
    + unknown weights).

    CRITICAL: Recomputes Routine Score and Reasoning Score after modifying
    weights, because _calculate_group_scores() computes them with the
    original (pre-malus) total_weight_global.
    """
```

**Logik:**

1. Bestimme `(deployed, rolling_out)` via `_get_deployed_scoring_modules()`
2. Bestimme incapable map via `_get_incapable_models()`
3. Für jedes deployed scoring module: berechne `expected_w_routine`, `expected_w_reasoning` via `_compute_expected_module_weights()`
4. Für jedes Modell in `result`:
   a. Für jedes deployed scoring module: klassifiziere als present/missing/unknown/incapable
   b. Für "missing" und "unknown" modules: addiere `expected_w_routine` zu `total_weight_routine`, `expected_w_reasoning` zu `total_weight_reasoning`
   c. Berechne `coverage_ratio` = Σ(present module_weight) / Σ(present + missing + unknown module_weight)
5. **Recompute** `total_weight_global`, `Routine Score`, `Reasoning Score` mit aktualisierten Gewichten
6. Füge `coverage_ratio` als neue Spalte hinzu

**Aufrufort** in `calculate_scores()`:

```python
# Routine vs Reasoning (v2.1: Granular Weights)
result = _merge_granular_scores(result, df_success, modules_config)

# v5.0: Generalized Coverage Malus (missing/unknown → penalize, incapable → exempt)
result = _apply_coverage_malus(result, df_success, modules_config, deployment_threshold)

# Total Score Calculation (Volume-Weighted)
result["Total Score"] = result.apply(_calc_weighted_total, axis=1)
```

**Warum Routine/Reasoning recomputiert werden müssen:**

`_calculate_group_scores()` berechnet `Routine Score = sum_routine / total_weight_global`
mit dem ursprünglichen `total_weight_global` (nur present-Module). Der Malus
erhöht `total_weight_routine` und `total_weight_reasoning` für missing/unknown-Module.
Ohne Recomputation würde `Total Score` den neuen Nenner verwenden, aber
`Routine Score` und `Reasoning Score` den alten — die Invariante
`Routine + Reasoning = Total` wäre verletzt.

### Task 5: Per-Modell "Tests Run"-Erwartung

**Datei:** `scripts/leaderboard/score_calculator.py`

Modifikation in `_calculate_run_counts()`:

```python
# Nach Berechnung von expected_assets und logical_count:
incapable_map = _get_incapable_models(modules_config)

# Sammle Assets-Count der incapable-Module pro Modell
# (generalisiert: nicht nur tooluse)
def _expected_for_model(row):
    model_id = str(row.get("model", ""))
    canonical = _resolve_to_canonical_id(model_id)
    reduction = 0
    for cat, incapable_ids in incapable_map.items():
        if canonical in incapable_ids:
            mod_data = _find_mod_data_by_name(modules_config, cat)
            if mod_data:
                reduction += mod_data.get("assets_count", 0)
    return expected_assets - reduction

run_counts["expected_assets"] = run_counts.apply(_expected_for_model, axis=1)
```

**Ergebnis:**
- Present-Modelle: 49/49 (complete)
- Missing-Modell (llama-4-scout): 43/49 (* incomplete — korrekt)
- Incapable-Modelle: 43/43 (complete — ToolUse nicht erwartet)

### Task 6: `_finalize_leaderboard_columns` anpassen

**Datei:** `scripts/leaderboard/score_calculator.py`

`coverage_ratio` nicht in `cols_to_drop` aufnehmen — sie ist eine Output-Spalte.
Eventuell formatieren (z.B. als Dezimalzahl mit 2 Nachkommastellen).

### Task 7: Tests

**Datei:** `scripts/leaderboard/tests/test_score_calculator_coverage.py` (neu)

#### Generalisierte Coverage-Tests

- `test_present_module_scored`: Modell mit Daten für alle Module → normaler Score
- `test_missing_module_penalized`: Modell fehlt Daten für ein deployed-Modul → Score reduziert um module_weight / total_weight
- `test_unknown_module_penalized_and_warned`: capability_field fehlt in Card → wie missing bestraft, aber WARNING-Log erzeugt
- `test_incapable_module_exempt`: Modell ist incapable für ein Modul → keine Strafe, Modul aus Nenner entfernt
- `test_not_deployed_module_excluded`: Modul hat 0 Daten für alle Modelle → nicht im Nenner für irgendjemand
- `test_rolling_out_module_excluded`: Modul hat Daten für <10% der Modelle → nicht im Nenner für irgendjemand, INFO-Log
- `test_coverage_ratio_present`: coverage_ratio = 1.0 für vollständige Modelle
- `test_coverage_ratio_missing`: coverage_ratio < 1.0 für Modelle mit fehlendem Modul
- `test_coverage_ratio_unknown`: coverage_ratio < 1.0 für unknown-Modelle (zählt gegen coverage)
- `test_coverage_ratio_incapable`: coverage_ratio = 1.0 für incapable-Modelle (incapable zählt nicht gegen coverage)

#### Invarianten-Tests (getrennt für Routine/Reasoning)

- `test_invariant_routine_plus_reasoning_equals_total_present`: Für present-Modelle
- `test_invariant_routine_plus_reasoning_equals_total_missing`: Für missing-Modelle (nach Malus)
- `test_invariant_routine_plus_reasoning_equals_total_unknown`: Für unknown-Modelle (nach Malus)
- `test_invariant_routine_plus_reasoning_equals_total_incapable`: Für incapable-Modelle
- `test_routine_score_recomputed_after_malus`: Routine Score reflektiert aktualisierten Nenner
- `test_reasoning_score_recomputed_after_malus`: Reasoning Score reflektiert aktualisierten Nenner

#### ToolUse-spezifische Tests

- `test_tooluse_present_scored`: ToolUse-Daten fließen in Total Score ein
- `test_tooluse_missing_penalized`: llama-4-scout-Äquivalent → ~13% Reduktion
- `test_tooluse_incapable_exempt`: supports_tool_use=false → keine Strafe
- `test_expected_count_incapable`: Incapable-Modell hat expected=43
- `test_expected_count_present`: Present-Modell hat expected=49
- `test_no_per_asset_data_changed`: Benchmark-CSVs unverändert (Regression-Schutz)

#### Edge-Case-Tests

- `test_multiple_missing_modules`: Modell fehlen 2+ Module → kumulativer Malus
- `test_extreme_low_coverage`: **(Schwäche 4 aus Kritik)** Modell hat nur 1 von 8 Modulen present → coverage_ratio sehr niedrig, Score massiv reduziert, Modell rangiert unter allen vollständigen Modellen. Verifikation: coverage_ratio ≈ weight_of_single_module / total_weight, und score_rank > rank_any_complete_model
- `test_coverage_ratio_zero`: Modell hat 0 present-Module (alle missing) → coverage_ratio = 0.0, Score = 0.0
- `test_capability_field_none`: Modul ohne capability_field in config → alle missing = "missing" (kein incapable, kein unknown)
- `test_capability_field_absent_in_card`: capability_field in config, aber Key fehlt in Model Card → "unknown" + WARNING-Log
- `test_capability_field_explicit_false`: capability_field in Card = False → "incapable" (kein unknown)
- `test_module_weight_none`: Modul ohne module_weight → Scale=1.0, erwartete Gewichte aus contributions
- `test_deployment_threshold_boundary`: Schwellen-Exaktheit: 11/110 (= 0.10 = genau Threshold) → **deployed** (inklusiv ≥); 10/110 (= 0.091 < Threshold) → **rolling_out**

## Implementierung — Web Frontend (CrucibleMark-Web)

### Task 8: Agentic-Profilformeln bereinigen (reine Redundanz-Bereinigung)

**Datei:** `CrucibleMark-Web/src/assets/js/config/profiles.js`

**Scope:** Nur `tooluse_combined` aus den Profilgewichten entfernen und p1/p2
rebalancieren. **Keine Änderung an `resolveScore()` oder anderer
Profil-Ranking-Logik.** Eine mögliche Anker-Formel (Total Score Blend, Floor,
etc.) wird zu einem späteren Zeitpunkt separat im Web-Frontend-Projekt
entschieden.

**Begründung:** Der Python-Backend integriert ab v5.0 ToolUse's `percentage`
(= combined_score) in den Total Score. Die agentic Profile verwendeten bisher
`tooluse_combined` als separates Gewicht alongside `p1_score` und `p2_score`.
Da der Total Score combined_score bereits enthält, würde eine separate
Profil-Gewichtung dasselbe Metric doppelt zählen.

`agentic_execution` weights:
```js
// Vorher: tool_execution 0.35, synthesis_quality 0.30, tooluse_combined 0.20
// Nachher:
weights: {
    tool_execution:    0.55,
    synthesis_quality: 0.45,
},
```

`agentic_creative` weights:
```js
// Vorher: synthesis_quality 0.40, tool_execution 0.25, tooluse_combined 0.20
// Nachher:
weights: {
    synthesis_quality: 0.65,
    tool_execution:    0.35,
},
```

Penalties unverändert. Description-HTML und Gewichtung-Summary aktualisieren
("ToolUse Score 20%" aus Beschreibung entfernen).

### Task 9: Coverage-Badge (optional)

**Datei:** `CrucibleMark-Web/src/assets/js/modules/leaderboard-groups.js`

- Lese `coverage_ratio` Spalte aus leaderboard CSV
- Modelle mit `coverage_ratio < threshold` erhalten "Vorläufig"-Badge
- Badge wird neben Model-Name angezeigt (ähnlich "Tests Run" Anzeige)
- Sortierreihenfolge nicht verändert — der Malus im Score bereits sortiertkorrekt

**Threshold-Ableitung (aus Gewichtslogik, nicht aus Einzelfall kalibriert):**

```
threshold = (total_weight - max_single_module_weight) / total_weight
          = (7.5 - 1.0) / 7.5
          = 0.867
```

Ein fehlendes Modul mit maximalem Gewicht (1.0) senkt Coverage auf 0.867.
Threshold = 0.85 (abgerundet als Puffer für zukünftige Gewichtsänderungen).
Badge-Threshold als Konstante in `profiles.js` oder `chart-constants.js`:
```js
export const COVERAGE_BADGE_THRESHOLD = 0.85;
```

**Hinweis:** Diese Task ist optional und kann in einem separaten PR folgen.
Die Python-Backend-Änderung (coverage_ratio-Spalte) ist nicht optional.

**Hinweis zur Threshold-Platzierung:** Die Herleitung nutzt Backend-Gewichte
(total_weight=7.5, max_weight=1.0), weil diese dort definiert sind. Die
Umsetzung (Badge-Anzeige) ist Frontend. Bei zukünftigen Modul-Gewichts-
änderungen muss der Threshold im Frontend-Projekt neu hergeleitet werden —
dieser Plan liefert die Formel, nicht den fixen Wert.

### Task 10: resolveScore-Kommentar aktualisieren

**Datei:** `CrucibleMark-Web/src/assets/js/modules/leaderboard-groups.js`

```js
// v5.0: tooluse_combined aus agentic Profilen entfernt.
// Total Score enthält combined_score bereits (Python Backend).
// p1/p2 liefern granularere Signale; Guardrails via Penalties.
```

## Validierung

### V1: Lint & Tests
```bash
make validate
pytest -v --tb=short
```

### V2: Leaderboard-Regeneration
```bash
python -m scripts.leaderboard
```
Vergleiche `benchmark_leaderboard_detailed.csv` vor/nach.

### V3: Vorher/Nachher-Ranking-Tabelle
- Top-10-Modelle: Sortierung vergleichen
- 1 Missing-Modell (llama-4-scout): Score-Reduktion ~13% dokumentieren
- 3 Incapable-Modelle: Score unverändert (7-Module-Normalisierung) dokumentieren
- Modelle mit Rank-Verschiebung >3: Einzelfall-Analyse

### V4: Invarianten-Check (getrennt für Routine/Reasoning)
- `Routine Score + Reasoning Score ≈ Total Score` für alle Modelle (Toleranz 0.1)
- Separate Verifikation für present, missing, unknown, incapable Status
- `Routine Score` und `Reasoning Score` verwenden aktualisierten Nenner (nicht Original)
- Keine negativen Scores, keine Scores > 100
- Benchmark-CSVs (local/cloud/commercial) unverändert (`git diff`)

### V5: Coverage-Ratio-Verifikation
- 106 present-Modelle: coverage_ratio = 1.0
- 1 missing-Modell (llama-4-scout): coverage_ratio ≈ 0.87 (6.5/7.5)
- 3 incapable-Modelle: coverage_ratio = 1.0 (incapable zählt nicht gegen coverage)
- `coverage_ratio`-Spalte in `benchmark_leaderboard_detailed.csv` vorhanden

### V6: Not-Deployed- und Rolling-Out-Verifikation
- Alle 8 Scoring-Module sind deployed (Daten für ≥96% der Modelle → weit über 10% Threshold)
- Bei Hinzufügen eines fiktiven nicht-deployed Moduls: kein Einfluss auf Scores
- Bei Hinzufügen eines fiktiven rolling_out Moduls (3/110 Modelle): kein Einfluss auf Scores, INFO-Log

### V7: Unknown-Status-Verifikation
- Aktuell keine unknown-Modelle (alle 110 Modelle haben `supports_tool_use` in Card)
- Bei Entfernen des Felds aus einer Test-Card: WARNING-Log, Modell als missing+unknown behandelt

## Dokumentation

### D1: CHANGELOG.md
- v5.0.0-Eintrag: Generalisierte Coverage-Logik, ToolUse als Scoring-Modul, Incapable-exempt/Missing-penalize/Unknown-warned, Deployment-Threshold, coverage_ratio-Spalte, Web-Frontend-Redundanzbereinigung
- Breaking-Change-Hinweis: Total Scores und Rankings ändern sich

### D2: README.md
- Scoring-Beschreibung: "7 Module" → "8 Module (inkl. ToolUse)"
- Abschnitt zu Coverage-Logik: present/missing/unknown/incapable/rolling_out/not_deployed
- coverage_ratio-Erklärung
- deployment_threshold-Erklärung

### D3: benchmark_modules/tooluse/SCORING_RUBRIC.md
- Abschnitt "Integration" ergänzen: combined_score als percentage in Total Score
- Incapable-Exempt-Dokumentation (nicht mehr Malus)
- Unknown-Status-Dokumentation

### D4: docs/ARCHITECTURE.md (oder .agent/architecture.md)
- Scoring-Formel aktualisieren: Coverage-aware denominator
- 6-Status-Taxonomie dokumentieren (present/missing/unknown/incapable/rolling_out/not_deployed)
- Deployment-Threshold dokumentieren

## Risken

| Risiko | Wahrscheinlichkeit | Mitigation |
|---|---|---|
| Routine/Reasoning Score nicht recomputiert nach Malus | Hoch (subtiler Bug) | Task 4 explizit; V4-Invarianten-Check getrennt für Routine/Reasoning |
| Top-10-Ranking verschiebt sich stark | Mittel | V3-Vergleich; bei >2 Modellen aus Top-10 Formel hinterfragen |
| Incapable-Erkennung verfehlt Modelle | Mittel (für neue Modelle) | Unknown-Status mit WARNING-Log als Fallback; V7-Verifikation |
| `module_weight` vs `moduleweight` Typo persists | Niedrig | Task 1 fixt explizit; V1-Lint prüft |
| Generalisierung hat keinen Effekt auf aktuelle Daten | Bekannt (by design) | Architektonisch korrekt; future-proof für neue Module |
| Web-Frontend veraltet (anderes Repo) | Medium | Tasks 8-10 als separater PR im CrucibleMark-Web-Repo |
| coverage_ratio-Threshold zu niedrig/hoch | Niedrig | Aus Gewichtslogik abgeleitet: (7.5-1.0)/7.5=0.867 → 0.85; konfigurierbar |
| Historische Benchmarks nicht reproduzierbar | Hoch (by design) | v5.0-Versionierung; alte Leaderboards in Git-History |
| Rolling_out-Schwelle falsch kalibriert | Niedrig | 10% Default ist konservativ; konfigurierbar; alle aktuellen Module weit über Threshold |
| Unknown-Status überflutet Logs | Niedrig | Aktuell 0 unknown-Modelle; nur bei neuen Modellen ohne capability_field relevant |

## Out of Scope

- **Web-Frontend Agentic-Profil-Ankerung** (Total Score Blend, Floor, etc.) — separates Web-Frontend-Projekt
- **Web-Frontend `resolveScore()` Renormalisierungs-Logik** — keine Änderung an Profil-Ranking-Logik in diesem Plan
- Kontextfenster-Gewichtung (separates Thema)
- Judge-Prompt-Logik oder Golden Standards
- Political Compass Integration (bleibt enable_scoring: false)
- `benchmark_leaderboard_detailed.csv`-Spaltennamen-Änderung (nur neue Spalte `coverage_ratio`)
- Re-Runs von Benchmarks (Per-Asset-Daten bleiben unverändert)
- CLI Badge / Cultural Intelligence Re-Aktivierung (bereits aktiv und deployed)
- Automatische coverage_ratio-basierte Sortierung (Badge nur optisch)
