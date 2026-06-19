# Plan: Model-Card-Lifecycle — `card-create` / `card-validate` / `card-research`

## Ziel

Drei neue Make-Targets, die den kompletten Lebenszyklus einer Model Card
abdecken, von der Erstellung aus `provider_config.yaml` über die
Struktur-Sync mit dem Template bis zur inhaltlichen LLM-Recherche:

| Make-Befehl | Wirkung |
|-------------|---------|
| `make card-create MODEL=<id>` | Legt eine neue Card aus `provider_config.yaml` an. Validiert, dass die ID keine Punkte enthält (Schutz vor Slug-Mismatch-Bug). |
| `make card-validate` / `make card-validate MODEL=<id>` | Synchronisiert Cards mit dem SSoT-Template (Felder hinzufügen wenn im Template neu, entfernen wenn nicht mehr im Template). Stille Validierung — kein LLM-Aufruf, sondern deterministisches Schema-Matching. |
| `make card-research` / `make card-research MODEL=<id>` | LLM-Recherche der Card-Inhalte (Preise, Beschreibung, Quellen, Sonderzeichen wie Chinesisch). Lock-Mechanismus via `profile_verified`: `true` → `false` zu Beginn, zurück auf `true` am Ende. Bei Abbruch bleibt `false` und ist der Resumption-Marker. |

Phase-1-Skript `scripts/manage_model_cards.py` (LLM-gestütztes
Check/Make) bleibt unverändert; Phase 2 ergänzt rein deterministische
Struktur-Tools und einen dedizierten Recherche-Pfad.

## Designentscheidungen (vorab geklärt)

1. **Lock via `profile_verified: false`** (vom User bestätigt).
   - `make card-research` setzt `profile_verified` zu Beginn auf `false` und
     schreibt `profile_verified_at: null` und `profile_verified_by: null`
     (neues optionales Feld, von dem Editor-Prompt später befüllt wird).
   - Am Ende: `profile_verified: true` + `profile_verified_at: YYYY-MM-DD`.
   - Abbruch/Fehler: `false` bleibt stehen → klarer Resumption-Marker.
   - Keine separaten `.lock`-Dateien, keine `flock`/Hidden-Files.

2. **Card-Erstellung: Skeleton + Pre-Fill aus `provider_config.yaml`**.
   - Look-up via `utils.config_validator.ConfigValidator` (bereits SSoT für
     `benchmark_config.yaml` + `config/provider_config.yaml`).
   - Übernommen werden: `id` → `model_id`, `name` → `display_name`, und
     `developer` falls im Provider-Config-Top-Level vorhanden (z.B. via
     `name`-Feld der Provider-Sektion).
   - Restliche Felder: Template-Defaults (`TODO`/null).
   - `vendor` wird aus `classification_taxonomy.json` abgeleitet, falls
     Hersteller-Name in der Taxonomy liegt.

3. **Validation = `utils.card_sync` mit `--yes` Default**.
   - Das bestehende `utils/card_sync.py` implementiert bereits
     Add (fehlende Felder) und Delete (überzählige Felder) — exakt das
     was der User beschreibt. `scripts/analysis/sync_cards.py` ist der
     CLI-Wrapper.
   - Erweiterung: `--model <id>` Flag für Einzelkarten-Modus.
   - `make card-validate` setzt `--yes` (kein Prompt), damit CI-tauglich.
   - `make card-validate MODEL=<id>` analog.

4. **Recherche = neuer Modus in `manage_model_cards.py`** (NICHT ein
   zweites Skript).
   - Vermeidet Code-Duplikation: `LLMSession`, Override-Hierarchie,
     Operator-Protected-Fields, JSON-Parser, Editor-Prompt-Loader
     existieren bereits.
   - Neuer Modus `--mode research` mit eigenem System-Instruction
     (Fokus: Preise, Beschreibung, Sonderzeichen-Erkennung, Quellen).
   - `profile_verified`-Lock-Logik im neuen `Researcher`-Helper.
   - Wenn `manage_model_cards.py` zu groß wird (>900 Zeilen), Refactoring
     in `utils/llm_session.py` + `utils/card_research.py` als Folge-Phase.

