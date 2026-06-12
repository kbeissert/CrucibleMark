# CrucibleMark: Card-Management

**Zielgruppe:** Entwickler, die Model- oder Provider-Cards erstellen, prüfen oder mit dem Template synchronisieren wollen.

**Inhalt:**

- [Überblick](#überblick)
- [Card-Typen](#card-typen)
- [SSoT-Architektur](#ssot-architektur)
- [Card-Lifecycle](#card-lifecycle)
- [Workflows](#workflows)
- [CLI-Referenz](#cli-referenz)
- [Make-Targets](#make-targets)
- [Troubleshooting](#troubleshooting)

---

## Überblick

CrucibleMark verwaltet zwei Klassen von Karten, beide als JSON-Dateien:

| Typ | Pfad | SSoT-Template |
|---|---|---|
| **Vendor Card** | `benchmark_scores/vendor_cards/{slug}.json` | `utils/vendor_card_template._PROVIDER_CARD_TEMPLATE` |
| **Model Card** | `benchmark_scores/model_cards/{slug}.json` | `utils/card_utils._CARD_TEMPLATE` |

Zusätzlich gibt es zwei **deklarative YAML-Templates** (`config/card_template_*.yaml`),
die für den **Validator** genutzt werden — sie beschreiben zusätzlich *welcher
Konsument* welches Feld liest. Beide SSoT-Layer (Python-Dict + YAML) sind seit
Phase 24 dokumentiert und werden vom Sync-Workflow zusammengeführt.

---

## Card-Typen

### Vendor Card

Beschreibt einen **API-/Cloud-Anbieter**: Unternehmen, Sitz, Gründungsjahr,
Pricing-Modell, Deployment-/Compliance-Subobjekt (CLOUD-Act, GDPR, etc.),
Datenschutz-Hinweis, gemessene Performance-Statistiken.

Felder (16 Pflicht, 4 Optional inkl. `description`): siehe `config/card_template_vendor.yaml`.

### Model Card

Beschreibt ein **einzelnes Modell**: Identität, Deployment-Typ, Architektur,
Lizenz, Pricing, Thinking-Probe-Ergebnisse, Tool-Use-Support.

Felder (38 Pflicht, 18 Optional inkl. `profile_verified`): siehe `config/card_template_model.yaml`.

---

## SSoT-Architektur

```
                ┌───────────────────────────────────────────────┐
                │  config/card_template_{model,provider}.yaml   │
                │  (Deklarativ: Pflicht, Optional, Konsumenten)  │
                └──────────────────┬────────────────────────────┘
                                   │  Loader
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  utils/card_template.py (load_card_template)  │
                └──────────────────┬────────────────────────────┘
                                   │
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  scripts/analysis/validate_cards.py           │
                │  (YAML-driven Validator)                      │
                └───────────────────────────────────────────────┘

                ┌───────────────────────────────────────────────┐
                │  utils/{card_utils,vendor_card_template}   │
                │  .py  (Python-Dict SSoT für Generatoren)      │
                └──────────────────┬────────────────────────────┘
                                   │  ensure_card / normalize
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  scripts/analysis/{generate_model_cards,      │
                │  generate_vendor_cards}.py                  │
                └──────────────────┬────────────────────────────┘
                                   │  (LLM-Calls + Stats)
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  benchmark_scores/{model,provider}_cards/     │
                └──────────────────┬────────────────────────────┘
                                   │  Sync (SSoT)
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  utils/card_sync.py (plan_sync, apply_sync)   │
                └───────────────────────────────────────────────┘
```

**Drei SSoT-Layer:**

1. **Python-Dict** (`utils/*_card_template.py`) — wird von den Generatoren
   und `ensure_card()`-Funktionen genutzt, um fehlende Felder mit Defaults
   zu ergänzen.
2. **YAML** (`config/card_template_*.yaml`) — wird vom Validator genutzt,
   um Karten gegen das deklarierte Schema zu prüfen. Annotiert Konsumenten.
3. **JSON-Dateien** in `benchmark_scores/` — der Endzustand auf Platte.

**Konsequenz:** Template-Änderungen müssen in **beide** Layer gepflegt
werden (Python-Dict + YAML), damit Generator und Validator synchron
bleiben. Die Card-Sync-Logik (`utils/card_sync.py`) liest den Python-Dict
und schreibt die JSON-Dateien.

**Taxonomie-SSoT (seit v4.7.x):** Die kontrollierten Vokabulare für
`weights_license_tier`, `use_case` und `parameter_architecture` leben in
`config/classification_taxonomy.json`. Generator, Validator und
`ensure_card()` lesen alle aus dieser Datei via
`utils.card_utils.load_taxonomy()` / `get_valid_values()`. Eine
Liste der gültigen Werte ist damit immer an einer einzigen Stelle zu
pflegen — Template-Beschreibungen werden durch
`tests/test_taxonomy_ssot.py::TestTemplateTaxonomySync` automatisch
gegen die Taxonomie synchron gehalten.

---

## Placeholder-Konvention

Bevor die Taxonomie-SSoT eingeführt wurde, enthielten Karten häufig
Workaround-Strings in den kontrollierten Feldern. Diese sind inzwischen
**verboten** und werden durch `make validate-cards` bzw. den Regressionstest
`tests/test_taxonomy_ssot.py::TestNoPlaceholderStrings` abgefangen.

### Verbotene Werte in kontrollierten Feldern

| Feld                       | Verbotene Placeholder                                | Korrekter Wert (Beispiele)                          |
|----------------------------|------------------------------------------------------|-----------------------------------------------------|
| `weights_license_tier`     | `open-weights-pending`, `TODO`                       | `proprietary`, `open-weights`, `restricted-weights` |
| `use_case_primary`         | `code-generation`, `code-gen`, `frei`, `TODO`        | `generalist`, `coding`, `reasoning`, `vision-language`, `agentic` |
| `parameter_architecture`   | `hybrid-attention`, `unknown`, `TODO`                | `dense`, `moe`, `hybrid`                            |

`TODO` ist **ausschließlich** in `weights_license_tier` als Fallback für
noch nicht recherchierte Karten zulässig (Taxonomie-Fallback). In allen
anderen kontrollierten Feldern ist `TODO` ein Validierungs-Fehler.

### Verbotene Architektur-Tags

`architecture_tags` ist eine freie Liste, aber zwei Werte sind
reserviert und haben eine spezifische Bedeutung im Validator
(`scripts/dev/validate_model_cards.py`):

| Tag              | Bedeutung                                                              |
|------------------|-------------------------------------------------------------------------|
| `Multimodal`     | Primär visuell: löst Warnung aus, wenn `use_case_primary != vision-language` |
| `Vision-Capable` | Sekundäres Vision-Feature (z.B. Claude 4.x, Qwen 3.6 Plus bei agentic-Use-Case) — löst **keine** Warnung aus |

**Faustregel:** `Multimodal` nur, wenn das Modell primär für
Vision-Aufgaben optimiert ist. Andernfalls `Vision-Capable` verwenden.

### Workflow bei neuen Workarounds

Wenn du einen Workaround brauchst (z.B. ein Modell, das in keine
bestehende Kategorie passt):

1. **Niemals** einen neuen String in die Karten-Datei schreiben.
2. Stattdessen prüfen, ob die Taxonomie (`config/classification_taxonomy.json`)
   erweitert werden muss.
3. Erweiterung in einem separaten Commit mit Begründung.
4. Template-Beschreibung in `config/card_template_model.yaml` synchron
   halten — der Test `TestTemplateTaxonomySync` schlägt sonst Alarm.

---

---

## Card Vocabulary Registry (`config/card_vocabulary.yaml`)

Ab v4.7.0 gibt es eine zentrale Registry für alle **programmatisch wirksamen
Felder und Tags** in Model- und Provider-Cards. Sie ist die Single Source of
Truth (SSoT) für die kontrollierten Vokabulare, damit Auto-Generatoren,
Validator und Web-Export dieselbe Definition nutzen.

### Struktur

Die Registry hat vier Sektionen:

| Sektion | Zweck | Code-Effekt? |
| --- | --- | --- |
| `controlled_fields` | Verweise auf Taxonomie-Felder (`weights_license_tier`, `use_case_primary` etc.) | ja |
| `reserved_tags` | Tags, die vom Code aktiv ausgewertet werden (z.B. `Thinking`, `Coder`) | ja |
| `informational_tags` | Tags, die nur als Web-Export-Filter dienen (z.B. `Long-Context`) | nein |
| `deprecated_tags` | Alte Tags mit Migrations-Hinweis (z.B. `MoE`, `Mamba-Hybrid`) | normalisiert |
| `reasoning_triggers` | Modellname-Substrings, die den 5× Reasoning-Multiplikator triggern | ja |

### Konsumenten

Die Registry wird von folgenden Modulen konsumiert:

- `utils/card_utils.py` — Lade-Helper, `normalize_tags()`, `get_reasoning_triggers()`
- `scripts/dev/validate_model_cards.py` — Tag-Whitelist-Check
- `scripts/dev/migrate_architecture_tags.py` — Tag-Normalisierung beim Card-Update
- `utils/model_utils.py` — `is_reasoning_model()` Trigger-Liste
- `scripts/web_export.py` — Tag-Filter via `_normalize_export_tags()`

### Workflow: Neuen Tag einführen

1. Prüfen, ob der Tag semantisch zur bestehenden Registry passt.
2. Entscheiden, ob `reserved` (Code-Effekt) oder `informational` (nur Filter).
3. Eintrag in `config/card_vocabulary.yaml` mit Beschreibung und `since`-Version.
4. Bei `reserved`: Konsument-Code (z.B. `web_export.py`, `model_utils.py`) implementieren.
5. Test anpassen in `tests/test_card_vocabulary_ssot.py` (z.B. `must_have`).
6. Bei Bedarf Bulk-Migration: `python scripts/dev/migrate_architecture_tags.py --dry-run`.

### Workflow: Tag als deprecated markieren

1. In `deprecated_tags` mit `normalized_to` (Slug des Nachfolgers) oder `null` (entfernen) eintragen.
2. Migrations-Hinweis in `reason` dokumentieren.
3. `migrate_architecture_tags.py` läuft idempotent — bestehende Karten werden beim nächsten Lauf bereinigt.
4. Validator warnt bei verbleibenden deprecated Tags (zur Erinnerung).

### Anti-Pattern: Wildwuchs

Unbekannte Tags in `architecture_tags` lösen eine **WARN** im Validator aus.
Das ist Absicht: Wildwuchs verhindern, Registry als Orientierung für
Auto-Generatoren erzwingen. Falls ein Generator einen neuen Tag schreibt,
muss er vorher in der Registry dokumentiert werden.

Beispiel für typische Meldung:
```
[WARN] architecture_tags enthält unbekannten Tag 'MyNewTag' — nicht in
config/card_vocabulary.yaml. Falls gewollt: in reserved_tags/informational_tags
aufnehmen, sonst entfernen.
```

### Beispiel: Eintrag in `reserved_tags`

```yaml
  - slug: Agentic
    label: "Agentic"
    description: "Modell ist auf Tool-Use und mehrstufige Aufgabenplanung optimiert."
    consumers: [use_case_inference]
    programmatic_effect: "Marker für use_case_primary='agentic'."
    since: v4.4.0
```

Felder:
- `slug` — kanonische Schreibweise (case-sensitive, Kebab-Case bevorzugt)
- `label` — Anzeige-Name im Web-Export
- `description` — fachliche Erklärung für Doku und Auto-Generatoren
- `consumers` — Liste der Module, die den Tag auswerten
- `programmatic_effect` — kurze Beschreibung der Wirkung (für Audits)
- `since` — Version, ab der der Tag in der Registry steht

---

## Card-Lifecycle

### 1. Erstellen

**Manuell (eine Karte):**

```bash
# Model Card
python scripts/analysis/generate_model_cards.py --model-id claude-opus-4-7

# Vendor Card
python scripts/analysis/generate_vendor_cards.py --provider "Anthropic"
```

**Batch (alle fehlenden):**

```bash
make model-cards
make vendor-cards
```

### 2. Felder ergänzen (vorwärts)

Wenn ein neues Feld ins Template aufgenommen wird, ergänzen
`ensure_card()` und `ensure_vendor_card()` fehlende Felder mit
Default-Werten — automatisch beim nächsten Schreibvorgang.

**Pro Karte erzwingen:**

```bash
make ensure-card MODEL=claude-opus-4-7
```

**Alle Karten:**

```bash
make ensure-cards
```

### 3. Validieren

```bash
# Beide Typen
make validate-cards-template

# Nur Provider
make validate-cards-template CARD_TYPE=provider

# Nur Model
make validate-cards-template CARD_TYPE=model

# Als JSON-Report
make validate-cards-template JSON=1

# CI-Gate (Exit 1 bei Drift)
make validate-cards-template FAIL_ON_DRIFT=1
```

Validator-Issue-Typen (`scripts/analysis/validate_cards.py`):
- `missing_required` — Pflichtfeld fehlt komplett
- `unknown_sentinel` — Pflichtfeld hat Sentinel-Wert (`null`, `"TODO"`, `"unknown"`, `""`, leere Liste)
- `drift_extras` — Feld außerhalb des Templates (Toleranz: `tooluse_*` Legacy)
- `missing_sub_field` — Sub-Feld fehlt (z.B. `deployment.cloud_act_exposure`)
- `parse_error` — JSON-Parse-Fehler

Konsistenz-Checks (`scripts/dev/validate_model_cards.py`):
1. **Summary/Tier-Mismatch**: Summary enthält "Open-Weights" aber `weights_license_tier != "open-weights"`
2. **Tier/Commercial-Mismatch**: `weights_license_tier="open-weights"` aber `commercial_use_allowed=false` (sollte `restricted-weights` sein)
3. **Required Fields**: `model_id`, `display_name`, `weights_license_tier`, `license`, `commercial_use_allowed`, `use_case_primary`, `parameter_architecture`
4. **Controlled Vocabulary**: `use_case_primary`, `weights_license_tier`, `parameter_architecture` gegen Taxonomie-SSoT (`config/classification_taxonomy.json`)
5. **Vision/Multimodal Warning**: `architecture_tags` enthält `Vision`/`Multimodal` (ohne `Vision-Capable`), aber `use_case_primary != "vision-language"`
6. **Architecture Tags Whitelist**: Unbekannte/deprecated Tags gegen `config/card_vocabulary.yaml`
7. **Top-Level Field Whitelist**: Unbekannte Felder in complete-Cards gegen `config/card_template_model.yaml`
8. **Provenance Risk Auto-Validation** (seit v4.7.6):
   - `proprietary` + `origin_country=(USA|China)` → `weights_provenance_risk` ≥ `"medium"`
   - `open-weights` + `origin_country=(USA|China)` + `deployment_type="cloud-only"` → `weights_provenance_risk` ≥ `"medium"`
   - Hintergrund: CLOUD Act (USA), Cyber Security Law (China) ermöglichen staatlichen Datenzugriff

Test-Coverage: `tests/test_provenance_risk_validation.py` (8 Test-Cases)

### 4. Synchronisieren (SSoT-Sync)

**Vorwärts-Sync** (neue Felder im Template → in Karten ergänzen) läuft
automatisch. **Rückwärts-Sync** (entfernte Felder → aus Karten entfernen)
braucht eine Bestätigung.

```bash
# Vorschau (was würde passieren?)
make cards-sync DRY_RUN=1

# Beide Typen, Löschung bestätigen pro Karte
make cards-sync

# Beide Typen, alle Löschungen automatisch bestätigen
make cards-sync YES=1

# Nur Provider-Karten
make cards-sync CARD_TYPE=provider

# Über den Provider-Generator
make vendor-cards-update
make vendor-cards-update YES=1
make vendor-cards-update DRY_RUN=1

# Über den Model-Generator (DEPRECATED seit v4.7.5: --update entfernt)
make cards-sync CARD_TYPE=model
```

CLI direkt:

```bash
python scripts/analysis/sync_cards.py --card-type all --dry-run
python scripts/analysis/sync_cards.py --card-type provider --yes
python scripts/analysis/sync_cards.py --card-type model --json
```

**Sync-Logik:**

| Aktion | Wann | Wie |
|---|---|---|
| **add** | Feld im Template, fehlt in Karte | Default aus Template, automatisch |
| **keep** | Feld in Karte UND Template | unverändert |
| **delete** | Feld in Karte, nicht im Template | nach Bestätigung entfernt |

**Schutzregeln:**

- `provider_id` / `model_id` werden nie gelöscht (Pflicht-IDs)
- `tooluse_*`-Legacy in Model Cards wird toleriert (nicht gelöscht)
- Bei Lösch-Ablehnung wird die **ganze Karte** nicht angefasst (atomarer Sync)

### 5. Status prüfen

**Provider-Card-Hygiene** (verifiziert, stale, unknown deployment-Felder):

```bash
make vendor-cards-status                    # default 90 Tage
make vendor-cards-status STALE_DAYS=30      # aggressiver
make vendor-cards-status JSON=1             # für CI-Parsing
```

---

## Workflows

### Workflow 1: Neues Feld ins Template einführen

1. **YAML-Template** editieren (`config/card_template_*.yaml`)
2. **Python-Dict** synchron editieren (`utils/*_card_template.py`)
3. **Test schreiben** für `utils/card_sync.py` (wenn Verhalten geändert)
4. **Tests laufen lassen**: `make test`
5. **Cards synchronisieren**: `make cards-sync YES=1`
6. **Karten validieren**: `make validate-cards-template`

### Workflow 2: Feld aus Template entfernen

1. Feld aus YAML + Python-Dict entfernen
2. Tests anpassen (Test-Daten, die das Feld noch nutzen)
3. `make cards-sync DRY_RUN=1` — prüfen, welche Karten betroffen sind
4. `make cards-sync YES=1` — endgültig entfernen
5. `make validate-cards-template` — bestätigen, dass keine Drift mehr da ist

### Workflow 3: Neue Karte für bestehenden Provider

```bash
make vendor-cards PROVIDER=Anthropic
make vendor-cards-update YES=1   # SSoT-Sync nach Generierung
make vendor-cards-status
```

### Workflow 4: Bulk-Migration nach Template-Update

```bash
# 1. Vorschau
make cards-sync DRY_RUN=1

# 2. JSON-Report für Audit-Trail
make cards-sync DRY_RUN=1 JSON=1 > sync-plan.json

# 3. Endgültig ausführen
make cards-sync YES=1

# 4. Validieren
make validate-cards-template
```

---

## Thinking-Override in Vendor Cards (ab v4.7.1)

**Opt-in Escape-Hatch** für die Thinking-SSoT-Auflösung. Die Probe aus
der Model Card (`thinking_probe_detected`) ist normalerweise SSoT — der
Override erlaubt es, für Spezialfälle (Cost-Benchmark, A/B-Test,
Provider-seitige reasoning-Steuerung) einen abweichenden Wert zu setzen.

### SSoT-Auflösung (`utils/model_utils.resolve_effective_thinking`)

```
1. aktiver thinking_override?  → (override_value, "override")  + Audit-Log [ThinkingOverride]
2. Card thinking_probe_detected? → (card_value, "card_probe")
3. nichts                       → (None, "none")
```

### Schema (`config/card_template_vendor.yaml → optional_fields`)

```yaml
thinking_override:
  value: false                              # bool, Pflicht
  reason: "Cost-Benchmark: CoT-Suppression fuer faire Speed-Vergleiche"
  active_until: "2026-12-31"                # Optional, ISO-8601, Auto-Expiry
```

### Aktivierungs-Regeln (`_is_override_active`)

| Bedingung | Anforderung |
|---|---|
| `value` | muss `true` oder `false` sein (bool, Pflicht) |
| `reason` | Pflicht (Whitespace-only zählt als leer) |
| `active_until` | Optional, ISO-8601; muss in der Zukunft liegen, naive wird UTC interpretiert |
| Bei Inaktivität | Card-Probe gewinnt automatisch |

**Audit-Trail:** Jede Override-Anwendung wird geloggt:
`[ThinkingOverride] model_id: override active (value=…, reason=…)`.

**Auto-Expiry:** `active_until` verhindert ewige Drift zwischen Card
und Config. Nach Ablauf greift die Card-Probe automatisch.

### Beispiel-Use-Cases

| Szenario | Empfehlung |
|---|---|
| Standard-Benchmark | Card-Probe (kein Override) |
| Cost-Benchmark (CoT aus, fairer Speed-Vergleich) | `value: false` mit `reason` + `active_until` |
| A/B-Test Thinking vs. Non-Thinking | `value: …` mit verschiedenen `active_until`-Daten |
| Provider-API mit eigener Reasoning-Steuerung | Override als Brücke, bis Probe automatisch erkennt |
| Alte Probe-Daten (>30 Tage) | Re-Probe via `make probe-thinking MODEL=…` |

### Konsumenten

- `utils/model_utils.resolve_effective_thinking()` — SSoT-Auflösung
- `utils/base_runner.py:121` — reicht `provider=provider` an `resolve_token_budget()` durch
- `utils/providers/*.py` — 5 alte Call-Sites (Backward-Compat ohne `provider`-Argument)

**Effekt auf Token-Budget (Runner-Consumer):**

| Szenario | Token-Budget-Verhalten |
|---|---|
| `thinking_override.value: false` aktiv | **KEIN** 5× Reasoning-Multiplikator (Cost-Benchmark-fair) |
| `thinking_override.value: true` auf Non-Reasoning-Modell | 5× Multiplikator (A/B-Test) |
| Card-Probe `false` trotz magistral-Trigger im Namen | **KEIN** 5× (Card-First) |
| Card fehlt, Provider ohne Override | Trigger-Liste (Backward-Compat) |

**Methodik-Doku:** `docs/THINKING_PROBE.md` (Drei-Signal-Hierarchie,
Multi-Prompt-Aggregation, SSoT-Auflösung, Discovery-Inventar).
**Discovery-Roh-Daten:** `docs/THINKING_TAGS_INVENTORY.md` +
`_M4/_SPARK/_CLOUD.md`.
**Implementierung:** `utils/model_utils.py` (SSoT) + `utils/base_runner.py`
(Consumer) + `tests/test_thinking_override.py` (24 Tests) +
`tests/test_base_runner_thinking_budget.py` (17 Tests).

---

## Sampling-Defaults (ab v4.7.2)

Modell-spezifische Sampling-Parameter, die in der Card mit `null` belassen werden
können — dann greift der Pipeline-Default. Sobald ein Wert gesetzt ist, wird
er in der Asset-Pipeline und im Thinking-Probe respektiert.

| Feld | Typ | Default | Zweck | Provider-spezifisch? |
| --- | --- | --- | --- | --- |
| `top_p` | float | `null` | Nucleus-Sampling-Threshold (0.0–1.0) | nein (universell) |
| `top_k` | int | `null` | Top-K-Limit für Token-Auswahl | nein (universell) |
| `repetition_penalty` | float | `null` | Strafterm für wiederholte Tokens (oft > 1.0) | nein (universell) |
| `frequency_penalty` | float | `null` | Wiederholungs-Strafe basierend auf Frequenz | ja (OpenAI) |
| `presence_penalty` | float | `null` | Anwesenheits-Strafe basierend auf Vorkommen | ja (OpenAI) |
| `seed` | int | `null` | Reproduzierbarkeits-Seed | nein (universell) |
| `stop_sequences` | list[str] | `null` | Stop-Sequenzen, bei denen Generierung abbricht | nein (universell) |

**Semantik:**
- Schlüssel vorhanden, Wert `null` → Pipeline-/Provider-Default greift
- Schlüssel vorhanden, Wert gesetzt → Modell-spezifische Konfiguration aktiv
- Schlüssel fehlt → wie `null` (Migration sichert Existenz)

**Bulk-Migration:** `python scripts/dev/add_sampling_keys.py` (idempotent, Dry-Run mit `--dry-run`).

**Beispiel:**
```json
{
  "model_id": "qwen2.5-coder-32b",
  "top_p": 0.8,
  "repetition_penalty": 1.05,
  "stop_sequences": ["\n\nUser:", "###"]
}
```

## Top-Level-Field-Whitelist (ab v4.7.2)

Der Validator (`scripts/dev/validate_model_cards.py`) prüft seit v4.7.2, dass
alle Top-Level-Felder einer Card im Template (`config/card_template_model.yaml`)
definiert sind. Verhalten:

- **`card_status=complete`:** unbekanntes Feld → WARN (Wildwuchs-Schutz)
- **`card_status=draft` oder `minimal`:** unbekanntes Feld → toleriert (experimentelle Felder erlaubt)

Damit lassen sich unbekannte Felder in Drafts explorativ ergänzen, ohne dass
die CI bei `complete`-Cards scheitert. Beim Übergang von `draft` zu `complete`
muss entweder das Feld ins Template aufgenommen oder aus der Card entfernt
werden.

## CLI-Referenz

### `scripts/analysis/validate_cards.py`

```bash
python scripts/analysis/validate_cards.py --card-type {model,provider,all}
python scripts/analysis/validate_cards.py --json
python scripts/analysis/validate_cards.py --fail-on-drift
```

### `scripts/analysis/sync_cards.py`

```bash
python scripts/analysis/sync_cards.py --card-type {model,provider,all}
python scripts/analysis/sync_cards.py --dry-run
python scripts/analysis/sync_cards.py --yes
python scripts/analysis/sync_cards.py --json
```

### `scripts/analysis/generate_vendor_cards.py`

```bash
python scripts/analysis/generate_vendor_cards.py            # alle fehlenden
python scripts/analysis/generate_vendor_cards.py --force    # alle neu
python scripts/analysis/generate_vendor_cards.py --provider "Anthropic"
python scripts/analysis/generate_vendor_cards.py --update [--yes] [--dry-run]
```

### `scripts/analysis/generate_model_cards.py`

Seit v4.7.5 unterstützt das Skript ein optionales `--card-type {model,provider,all}`-Flag für Pipeline-Integration.

```bash
python scripts/analysis/generate_model_cards.py --model-id claude-opus-4-7
python scripts/analysis/generate_model_cards.py --model-id qwen3:14b --provider ollama_local
python scripts/analysis/generate_model_cards.py --interactive
python scripts/analysis/generate_model_cards.py --force --model-id claude-opus-4-7
python scripts/analysis/generate_model_cards.py --json --model-id claude-opus-4-7
python scripts/analysis/generate_model_cards.py --card-type model --json    # alle Modelle als JSON-Report
```

**Hinweis:** Sync bestehender Karten (fehlende Felder ergänzen, entfernte
löschen) ist **nicht** Aufgabe dieses Skripts. Dafür
``python scripts/analysis/sync_cards.py --card-type model [--yes|--dry-run]``
nutzen. Die früheren Flags ``--update`` / ``--yes`` / ``--dry-run`` wurden
in v4.7.5 entfernt (SRP-Trennung zwischen Create und Sync).

### `scripts/analysis/vendor_card_status.py`

```bash
python scripts/analysis/vendor_card_status.py --stale-days 90
python scripts/analysis/vendor_card_status.py --json
python scripts/analysis/vendor_card_status.py --fail-on-unknown
python scripts/analysis/vendor_card_status.py --fail-on-stale
```

---

## Make-Targets

| Target | Zweck | Flags |
|---|---|---|
| `make model-cards` | Model Card Template anlegen | `MODEL=name`, `PROVIDER=key`, `FORCE=1` |
| `make model-card` | Alias für `model-cards` | (siehe oben) |
| `make vendor-cards` | Vendor Card generieren (LLM) | `PROVIDER=name`, `FORCE=1` |
| `make ensure-card` | Eine Card mit Template sync | `MODEL=name`, `DRY=1` |
| `make ensure-cards` | Alle Cards mit Template sync | `ALL=1`, `DRY=1` |
| `make validate-cards` | Konsistenz-Check (tier/summary) | — |
| `make validate-cards-template` | Schema-Validierung gegen YAML | `CARD_TYPE=…`, `JSON=1`, `FAIL_ON_DRIFT=1` |
| `make cards-sync` | SSoT-Sync (add + delete mit Confirm) | `CARD_TYPE=…`, `DRY_RUN=1`, `YES=1`, `JSON=1` |
| `make vendor-cards-update` | `--update` für Provider-Generator | `YES=1`, `DRY_RUN=1` |
| `make cards-sync` | Model-Card-Sync mit Template (SSoT) | `CARD_TYPE=model`, `YES=1`, `DRY_RUN=1` |
| `make vendor-cards-status` | Audit-Readiness-Report | `STALE_DAYS=N`, `JSON=1` |

---

## Troubleshooting

### „Card existiert bereits" bei `make model-cards`

→ Nutze `--force` zum Überschreiben oder einen anderen `--model`-Namen:

```bash
make model-cards MODEL=neuer-name
make model-cards MODEL=claude-opus-4-7 FORCE=1
```

### „Feld fehlt" im Validator

→ `make cards-sync YES=1` ergänzt fehlende Felder automatisch mit Defaults.

### „Feld hat Sentinel-Wert" im Validator

→ Wert ist `null` / `"TODO"` / `"unknown"` — Karte manuell oder via
LLM-Generator befüllen. Die Sentinel-Erkennung ist absichtlich, damit
unbefüllte Karten auffallen.

### „Drift-Feld" im Validator

→ Feld ist in der Karte, aber nicht im Template. Zwei Optionen:

1. **Feld ins Template aufnehmen** (YAML + Python-Dict)
2. **Feld aus Karte entfernen** via `make cards-sync YES=1`

### „Vendor Card hat unbekannte deployment-Sub-Felder"

→ `make vendor-cards-status` zeigt, welche Sub-Felder betroffen sind.
Manuell befüllen (siehe `config/card_template_vendor.yaml → deployment`).

### Sync-Bestätigung: pro Karte oder pro Feld?

→ Pro **Karte** (gesammelt). Wenn z.B. 3 Felder aus `llamacpp.json`
entfernt werden sollen, kommt **eine** Abfrage mit der Feld-Liste.

### Karte wurde nicht synchronisiert (Löschung abgelehnt)

→ Das ist gewollt: atomarer Sync. Entweder `--yes` setzen oder im
Template anpassen, dann erneut syncen.

### `make cards-sync YES=1` löscht trotzdem nicht

→ Prüfen, ob das Feld als Pflicht-ID geschützt ist (`provider_id`,
`model_id`) oder unter `tooluse_*` fällt (Legacy). Diese werden nie
automatisch gelöscht — bewusste Entscheidung.

---

## Vendor-Kanonisierung in Model Cards (ab v4.9.0)

Das Feld `vendor` in Model Cards bezeichnet den **kanonischen Hersteller-Namen**
(nicht den API-Anbieter, nicht den langen Firmennamen). Eine kanonische Liste
ist SSoT in `config/classification_taxonomy.json → manufacturers → values`.

### Aktuell gültige Hersteller-Namen

| `vendor`-Wert | Bekannte Aliases (werden normalisiert) |
|---|---|
| `Alibaba` | "Alibaba Cloud", "Qwen / Alibaba Cloud", "HauhauCS / Qwen" |
| `Anthropic` | — |
| `DeepSeek` | — |
| `Google` | "Google DeepMind", "Google / UndiX (Community)" |
| `Meta` | "Meta AI", "Meta Llama" |
| `MiniMax` | — |
| `Mistral AI` | "Mistral" |
| `Moonshot AI` | "Moonshotai", "Kimi" |
| `NousResearch` | "Nous Research" |
| `NVIDIA` | "Nvidia" |
| `OpenAI` | — |
| `xAI` | "Grok", "xAI (Grok)" |
| `Zhipu AI` | "Z.ai", "Z.ai (Zhipu AI)" |

### Normalisierung im Web-Export

`scripts/web_export.py` normalisiert das `vendor`-Feld zur Laufzeit via
`_normalize_vendor()` — übersetzt bekannte Alias-Strings auf den kanonischen
Wert. Unbekannte Werte werden mit `WARNING` geloggt. Die Alias-Map wird einmalig
aus der Taxonomy geladen (`_build_vendor_alias_map()`).

**Ziel:** Auch wenn eine Card noch einen Alias-String enthält (z.B. nach
einem Batch-Migration-Fehler), erscheint im Frontend immer der kanonische Name.

### Vendor-Prüfung im Validator (`scripts/verify_model_cards.py`)

`verify_model_cards.py` prüft seit v4.9.0, ob `vendor` in der kanonischen Liste
steht. Abweichungen → `🏭`-Warnung. Kanonische Liste wird aus der Taxonomy
gelesen (graceful: leeres Set wenn Taxonomy nicht geladen werden kann).

### Workflow: Neuen Hersteller aufnehmen

1. Eintrag in `config/classification_taxonomy.json → manufacturers → values` ergänzen:
   - `label` — kanonischer Name (= `vendor`-Wert in Cards)
   - `description` — kurze Beschreibung
   - `aliases` — alle bekannten Schreibvarianten (als Liste)
   - `jurisdiction` — Rechtsraum (z.B. "US", "EU", "CN")
2. Betroffene Model Cards aktualisieren (Batch per `jq` oder manuell)
3. `make validate-cards` — prüfen dass kein `🏭`-Fehler mehr auftritt

---

## Datenpflege-Verifikation: profile_verified (ab v4.9.0)

Sowohl Model Cards als auch Vendor Cards haben seit v4.9.0 zwei optionale
Felder für redaktionelle Qualitätssicherung:

| Feld | Typ | Default | Bedeutung |
|---|---|---|---|
| `profile_verified` | `bool` | `false` | Inhaltliche Felder wurden manuell recherchiert und verifiziert |
| `profile_verified_at` | `str` | `null` | Datum der letzten Verifikation (ISO 8601: YYYY-MM-DD) |

Das Flag ist **kein Hard-Gate** (der Benchmark läuft unabhängig davon).
Es dient als Audit-Signal für redaktionelle Vollständigkeit.

### Was fällt unter profile_verified?

**Model Cards — verifizierbare Felder:**
`display_name`, `developer`, `vendor`, `origin_country`, `developer_jurisdiction`,
`model_family`, `model_version`, `parameter_architecture`, `params_total_b`,
`params_active_b`, `context_window_k`, `knowledge_cutoff`, `input_modalities`,
`output_modalities`, `supports_tool_use`, `architecture_tags`, `primary_focus`,
`deployment_type`, `local_deployment_possible`, `license`, `license_url`,
`commercial_use_allowed`, `weights_license_tier`, `input_price_per_1m`,
`output_price_per_1m`, `weights_provenance_risk`, `weights_provenance_risk_rationale`,
`summary`, `strengths`, `known_limitations`, `judge_context_hint`, `use_case_primary`

**Model Cards — NICHT verifizierbar (automatisch gesetzt):**
`thinking_probe_*`, `cot_marker_family`, `cot_tags_detected`, `tooluse_*`,
`generated_at`, `size_class`, `model_id`, `card_status`, `unknown`,
Sampling-Parameter (`temperature`, `top_p`, etc.), `heritage_ids`, `system_prompt_override`

**Vendor Cards — verifizierbare Felder:**
`company`, `headquarters`, `founding_year`, `api_base_url`, `api_documentation_url`,
`deployment.*`, `privacy_note`, `last_verified_at`, `verification_source`

**Vendor Cards — NICHT verifizierbar:**
`provider_id`, `display_name`, `notable_models`, `stats`, `pricing_model`,
`unknown`, `generated_at`

### Workflow

```bash
# Welche Model Cards sind noch nicht verifiziert?
jq -r 'select(.profile_verified == false) | .model_id' \
   benchmark_scores/model_cards/*.json

# Welche Vendor Cards sind noch nicht verifiziert?
jq -r 'select(.profile_verified == false) | .provider_id' \
   benchmark_scores/vendor_cards/*.json

# Alle Model Cards nach Verifikation mit jq auf false setzen (Migration)
for f in benchmark_scores/model_cards/*.json; do
  [[ "$f" == *"_index.json" ]] && continue
  jq 'if has("profile_verified") then . else . + {"profile_verified": false, "profile_verified_at": null} end' \
     "$f" > /tmp/mc.json && mv /tmp/mc.json "$f"
done
```

### verify_model_cards.py

`scripts/verify_model_cards.py` gibt seit v4.9.0 `🔍`-Warnungen aus:
- `profile_verified` fehlt → Hinweis auf fehlende Migration
- `profile_verified == false` → Hinweis auf noch nicht verifizierten Inhalt

---

## Editor-Prompts: Redaktionelle LLM-Aufgaben (ab v4.9.0)

`config/editor_prompts.yaml` enthält kuratierte Prompts für Datenpflege-Aufgaben,
die ein Operator an ein leistungsfähiges LLM mit Web-Recherche delegiert.
Diese Prompts sind **kein Teil der Benchmark-Logik** — sie dienen nur der
redaktionellen Qualitätssicherung.

### Verfügbare Prompts

| Prompt-Schlüssel | Ziel | Filter |
|---|---|---|
| `vendor_card_verification` | Statische Hersteller-Infos verifizieren (Sitz, Compliance, DSGVO) | Vendor Cards mit `profile_verified: false` |
| `model_card_verification` | Modell-Metadaten recherchieren/ergänzen (Params, Pricing, Summary) | Model Cards mit `profile_verified: false` |

### Empfohlene Modelle

Claude Opus 4+, GPT-5+, Gemini 2.5 Pro (mit Web-Recherche-Fähigkeit)

### Typischer Workflow

```
1. Prompt aus editor_prompts.yaml kopieren (Schlüssel → prompt: | Block)
2. An LLM mit Datei-Schreibzugriff + Web-Recherche schicken
3. LLM liest Cards, recherchiert, aktualisiert Felder, setzt profile_verified: true
4. Operator prüft git diff, commitet
```

**Einschränkungen des Prompts (model_card_verification):**
- Probe-Felder (`thinking_probe_*`, `cot_*`) → **gesperrt** (automatisch)
- ToolUse-Benchmark-Felder (`tooluse_*`) → **gesperrt** (automatisch)
- Sampling-Parameter → **gesperrt** (Operator-Entscheidung)
- `supports_tool_use` → **recherchierbar** (öffentliche Tatsache, aber Tooluse-Benchmark kann überschreiben)

---

## Verwandte Dokumentation

- `docs/ARCHITECTURE.md` — SSoT-Architektur des Projekts
- `docs/MODEL_CLASSIFICATION.md` — Modell-Klassifikationslogik
- `docs/MAINTENANCE_LOG.md` — Changelog (Phase 24/25 Einträge)
- `docs/USER_GUIDE.md` — End-Nutzer-Dokumentation
- `config/editor_prompts.yaml` — Kuratierte LLM-Datenpflege-Prompts
- `config/classification_taxonomy.json → manufacturers` — Kanonische Hersteller-Liste (SSoT)
