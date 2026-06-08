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
| **Provider Card** | `benchmark_scores/provider_cards/{slug}.json` | `utils/provider_card_template._PROVIDER_CARD_TEMPLATE` |
| **Model Card** | `benchmark_scores/model_cards/{slug}.json` | `utils/card_utils._CARD_TEMPLATE` |

Zusätzlich gibt es zwei **deklarative YAML-Templates** (`config/card_template_*.yaml`),
die für den **Validator** genutzt werden — sie beschreiben zusätzlich *welcher
Konsument* welches Feld liest. Beide SSoT-Layer (Python-Dict + YAML) sind seit
Phase 24 dokumentiert und werden vom Sync-Workflow zusammengeführt.

---

## Card-Typen

### Provider Card

Beschreibt einen **API-/Cloud-Anbieter**: Unternehmen, Sitz, Gründungsjahr,
Pricing-Modell, Deployment-/Compliance-Subobjekt (CLOUD-Act, GDPR, etc.),
Datenschutz-Hinweis, gemessene Performance-Statistiken.

Felder (16 Pflicht, 3 Optional): siehe `config/card_template_provider.yaml`.

### Model Card

Beschreibt ein **einzelnes Modell**: Identität, Deployment-Typ, Architektur,
Lizenz, Pricing, Thinking-Probe-Ergebnisse, Tool-Use-Support.

Felder (39 Pflicht, 6 Optional): siehe `config/card_template_model.yaml`.

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
                │  utils/{card_utils,provider_card_template}   │
                │  .py  (Python-Dict SSoT für Generatoren)      │
                └──────────────────┬────────────────────────────┘
                                   │  ensure_card / normalize
                                   ▼
                ┌───────────────────────────────────────────────┐
                │  scripts/analysis/{generate_model_cards,      │
                │  generate_provider_cards}.py                  │
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

---

## Card-Lifecycle

### 1. Erstellen

**Manuell (eine Karte):**

```bash
# Model Card
python scripts/analysis/generate_model_cards.py --model claude-opus-4-7

# Provider Card
python scripts/analysis/generate_provider_cards.py --provider "Anthropic"
```

**Batch (alle fehlenden):**

```bash
make model-cards
make provider-cards
```

### 2. Felder ergänzen (vorwärts)

Wenn ein neues Feld ins Template aufgenommen wird, ergänzen
`ensure_card()` und `ensure_provider_card()` fehlende Felder mit
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

Validator-Issue-Typen:
- `missing_required` — Pflichtfeld fehlt komplett
- `unknown_sentinel` — Pflichtfeld hat Sentinel-Wert (`null`, `"TODO"`, `"unknown"`, `""`, leere Liste)
- `drift_extras` — Feld außerhalb des Templates (Toleranz: `tooluse_*` Legacy)
- `missing_sub_field` — Sub-Feld fehlt (z.B. `deployment.cloud_act_exposure`)
- `parse_error` — JSON-Parse-Fehler

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
make provider-cards-update
make provider-cards-update YES=1
make provider-cards-update DRY_RUN=1

# Über den Model-Generator
make model-cards-update
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
make provider-cards-status                    # default 90 Tage
make provider-cards-status STALE_DAYS=30      # aggressiver
make provider-cards-status JSON=1             # für CI-Parsing
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
make provider-cards PROVIDER=Anthropic
make provider-cards-update YES=1   # SSoT-Sync nach Generierung
make provider-cards-status
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

### `scripts/analysis/generate_provider_cards.py`

```bash
python scripts/analysis/generate_provider_cards.py            # alle fehlenden
python scripts/analysis/generate_provider_cards.py --force    # alle neu
python scripts/analysis/generate_provider_cards.py --provider "Anthropic"
python scripts/analysis/generate_provider_cards.py --update [--yes] [--dry-run]
```

### `scripts/analysis/generate_model_cards.py`

```bash
python scripts/analysis/generate_model_cards.py --model claude-opus-4-7
python scripts/analysis/generate_model_cards.py --model qwen3:14b --provider ollama_local
python scripts/analysis/generate_model_cards.py --update [--yes] [--dry-run]
```

### `scripts/analysis/provider_card_status.py`

```bash
python scripts/analysis/provider_card_status.py --stale-days 90
python scripts/analysis/provider_card_status.py --json
python scripts/analysis/provider_card_status.py --fail-on-unknown
python scripts/analysis/provider_card_status.py --fail-on-stale
```

---

## Make-Targets

| Target | Zweck | Flags |
|---|---|---|
| `make model-cards` | Model Card Template anlegen | `MODEL=name`, `PROVIDER=key`, `FORCE=1` |
| `make model-card` | Alias für `model-cards` | (siehe oben) |
| `make provider-cards` | Provider Card generieren (LLM) | `PROVIDER=name`, `FORCE=1` |
| `make ensure-card` | Eine Card mit Template sync | `MODEL=name`, `DRY=1` |
| `make ensure-cards` | Alle Cards mit Template sync | `ALL=1`, `DRY=1` |
| `make validate-cards` | Konsistenz-Check (tier/summary) | — |
| `make validate-cards-template` | Schema-Validierung gegen YAML | `CARD_TYPE=…`, `JSON=1`, `FAIL_ON_DRIFT=1` |
| `make cards-sync` | SSoT-Sync (add + delete mit Confirm) | `CARD_TYPE=…`, `DRY_RUN=1`, `YES=1`, `JSON=1` |
| `make provider-cards-update` | `--update` für Provider-Generator | `YES=1`, `DRY_RUN=1` |
| `make model-cards-update` | `--update` für Model-Generator | `YES=1`, `DRY_RUN=1` |
| `make provider-cards-status` | Audit-Readiness-Report | `STALE_DAYS=N`, `JSON=1` |

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

### „Provider Card hat unbekannte deployment-Sub-Felder"

→ `make provider-cards-status` zeigt, welche Sub-Felder betroffen sind.
Manuell befüllen (siehe `config/card_template_provider.yaml → deployment`).

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

## Verwandte Dokumentation

- `docs/ARCHITECTURE.md` — SSoT-Architektur des Projekts
- `docs/MODEL_CLASSIFICATION.md` — Modell-Klassifikationslogik
- `docs/MAINTENANCE_LOG.md` — Changelog (Phase 24/25 Einträge)
- `docs/USER_GUIDE.md` — End-Nutzer-Dokumentation