5. **Sonderzeichen-Detektion (`Murks` / Chinesisch / Em-Dashes)**:
   - Vor dem LLM-Call: heuristischer Pre-Check der `summary`,
     `strengths`, `known_limitations`, `judge_context_hint` auf:
     - CJK-Unicode-Ranges (`U+4E00`–`U+9FFF`, `U+3040`–`U+30FF`,
       `U+AC00`–`U+D7AF`)
     - Em-Dash (`—`) und Bullet-Striche in `summary` (laut Prompt
       Schritt 5 verboten)
     - Werden als Findings an die LLM-Antwort angehängt, damit der
       Operator sie im Report sieht.

6. **Dry-Run-Verhalten**:
   - `card-create` / `card-validate` / `card-research` schreiben
     standardmäßig **nicht** ohne explizite Bestätigung. Toggle:
     - `DRY=1` für Vorschau
     - `YES=1` (oder `--yes`) für Auto-Bestätigung
   - Konsistent mit existierender Convention (`make clean DRY=1`,
     `make sanitize-benchmark-csvs FIX=1`).

7. **Recherche-Targets**:
   - Default: alle Cards mit `profile_verified != true` ODER mit
     explizitem `FORCE=1`.
   - `--card` / `MODEL=<id>` Override für einzelne Karten.
   - Cards mit `profile_verified: true` UND ohne `FORCE` werden
     übersprungen (gleicher Skip-Pfad wie in Phase 1).

## Verzeichnis-Layout & Imports

```
scripts/manage_model_cards.py          (geändert: +Researcher-Mode, ~150 Zeilen)
scripts/analysis/sync_cards.py         (geändert: +--model Flag, ~30 Zeilen)
scripts/dev/create_model_card.py       (neu, ~150 Zeilen)
Makefile                                (geändert: +3 Targets, +3 Help-Zeilen)
config/card_template_model.yaml         (geändert: +optional profile_verified_by)
```

Keine neuen Top-Level-Skripte neben `scripts/dev/create_model_card.py` —
alles weitere wird in bestehende Skripte integriert.

ROOT_DIR-Bootstrap wie immer identisch zu `generate_review.py:23-25`.

## Config-Änderungen

### `config/card_template_model.yaml`

Optionales Feld ergänzen (nach `profile_verified_at`):

```yaml
  - name: profile_verified_by
    type: str
    required: false
    default: null
    description: "Wer hat zuletzt verifiziert ('human' | 'llm:<model>' | null). SSoT für Audit-Trail."
    consumers: [verify, web_export]
    since: "v4.10.0"
    example: "llm:gpt-5.4"
```

### `Makefile`

Drei neue Targets (Platzierung im `Card-Lifecycle`-Block, ca. Zeile 5+60):

```makefile
card-create:
	@if [ -z "$(MODEL)" ]; then \
		echo "Fehler: MODEL=<model-id> ist erforderlich."; \
		echo "Beispiel: make card-create MODEL=claude-sonnet-4-6"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/dev/create_model_card.py --model "$(MODEL)" $(if $(DRY),--dry-run) $(if $(YES),--yes) $(if $(PROVIDER),--provider "$(PROVIDER)")

card-validate:
	@echo "=== Card-Sync (Template → Cards) ==="
	@echo "Fügt fehlende Felder hinzu, entfernt Extras (mit Bestaetigung oder YES=1)."
	@echo ""
	@if [ -n "$(MODEL)" ]; then \
		$(PYTHON) scripts/analysis/sync_cards.py --card-type model --model "$(MODEL)" $(if $(YES),--yes,) $(if $(DRY),--dry-run,); \
	else \
		$(PYTHON) scripts/analysis/sync_cards.py --card-type model $(if $(YES),--yes,) $(if $(DRY),--dry-run,); \
	fi

card-research:
	@echo "=== Card-Inhalts-Recherche (LLM) ==="
	@echo "Lock-Mechanismus: profile_verified wird auf false gesetzt,"
	@echo "am Ende wieder auf true. Bei Abbruch bleibt false stehen."
	@echo ""
	@if [ -n "$(MODEL)" ]; then \
		$(PYTHON) scripts/manage_model_cards.py --mode research --card "$(MODEL)" $(if $(FORCE),--force) $(if $(DRY),--dry-run,); \
	else \
		$(PYTHON) scripts/manage_model_cards.py --mode research $(if $(FORCE),--force) $(if $(DRY),--dry-run,); \
	fi
```

