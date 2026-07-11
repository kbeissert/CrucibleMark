# CrucibleMark: Card-Management

**Zielgruppe:** Entwickler, die Model- oder Provider-Cards erstellen, prüfen oder mit dem Template synchronisieren wollen.

**Inhalt:**

- [Überblick](#überblick)
- [Card-Typen](#card-typen)
- [SSoT-Architektur](#ssot-architektur)
- [Card-Lifecycle](#card-lifecycle)
- [Card-Lifecycle v2 (ab v4.10.0)](#card-lifecycle-v2-ab-v4100)
  - [`make card-create MODEL=<id>`](#make-card-create-modelid)
  - [`make card-validate [MODEL=<id>]`](#make-card-validate-modelid)
  - [`make card-research [MODEL=<id>]`](#make-card-research-modelid)
  - [Lock-Mechanismus im Detail](#lock-mechanismus-im-detail)
  - [Pre-Check-Heuristik (CJK / Em-Dash)](#pre-check-heuristik-cjk--em-dash)
  - [CLI-Referenz: `manage_model_cards.py --mode research`](#cli-referenz-manage_model_cardspy--mode-research)
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
- `scripts/web_export/entry_builders.py` — Tag-Filter via `_normalize_export_tags()`

### Workflow: Neuen Tag einführen

1. Prüfen, ob der Tag semantisch zur bestehenden Registry passt.
2. Entscheiden, ob `reserved` (Code-Effekt) oder `informational` (nur Filter).
3. Eintrag in `config/card_vocabulary.yaml` mit Beschreibung und `since`-Version.
4. Bei `reserved`: Konsument-Code (z.B. `scripts/web_export/`, `model_utils.py`) implementieren.
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

## Card-Lifecycle v2 (ab v4.10.0)

Drei neue Make-Targets decken den kompletten Lebenszyklus einer Model Card ab,
von der Erstellung aus `provider_config.yaml` über die Struktur-Sync mit dem
Template bis zur inhaltlichen LLM-Recherche:

| Make-Befehl | Wirkung | LLM? |
|---|---|---|
| `make card-create MODEL=<id>` | Legt eine neue Card aus `provider_config.yaml` an. Validiert die ID (Schutz vor Slug-Mismatch-Bug). | nein |
| `make card-validate` / `make card-validate MODEL=<id>` | Synchronisiert Cards mit dem SSoT-Template (deterministisch, kein LLM). | nein |
| `make card-research` / `make card-research MODEL=<id>` | LLM-Recherche der Card-Inhalte (Preise, Beschreibung, Sonderzeichen). Lock via `profile_verified`. | ja |

> **Hinweis:** Der bestehende `make cards-sync` bleibt für Vendor-Cards und
> Cross-Type-Sync aktiv. `make card-validate` ist ein **Model-Card-spezifischer
> Wrapper** mit identischer Sync-Engine, der `MODEL=<id>` als Shortcut für
> Einzelkarten-Sync unterstützt.

### `make card-create MODEL=<id>`

Skeleton + Pre-Fill aus `config/provider_config.yaml`. Schutz vor
Slug-Mismatch-Bug (Punkte in der ID werden hart abgelehnt, weil
`utils/model_utils._safe_name` Punkte zu Underscores konvertiert).

**Pipeline:**

1. **ID-Validierung** — `SystemExit` falls die ID einen `.` enthält.
2. **Provider-Lookup** via `utils.config_validator.ConfigValidator`:
   - `id` → `model_id`
   - `name` → `display_name` (überschreibt nur, wenn aktueller Wert `"TODO"`)
   - `<provider.name>` → `developer` (gleiche Regel)
3. **Skeleton** via `utils.card_utils.ensure_card(model_id, provider=…)` (SSoT).

**Beispiele:**

```bash
# Vorschau
make card-create MODEL=claude-sonnet-4-6 DRY=1

# Card anlegen (Skeleton + display_name + developer aus provider_config)
make card-create MODEL=claude-sonnet-4-6

# Card existiert bereits → SystemExit, Empfehlung: card-validate / card-research
make card-create MODEL=claude-sonnet-4-6
# ⚠️  Card existiert bereits: benchmark_scores/model_cards/claude-sonnet-4-6.json
#    Verwende 'make card-research' fuer inhaltliche Updates
#    oder 'make card-validate' fuer Struktur-Sync.

# Override (z.B. bestehende Card ueberschreiben)
make card-create MODEL=claude-sonnet-4-6 YES=1
```

**Flags:**

| Flag | Effekt |
|---|---|
| `DRY=1` | Vorschau ohne Schreiben |
| `YES=1` | Bestehende Card überschreiben (ohne --yes: SystemExit) |
| `PROVIDER=<key>` | Expliziter Provider-Key für `ensure_card` (z.B. `anthropic`) |

**Fehler:**

| Situation | Verhalten |
|---|---|
| ID enthält `.` | `SystemExit` mit Slug-Mismatch-Hinweis |
| Model nicht in `provider_config.yaml` | `SystemExit` mit Top-10 verfügbaren IDs |
| Card existiert bereits (ohne `YES=1`) | `SystemExit`, Empfehlung `card-research` / `card-validate` |

### `make card-validate [MODEL=<id>]`

Synchronisiert Cards mit dem SSoT-Template (deterministisch, kein LLM).
Addiert fehlende Template-Felder, entfernt Extras (mit Bestätigung oder
`YES=1`). Wrapper um `scripts/analysis/sync_cards.py --card-type model`
mit komfortablem `MODEL=<id>`-Flag.

**Pipeline:**

1. `utils.card_sync.plan_sync(card_path, "model")` → `SyncPlan`
2. `apply_sync(...)` mit `dry_run` / `yes` aus dem Aufruf

**Beispiele:**

```bash
# Alle Model-Cards syncen (mit Bestaetigung pro Karte)
make card-validate

# Alle Model-Cards syncen (Lösch-Bestätigung auto-ja)
make card-validate YES=1

# Vorschau (welche Adds/Deletes würden passieren?)
make card-validate DRY=1

# Einzelne Card
make card-validate MODEL=claude-sonnet-4-6 YES=1

# JSON-Report fuer CI-Parsing
make card-validate DRY=1 JSON=1
```

**Hinweis — One-Time-Churn:** Wenn das Template neue Felder bekommt (z.B.
`profile_verified_by` in v4.10.0), meldet `make card-validate` für jede
bestehende Card einen "add" für diese Felder. Mit `YES=1` einmalig
anwenden, danach idempotent.

### `make card-research [MODEL=<id>]`

LLM-Recherche der Card-Inhalte (Preise, Beschreibung, Sonderzeichen).
**Lock-Mechanismus** via `profile_verified`: `true` → `false` zu Beginn,
zurück auf `true` am Ende. Bei Abbruch bleibt `false` als Resumption-Marker.

**Pipeline pro Card:**

1. **Lock**: `profile_verified=false`, `profile_verified_at=null`,
   `profile_verified_by=null`, `last_modified_at=YYYY-MM-DD`
2. **Backup**: `<card>.pre-research.bak` (Sicherheitsnetz für Diff-Inspektion)
3. **Pre-Check-Heuristik**: scan `summary`, `strengths`, `known_limitations`,
   `judge_context_hint` auf CJK-Zeichen + Em-Dash → Findings
4. **LLM-Call** mit `editor_prompts.model_card_verification` als User-Prompt
5. **Apply Diff**: `suggested`-Werte aus LLM-Response übernehmen (für
   Felder, die bereits in der Card existieren — keine neuen Felder)
6. **Operator-Protected-Fields preserven** (`model_id`, `generated_at`,
   `thinking_probe_*`, `tooluse_*`, Sampling-Parameter, `heritage_ids`, …)
7. **Validate** gegen `utils.card_template.load_card_template("model")`
8. **Un-Lock**: `profile_verified=true`, `profile_verified_at=YYYY-MM-DD`,
   `profile_verified_by="llm:<model>"`, `last_modified_at=YYYY-MM-DD`
9. **Delete Backup** bei Erfolg

**Beispiele:**

```bash
# Alle Cards mit profile_verified != true (Resumption-First)
make card-research

# Einzelne Card
make card-research MODEL=claude-sonnet-4-6

# Auch verifizierte Cards (Override)
make card-research FORCE=1

# Vorschau: zeigt LLM-Plan, schreibt NICHTS, setzt KEINEN Lock
make card-research MODEL=claude-sonnet-4-6 DRY=1
```

**Defaults (Resumption-First):**

- Ohne `--force`: nur Cards mit `profile_verified != true` werden
  bearbeitet (gleicher Skip-Pfad wie Phase-1-`manage_model_cards.py
  --mode check`).
- Mit `FORCE=1`: auch verifizierte Cards.
- Dry-Run: zeigt den LLM-Plan, ändert **nichts** an der Card
  (kein Lock, kein Backup, keine Findings werden geschrieben).

**Fehler-Verhalten:**

| Situation | Verhalten |
|---|---|
| LLM-Fehler nach `MAX_RETRIES` (3) | Lock bleibt offen (`profile_verified=false`), Backup bleibt liegen. Nächster Lauf ohne `--card` nimmt die Karte in den Resumption-Pfad. |
| User-Ctrl+C | Gleiche Exception-Safety wie LLM-Fehler (try/except um den Write-Pfad). |
| Card nicht parsebar | `SystemExit` bevor der Lock gesetzt wird (kein Schaden). |
| `DRY=1` | Kein Lock, kein Backup, kein Write — nur Markdown-Report mit LLM-Plan. |

**Exit-Code:** `1` wenn 1+ Cards nach der Recherche noch
`profile_verified=false` haben (CI-Signal). `0` wenn alle erfolgreich
oder gar keine Targets vorhanden.

### Lock-Mechanismus im Detail

Der Lock nutzt das vorhandene `profile_verified`-Feld als
Resumption-Marker — **keine separaten `.lock`-Dateien, kein `flock`**.

```
┌──────────────────┐  Card gefunden    ┌─────────────────────────┐
│ profile_verified │ ─────────────────▶ │ profile_verified=false  │
│ = true (alt)     │                   │ profile_verified_at=null│
└──────────────────┘                   │ profile_verified_by=null│
                                       │ last_modified_at=2026-…  │
                                       │ + <card>.pre-research.bak│
                                       └────────────┬────────────┘
                                                    │
                       ┌────────────────────────────┴────────────────┐
                       │                                             │
                       ▼ LLM OK                                     ▼ LLM Fehler / Abbruch
                ┌──────────────────────┐                    ┌────────────────────┐
                │ profile_verified=true│                    │ profile_verified   │
                │ profile_verified_at= │                    │ =false (unverändert)│
                │   2026-06-18         │                    │ Backup bleibt      │
                │ profile_verified_by= │                    └────────────────────┘
                │   "llm:gpt-5.4"      │
                │ last_modified_at=    │
                │   2026-06-18         │
                │ + Backup geloescht   │
                └──────────────────────┘
```

**Warum kein File-Lock?**

- Cards werden auch von anderen Tools (Web-Export, Review-Generator,
  `ensure_card_structure.py`) sequenziell gelesen/geschrieben. Ein
  `flock` würde blockieren.
- `profile_verified=false` ist **bereits semantisch der
  "unverifiziert"-Zustand** — der Lock-Mechanismus nutzt diesen
  vorhandenen Marker.
- Resumption: ein abgebrochener `card-research`-Lauf setzt die Card
  in den "zu recherchieren"-Zustand zurück. Der nächste Lauf findet
  sie automatisch.

**Wann `profile_verified` von Hand auf `true` setzen?**

Falls der LLM-Lauf fehlschlägt und der Operator die Recherche manuell
(abschließt, ohne LLM), dann direkt in der JSON-Datei:

```bash
jq '.profile_verified = true | .profile_verified_at = "2026-06-18" | .profile_verified_by = "human"' \
   benchmark_scores/model_cards/<card>.json > /tmp/x.json && mv /tmp/x.json …
```

### Pre-Check-Heuristik (CJK / Em-Dash)

`manage_model_cards.py --mode research` führt VOR dem LLM-Call einen
deterministischen Scan der redaktionellen Felder aus:

- **CJK-Zeichen** in `summary`, `strengths`, `known_limitations`,
  `judge_context_hint` (Unicode-Bereiche `U+4E00–U+9FFF`, `U+3040–U+30FF`,
  `U+AC00–U+D7AF` + Erweiterungen)
- **Em-Dash (`—`)** speziell in `summary` (laut Editor-Prompt Schritt 5
  verboten)

Beide Klassen werden als `severity="error"` Findings an die
LLM-Response angehängt, damit der Operator sie im Report sieht.
Der LLM wird in Phase 3 die Pre-Findings als zusätzlichen Kontext
bekommen.

### CLI-Referenz: `manage_model_cards.py --mode research`

```bash
python scripts/manage_model_cards.py --mode research
python scripts/manage_model_cards.py --mode research --card claude-sonnet-4-6
python scripts/manage_model_cards.py --mode research --force
python scripts/manage_model_cards.py --mode research --card <id> --dry-run
python scripts/manage_model_cards.py --mode research --max-retries 5
python scripts/manage_model_cards.py --mode research --model gpt-5.4 \
    --base-url http://localhost:1234/v1
```

| Flag | Default | Effekt |
|---|---|---|
| `--card <id>` | — | Nur diese eine Card bearbeiten (sonst: alle mit `profile_verified != true`) |
| `--force` | off | Auch verifizierte Cards einbeziehen |
| `--dry-run` | off | Nur Vorschau — kein Lock, kein Backup, kein Write |
| `--model <name>` | aus `benchmark_config.yaml` | LLM-Modell überschreiben |
| `--base-url <url>` | `https://api.openai.com/v1` | OpenAI-kompatibler Endpoint |
| `--api-key-env <name>` | `OPENAI_API_KEY` | Name der Env-Variable mit API-Key |
| `--max-retries <n>` | 3 | LLM-Retry-Budget |

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

### Workflow 5: Neue Karte aus provider_config (v4.10.0+)

```bash
# 1. Vorschau — was wuerde geschrieben?
make card-create MODEL=claude-sonnet-4-6 DRY=1

# 2. Card anlegen
make card-create MODEL=claude-sonnet-4-6

# 3. Inhaltliche Recherche via LLM
make card-research MODEL=claude-sonnet-4-6

# 4. Struktur mit Template sync (falls spaeter Felder dazukommen)
make card-validate MODEL=claude-sonnet-4-6 YES=1
```

### Workflow 6: Resumption nach abgebrochener Recherche (v4.10.0+)

```bash
# Welche Cards haben offenen Lock? (alle mit profile_verified != true)
jq -r 'select(.profile_verified != true) | .model_id' \
   benchmark_scores/model_cards/*.json

# Diese Cards werden beim naechsten Lauf automatisch aufgegriffen:
make card-research

# Force-Modus falls eine bereits-verifizierte Karte neu durchsucht werden soll:
make card-research MODEL=claude-sonnet-4-6 FORCE=1
```

### Workflow 7: One-Time-Seed fuer neue Template-Felder (v4.10.0+)

Wenn das Template neue Felder bekommt (z.B. `profile_verified_by`,
`last_modified_at`), meldet `make card-validate` für jede bestehende
Card einen "add". Statt `make card-validate YES=1` (was auch alle
anderen Adds anwendet) gibt es zwei gezielte Alternativen:

```bash
# 1. Nur Skeleton-Defaults (idempotent, ueberschreibt NICHTS):
make ensure-cards ALL=1

# 2. Re-Sync aller Cards mit dem erweiterten Template (deterministisch):
make card-validate YES=1
```

`make ensure-cards` ruft `utils.card_utils.ensure_card()` pro Card
auf, das nur fehlende Felder ergänzt. Bereits gesetzte Werte
(einschließlich `"TODO"`-Platzhalter) bleiben unverändert.

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
| `make model-cards` | Model Card Template anlegen (LLM-generiert) | `MODEL=name`, `PROVIDER=key`, `FORCE=1` |
| `make model-card` | Alias für `model-cards` | (siehe oben) |
| `make vendor-cards` | Vendor Card generieren (LLM) | `PROVIDER=name`, `FORCE=1` |
| `make ensure-card` | Eine Card mit Template sync | `MODEL=name`, `DRY=1` |
| `make ensure-cards` | Alle Cards mit Template sync | `ALL=1`, `DRY=1` |
| `make validate-cards` | Konsistenz-Check (tier/summary) | — |
| `make validate-cards-template` | Schema-Validierung gegen YAML | `CARD_TYPE=…`, `JSON=1`, `FAIL_ON_DRIFT=1` |
| `make cards-sync` | SSoT-Sync (beide Card-Typen, add + delete mit Confirm) | `CARD_TYPE=…`, `DRY_RUN=1`, `YES=1`, `JSON=1` |
| `make card-create` | Neue Model Card aus `provider_config.yaml` anlegen (v4.10.0) | `MODEL=name`, `PROVIDER=key`, `DRY=1`, `YES=1` |
| `make card-validate` | Model-Card-Sync mit `MODEL=<id>` Shortcut (v4.10.0) | `MODEL=name`, `YES=1`, `DRY=1`, `JSON=1` |
| `make card-research` | LLM-Inhalts-Recherche mit `profile_verified`-Lock (v4.10.0) | `MODEL=name`, `FORCE=1`, `DRY=1` |
| `make vendor-cards-update` | `--update` für Provider-Generator | `YES=1`, `DRY_RUN=1` |
| `make model-cards-update` | DEPRECATED-Alias für `cards-sync CARD_TYPE=model` | `YES=1`, `DRY_RUN=1` |
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

### „Card-ID enthält einen Punkt" bei `make card-create`

→ Schutz vor Slug-Mismatch-Bug. Punkte in der ID werden via
`_safe_name` zu Underscores konvertiert, was zu versteckten
Lookup-Mismatches führt. Slashes für Vendor-Präfixe verwenden
(`z-ai/glm-5.2` statt `z-ai.glm-5.2`).

### „Card existiert bereits" bei `make card-create`

→ Default: `SystemExit` (kein Force-Overwrite). Für Updates:
- `make card-validate MODEL=<id> YES=1` für Struktur-Sync
- `make card-research MODEL=<id>` für inhaltliche LLM-Recherche
- `make card-create MODEL=<id> YES=1` zum expliziten Überschreiben

### `make card-research` Lock bleibt offen

→ Der Lock (`profile_verified=false`) ist der Resumption-Marker bei
Abbruch. Drei Optionen:
1. **Nächster `make card-research`** ohne `--card` nimmt die Karte
   automatisch in den Resumption-Pfad (sie ist nicht `profile_verified=true`).
2. **Manuell abschließen** wenn die Recherche ohne LLM geklappt hat:
   `jq '.profile_verified = true | .profile_verified_at = "YYYY-MM-DD" | .profile_verified_by = "human"' card.json > /tmp/x.json && mv /tmp/x.json card.json`
3. **Mit `FORCE=1` neu starten** wenn die Karte bereits `profile_verified=true`
   war und neu durchsucht werden soll.

### `<card>.pre-research.bak` bleibt nach erfolgreicher Recherche liegen

→ Sehr selten, nur wenn `unlink()` auf dem Backup fehlschlägt (z.B.
read-only Filesystem). Manuell löschen — das Backup ist nur ein
Sicherheitsnetz für die Diff-Inspektion, kein notwendiger Zustand.

### `make card-research` ohne API-Key

→ `OPENAI_API_KEY` (oder die via `--api-key-env` gesetzte Variable)
muss gesetzt sein. Für lokale llama.cpp-Server:
`OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1 make card-research …`

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

`scripts/web_export/filters.py` normalisiert das `vendor`-Feld zur Laufzeit via
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

Sowohl Model Cards als auch Vendor Cards haben seit v4.9.0 Felder für
redaktionelle Qualitätssicherung:

| Feld | Typ | Default | Bedeutung | Seit |
|---|---|---|---|---|
| `profile_verified` | `bool` | `false` | Inhaltliche Felder wurden manuell recherchiert und verifiziert | v4.9.0 |
| `profile_verified_at` | `str` | `null` | Datum der letzten Verifikation (ISO 8601: YYYY-MM-DD) | v4.9.0 |
| `profile_verified_by` | `str` | `null` | Wer hat verifiziert: `"human"` \| `"llm:<model>"` \| `null` | v4.10.0 |
| `last_modified_at` | `str` | `null` | Datum der letzten inhaltlichen Änderung (ISO 8601) | v4.10.0 |

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

**Oder automatisiert via `make card-research`** (v4.10.0+) — der LLM-Call,
das Lock-Management und das Operator-Protected-Field-Preset laufen über
`scripts/manage_model_cards.py --mode research`. Der Prompt aus
`editor_prompts.yaml` wird als User-Prompt verwendet, der System-Prompt ist
auf Recherche-Aufgaben spezialisiert (Preise, Sonderzeichen, Quellen).

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