Help-Block (Zeile 58-62) erweitern:

```makefile
	@printf "  %-25s %s\n" "card-create"      "Neue Card aus provider_config.yaml anlegen"
	@printf "  %-25s %s\n" "card-validate"    "Cards mit Template synchronisieren (alle oder MODEL=)"
	@printf "  %-25s %s\n" "card-research"    "LLM-Inhalts-Recherche (Murks/Chinesisch/Preise)"
```

`card-create` und `card-validate` brauchen das `card-` Prefix-Pattern
(konsistent mit `card-sync`, `card-validate-template` etc.). `card-research`
ist neu; `research` als Top-Level-Name würde mit dem existierenden
`card-research` kollidieren, falls jemals hinzugefügt.

## Command 1: `make card-create MODEL=<id>`

### Skript: `scripts/dev/create_model_card.py` (neu, ~150 Zeilen)

Architektur analog zu `ensure_card_structure.py:1-141`:

```
1. CLI-Argumente parsen
   --model <id>        (required)
   --provider <key>    (optional, auto-detect aus provider_config wenn nicht gegeben)
   --dry-run           (default: False — Card wird geschrieben)
   --yes               (default: False — interaktive Bestaetigung)
2. ID-Validierung (HARTER FEHLER bei Punkt im Namen)
   - Wenn "." in model_id: SystemExit("Card-IDs duerfen keine Punkte enthalten ...")
3. Provider-Lookup
   - ConfigValidator().config
   - Durchsuche providers.{commercial,local}.* nach model_id
   - Falls gefunden: name → display_name, developer → developer
4. Card-Skeleton via utils.card_utils.ensure_card(model_id, provider=...)
   - Pfad via _card_path(model_id, for_write=True) bestimmen
5. Post-Fill: display_name / developer ueberschreiben TODO (falls gefunden)
6. rebuild_card_index("model")
7. Status-Print
```

### Validierungs-Detail: "Keine Punkte in der ID"

```python
def _validate_id(model_id: str) -> None:
    if "." in model_id:
        raise SystemExit(
            f"❌ Card-ID '{model_id}' enthaelt einen Punkt. "
            f"Punkte verursachen Slug-Mismatches zwischen API-IDs "
            f"(vendor/model-v1) und Dateinamen (vendor_model-v1). "
            f"Bitte verwende Slashes fuer Vendor-Präfixe "
            f"(z.B. 'z-ai/glm-5.2' statt 'z-ai.glm-5.2') "
            f"oder fuege einen Alias via heritage_ids hinzu."
        )
    if "/" not in model_id and ":" in model_id:
        # Ollama-Tag-Schema (z.B. "qwen2.5:14b") — explizit erlaubt,
        # weil ensure_card das via _safe_name korrekt behandelt.
        pass
```

Hintergrund (aus Plan-Phase-1-Discovery): `utils/model_utils.py:_safe_name`
konvertiert `.` zu `_`. Eine Card mit `model_id: "z-ai/glm-5.2"` wird zu
`z-ai_glm-5_2.json`. Wenn der User später `make research MODEL=z-ai/glm-5.2`
aufruft, würde `_find_card` zuerst `z-ai_glm-5.2.json` suchen (nicht
vorhanden) und dann den Glob-Fallback nutzen — das funktioniert, ist
aber fehleranfällig. Mit dem harten Validierungs-Fehler wird das
Missverständnis explizit.

### Imports (alle existieren bereits)

```python
import argparse, json, logging, sys
from pathlib import Path
from utils.card_template import rebuild_card_index
from utils.card_utils import ensure_card
from utils.config_validator import ConfigValidator
from utils.model_utils import _card_path
```

## Command 2: `make card-validate [MODEL=<id>]`

### Erweiterung: `scripts/analysis/sync_cards.py`

Aktuell: `--card-type {model,vendor,all}` + `--yes` + `--dry-run` + `--json`.

Neu: `--model <id>` für Einzelkarten-Modus.

```python
parser.add_argument(
    "--model", type=str,
    help="Nur diese eine Karte synchronisieren (sonst: alle des card-type).",
)
```

Logik-Erweiterung in `main()`:

```python
if args.model:
    if args.card_type == "all":
        args.card_type = "model"  # --model ohne --card-type = model
    from utils.card_sync import sync_card
    plan = sync_card(
        _resolve_single_card_path(args.model, args.card_type),
        args.card_type,
        dry_run=args.dry_run,
        yes=args.yes,
    )
    if args.json:
        # ... Single-Card-Plan als JSON
    else:
        print(format_summary([plan]))
else:
    # bisheriger Pfad
```

`_resolve_single_card_path(model_id, card_type)`:

```python
from utils.model_utils import _find_card, _card_path
if card_type == "model":
    p = _find_card(model_id)
    if not p.exists():
        raise SystemExit(f"❌ Card nicht gefunden: {model_id}")
    return p
else:
    from utils.vendor_card_template import CARDS_DIR
    p = CARDS_DIR / f"{_safe_id(model_id)}.json"
    if not p.exists():
        raise SystemExit(f"❌ Vendor Card nicht gefunden: {model_id}")
    return p
```

### Verhalten

- `make card-validate` → `sync_cards.py --card-type model` (alle Model-Cards)
- `make card-validate MODEL=claude-sonnet-4-6` → single card
- `make card-validate YES=1` → Adds auto, Deletes auto (kein Prompt)
- `make card-validate DRY=1` → Vorschau ohne Schreiben
- Exit-Code 0 bei Erfolg, 1 wenn Deletes in DRY-Run erkannt (bestehende Logik)

## Command 3: `make card-research [MODEL=<id>]`

### Erweiterung: `scripts/manage_model_cards.py`

Neuer Modus `--mode research`. Architektur:

```
class Researcher:
    def __init__(self, args, session, template, editor_prompt, llm_spec)
    def run() -> Summary
        - target_cards = _discover_research_targets(args)  # wie check, aber profile_verified-aware
        - for each card:
            - _research_one(card, path)
    def _research_one(mid, path) -> ResearchReport
        - 1. Lock: profile_verified = false, profile_verified_at = null, profile_verified_by = null
        - 2. Backup: copy path → path + ".pre-research.bak" (Sicherheitsnetz)
        - 3. Pre-Check: scan summary/strengths/known_limitations/judge_context_hint for
              - CJK chars (U+4E00-9FFF, U+3040-30FF, U+AC00-D7AF)
              - em-dash (—) in summary
              - Mark each as finding (severity: error)
        - 4. LLM query with system-instruction "du bist ein card-researcher"
              + editor prompt + existing card
        - 5. Parse JSON response
        - 6. Apply diff (LLM-suggested values)
        - 7. Preserve operator-protected fields (model_id, generated_at, ...)
        - 8. Validate against template
        - 9. Write card (if not dry-run)
        - 10. Un-lock: profile_verified = true, profile_verified_at = YYYY-MM-DD,
              profile_verified_by = "llm:<model>"
        - 11. Delete backup on success
        - 12. Rebuild index
    def _discover_research_targets(args) -> list
        - if args.card: single target
        - else: glob all *.json except _index.json
              - skip if profile_verified == true AND not args.force
```

### Lock-Logik — Exception-sicher

```python
def _research_one(self, mid, path):
    report = ResearchReport(model_id=mid, card_path=path)
    original_card = None
    try:
        original_card = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.error = f"Card nicht lesbar: {exc}"
        return report

    # Lock
    locked = dict(original_card)
    locked["profile_verified"] = False
    locked["profile_verified_at"] = None
    locked["profile_verified_by"] = None
    locked["last_modified_at"] = date.today().isoformat()
    path.write_text(json.dumps(locked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("    🔓 Lock geoeffnet: %s (profile_verified=false)", path.name)

    try:
        # ... LLM call, parse, apply, validate, write ...
        # Bei Erfolg: profile_verified = true setzen
        final = dict(cleaned)
        final["profile_verified"] = True
        final["profile_verified_at"] = date.today().isoformat()
        final["profile_verified_by"] = f"llm:{self.llm_spec.model}"
        path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        logger.info("    🔒 Lock geschlossen: %s (profile_verified=true)", path.name)
        report.success = True
    except Exception as exc:
        logger.error("    ❌ Recherche fehlgeschlagen — Lock bleibt offen: %s", exc)
        # KEIN Schreiben — Lock-Datei (profile_verified=false) bleibt stehen
        report.error = str(exc)
        # Backup NICHT loeschen — Operator kann Diff manuell inspizieren
```

### Pre-Check Heuristik (Murks / Chinesisch)

```python
_CJK_RANGES = (
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # CJK Extension A
    (0x3040, 0x309F),    # Hiragana
    (0x30A0, 0x30FF),    # Katakana
    (0xAC00, 0xD7AF),    # Hangul Syllables
)

def _check_murks(card: dict) -> list[CardFinding]:
    findings = []
    for field in ("summary", "strengths", "known_limitations", "judge_context_hint"):
        val = card.get(field)
        if not isinstance(val, str):
            continue
        # CJK check
        for ch in val:
            if any(lo <= ord(ch) <= hi for lo, hi in _CJK_RANGES):
                findings.append(CardFinding(
                    field=field,
                    severity="error",
                    message=f"CJK-Zeichen gefunden: {ch!r} (U+{ord(ch):04X}) — "
                            f"redaktioneller Text sollte lateinische Schrift verwenden",
                    current=ch,
                    suggested=None,
                ))
                break
        # em-dash in summary
        if field == "summary" and "—" in val:
            findings.append(CardFinding(
                field=field,
                severity="error",
                message="em-dash (—) im summary gefunden — laut Prompt Schritt 5 verboten",
                current="—",
                suggested=None,
            ))
    return findings
```

### System-Instruction für Research

```python
_RESEARCH_SYSTEM_INSTRUCTION = (
    "Du bist ein Card-Researcher. Prüfe die unten angegebene Model Card auf "
    "inhaltliche Korrektheit: Preise (input_price_per_1m / output_price_per_1m), "
    "Context-Window, Knowledge-Cutoff, Display-Name, Summary-Inhalt (kein Murks, "
    "keine chinesischen Zeichen, keine Em-Dashes). Recherchiere ueber offizielle "
    "Quellen (Hersteller-Website, HuggingFace, API-Pricing). "
    "Antworte AUSSCHLIESSLICH mit JSON: "
    "{\"findings\": [{\"field\": ..., \"severity\": \"error|warning|info\", "
    "\"message\": ..., \"current\": ..., \"suggested\": ...}], "
    "\"summary\": \"...\"}. "
    "Antworte NUR mit dem JSON-Objekt — kein Markdown-Fence, keine Kommentare."
)
```

### Reporting (analog zu Check-Mode)

- Markdown-Report bei `make card-research` ohne `--dry-run`:
  ```
  # Model Card Research Report — 2026-06-18

  **Modus:** research
  **Verarbeitet:** 12 · **Recherche-Fehler:** 0 · **Murks-Findings:** 3

  ## claude-sonnet-4-6
  - 🔴 `summary` — CJK-Zeichen gefunden: '大' (U+5927) — ...
  - 🟡 `input_price_per_1m` — aktueller Listenpreis ist 3.00 (3.50 seit 2025-11)
  ...
  ```

## Implementation Notes

- **Backup-Strategie in `_research_one`**: vor dem Schreiben
  `path.with_suffix('.pre-research.bak')` anlegen. Bei Erfolg löschen,
  bei Fehler behalten. Schutz vor versehentlichem Überschreiben ohne
  Wiederherstellungs-Möglichkeit.

- **`last_modified_at`-Feld** ist neu — sollte ins Template als
  optionales Feld (siehe Config-Änderungen). Wird vom
  `Researcher` und von `manage_model_cards.py --mode make --write`
  aktualisiert.

- **`--force` für Research**: standardmäßig nur Cards mit
  `profile_verified != true` bearbeiten (Resumption-First). `FORCE=1`
  zwingt die Bearbeitung auch verifizierter Cards.

- **Phase-1-Kompatibilität**: `manage_model_cards.py --mode check` und
  `--mode make` bleiben unverändert. Die `_research_one`-Logik nutzt
  die bestehenden Helper `_parse_*_response`, `_apply_check_fixes`,
  `_preserve_operator_fields`, `_validate_against_template`. Nur der
  `Researcher` ist neu.

- **Reihenfolge im `_research_one`**: Pre-Check-Heuristik läuft VOR dem
  LLM-Call, damit die Findings dem LLM als zusätzlicher Kontext
  mitgegeben werden können (optional, Phase 3).

- **JSON-Format**: Cards werden konsistent mit `ensure_ascii=False,
  indent=2 + "\n"` geschrieben (gleiches Format wie `ensure_card` und
  `rebuild_card_index`).

- **`profile_verified_by` Konvention**: `"human"` (manuell), `"llm:<model>"`
  (LLM-getrieben), `null` (nicht verifiziert). Wird in `web_export.py`
  angezeigt (Phase 3).

- **Edge-Case: Card existiert nicht bei `card-research`**: wirft
  `SystemExit` (analog zu `check`-Mode). Der User muss erst
  `make card-create` aufrufen.

## Datenfluss

### `make card-create MODEL=claude-sonnet-4-6`

```
ConfigValidator
  → providers.commercial.anthropic.models → match id "claude-sonnet-4-6"
  → display_name = "Claude Sonnet 4.6" (aus config)
  → developer = "Anthropic" (aus provider section.name)
utils.card_utils.ensure_card(model_id="claude-sonnet-4-6")
  → _card_path(for_write=True) → benchmark_scores/model_cards/claude-sonnet-4-6.json
  → schreibt Skeleton mit TODO-Defaults
post-fill: display_name, developer ueberschreiben TODO
rebuild_card_index("model")
print: "✅ Card erstellt: benchmark_scores/model_cards/claude-sonnet-4-6.json"
```

### `make card-validate MODEL=claude-sonnet-4-6`

```
utils.card_sync.plan_sync("claude-sonnet-4-6.json", "model")
  → add: ["profile_verified_by", "last_modified_at"] (neue Template-Felder)
  → delete: ["legacy_field"] (z.B. wenn im Template entfernt)
  → keep: alle anderen
sync_card(plan, yes=True)  # YES=1 ueberspringt Delete-Prompts
rebuild_card_index("model")
print: "1 Karte synchronisiert: +2 adds, -1 delete"
```

### `make card-research MODEL=claude-sonnet-4-6`

```
1. Lock-Phase: profile_verified=false schreiben (atomic)
2. Backup: claude-sonnet-4-6.json.pre-research.bak
3. Pre-Check: scan fuer CJK / em-dash → findings = [...]
4. LLM-Call (manage_model_cards.py LLMSession) mit Research-System-Instruction
5. Parse JSON-Response
6. Apply: merged = apply_research_diff(original, response)
7. Preserve: preserve_operator_fields(original, merged)
8. Validate: validate_against_template(merged, template)
9. Write: claude-sonnet-4-6.json (mit profile_verified=false waehrend Working-State —
   eigentlich Lock bleibt bis Schritt 10)
10. Un-Lock: profile_verified=true, profile_verified_at=today, profile_verified_by="llm:..."
11. Delete backup
12. rebuild_card_index
print: "✅ Recherche abgeschlossen: 3 Findings (1 error, 2 warnings) in 12.4s"
```

Bei Exception in Schritt 4-9:
- Lock-Datei (profile_verified=false) bleibt stehen
- Backup wird NICHT geloescht
- Nächster `make card-research` ohne `--card` ueberspringt diese Card
  nicht (profile_verified=false), sondern nimmt sie in den Resumption-Pfad
- Mit `FORCE=1` kann man sie neu starten

## CLI-Interface (gesamt)

```bash
# Card-Lifecycle
make card-create MODEL=z-ai/glm-5.2                    # Neue Card anlegen
make card-create MODEL=z-ai/glm-5.2 DRY=1              # Vorschau
make card-create MODEL=z-ai/glm-5.2 YES=1              # ohne Bestaetigung

make card-validate                                    # alle Cards mit Template syncen
make card-validate MODEL=claude-sonnet-4-6             # einzelne Card
make card-validate YES=1                              # ohne Delete-Prompt
make card-validate DRY=1                              # Vorschau

make card-research                                    # alle Karten mit profile_verified=false
make card-research MODEL=claude-sonnet-4-6             # einzelne Card
make card-research FORCE=1                            # auch verifizierte Cards
make card-research DRY=1                              # Vorschau (ohne Lock-Phase)
```

## Fehlerbehandlung

| Situation | Verhalten |
|-----------|-----------|
| `card-create`: ID enthält Punkt | `SystemExit` mit konkretem Hinweis auf Slug-Mismatch |
| `card-create`: Model nicht in provider_config | `SystemExit` mit Liste der verfügbaren Modelle (Top-10) |
| `card-create`: Card existiert bereits | `SystemExit` (User soll `card-research` oder `card-validate` nutzen) |
| `card-validate`: keine Cards | `logger.warning` + Exit 0 |
| `card-validate`: Delete in DRY-Run | Exit 1 (bestehende sync_cards-Logik) |
| `card-research`: LLM-Fehler nach max_retries | Lock bleibt offen, Backup bleibt, Card-Status bleibt `profile_verified=false` |
| `card-research`: Card nicht parsebar | Lock wird trotzdem gesetzt (`profile_verified=false`) — Operator muss manuell aufräumen |
| `card-research`: User bricht mit Ctrl+C ab | gleiche Exception-Safety wie LLM-Fehler |

## Tests (manuell / smoke)

Nach Implementierung:

1. `make card-create MODEL=claude-sonnet-4-6 DRY=1` → Vorschau, keine Card geschrieben
2. `make card-create MODEL=claude-sonnet-4-6 YES=1` → Card erstellt, `cat` zeigt Skeleton + display_name/developer
3. `make card-create MODEL=test.illegal-id` → SystemExit mit Slug-Mismatch-Hinweis
4. `make card-create MODEL=nonexistent` → SystemExit "Model nicht in provider_config"
5. `make card-validate` → Sync-Plan für alle Cards, +X adds, -Y deletes
6. `make card-validate MODEL=claude-sonnet-4-6` → single-card
7. Template-Feld entfernen → `make card-validate` zeigt delete-Plan
8. Template-Feld ergänzen → `make card-validate` zeigt add-Plan
9. `make card-research MODEL=claude-sonnet-4-6 DRY=1` → Vorschau, keine Card geschrieben
10. `make card-research MODEL=claude-sonnet-4-6` → Lock geöffnet, Recherche, Lock geschlossen
11. Mid-research Ctrl+C → Card hat `profile_verified=false`, Backup vorhanden
12. Nächster `make card-research` ohne `--card` → bearbeitet die halb-fertige Card
13. Card mit CJK-Zeichen in summary → Pre-Check findet es, Report zeigt es
14. Card mit em-dash in summary → Pre-Check findet es

## Offene Fragen an den User

1. **`card-create` und vorhandene Card**: Wenn die Card bereits existiert,
   was soll passieren? Mein Vorschlag: **SystemExit** (kein
   Force-Overwrite — der User soll bewusst `make card-research` oder
   `make card-validate` für Updates nutzen). Alternativ: `--force` Flag
   zum Überschreiben.

2. **Vendor/developer Pre-Fill aus `provider_config`**: Wie zuverlässig
   ist das Mapping `config.provider_config.yaml[*].name` →
   `model_card.vendor`? In der Taxonomy sind Vendor-Namen wie
   "Mistral AI" (mit space), aber in `classification_taxonomy.json` sind
   kanonische Namen wie "Mistral AI" — Mapping 1:1 möglich. Mein
   Vorschlag: **exact match** (case-sensitive, kein Fuzzy), mit Fallback
   auf `TODO` falls kein Match.

3. **Pre-Check-Heuristik — wo anwenden?** Soll der CJK/em-dash-Check
   nur in `summary` laufen, oder auch in `strengths` /
   `known_limitations` / `judge_context_hint`? Mein Vorschlag:
   **alle vier Felder**, weil der Editor-Prompt Schritt 5
   "summary" hervorhebt aber die anderen Felder gleichermaßen
   redaktionellen Standards folgen sollen.

4. **Recherche-Mode-Default-Targets**: Soll `make card-research`
   standardmäßig ALLE Cards mit `profile_verified=false` bearbeiten
   (auch wenn schon ein Lock offen ist), oder nur die "neuen"
   (d.h. vorher nie angefasst)? Mein Vorschlag: **alle mit
   `profile_verified != true`** (Resumption-First) — gleicher
   Skip-Pfad wie Phase 1.

5. **`make card-research` Exit-Code**: Wenn 1+ Cards nach der
   Recherche noch `profile_verified=false` haben (also fehlgeschlagen),
   soll das Skript mit Exit 1 enden? Mein Vorschlag: **Ja** (CI-Signal).

6. **`--model`-Flag in `sync_cards.py`**: Soll `--model` ohne
   `--card-type` implizit `--card-type model` annehmen, oder
   zwingend `--card-type` erfordern? Mein Vorschlag: **implizit
   model** (analog zu `manage_model_cards.py` — ist eh nur für
   Model-Cards sinnvoll in der Praxis).

## Implementierungs-Reihenfolge (nach Freigabe)

1. `config/card_template_model.yaml`: `profile_verified_by` und
   `last_modified_at` als optionale Felder ergänzen.
2. `scripts/analysis/sync_cards.py`: `--model` Flag + Single-Card-Pfad.
3. `scripts/dev/create_model_card.py`: Skeleton-Script mit
   ID-Validierung.
4. `Makefile`: Drei neue Targets + Help-Block.
5. `scripts/manage_model_cards.py`: `--mode research` mit
   `Researcher`-Klasse, Lock-Mechanismus, Pre-Check-Heuristik.
6. End-to-End-Smoke-Tests (siehe oben).

Geschätzter Umfang: ~350 Zeilen neue/geänderte Python-Zeilen,
~50 Zeilen Makefile-Änderungen, ~10 Zeilen Template-YAML.
