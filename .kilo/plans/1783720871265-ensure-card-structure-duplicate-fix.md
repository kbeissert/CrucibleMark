# Fix: `ensure_card_structure.py` erzeugt doppelte Base-Cards für suffixed Modelle

## Problem

`scripts/dev/ensure_card_structure.py` erzeugt beim Batch-Modus (`--all`/`--missing`)
doppelte Base-Cards für provider-suffixed Modelle (`qwen3_6-27B--VSPK.json`,
`ornith-1_0-35B-FP8--SPRK.json`, etc.).

### Root Cause

`run_for_card()` (Zeile 90) liest `model_id` aus der Card-JSON (z.B. `qwen3_6-27B` —
die Base-ID ohne Suffix) und ruft dann `ensure_card(model_id)` **ohne** `card_path` oder
`provider` auf.

`ensure_card()` → `_resolve_card_path_for(model_id, None, None)` → `_card_path(model_id, for_write=True)`
→ kein Provider → Rule 2: gibt den **unprefixed** Pfad zurück (`qwen3_6-27B.json`).
Da diese Datei nicht existiert, erstellt `ensure_card` eine **neue** Base-Card — ein Duplikat
der existierenden suffixed Card.

Betroffen: alle Shortcodes `--SPRK`, `--VSPK`, `--M4APL`, `--GR` (siehe
`_try_prefixed_shortcode_lookup` in `utils/model_card_io.py:280`).

### Bestätigung

- `model_id`-Feld in suffixed Cards enthält die Base-ID:
  `qwen3_6-27B--VSPK.json` → `model_id='qwen3_6-27B'`
- Beim Audit-Lauf von `make ensure-cards` wurden 108 Cards modifiziert + 13 doppelte
  Base-Cards erstellt (alle revertiert)
- Keine Duplikate aktuell vorhanden (Daten sauber revertiert)

### Sekundärer Bug: `--model`-Modus

`--model` ohne `--dry-run` (Zeile 119) ruft ebenfalls `ensure_card(args.model)` ohne
`card_path` auf. Für Base-IDs mit existierenden suffixed Cards entsteht das gleiche
Duplikat-Problem. Zusätzlich:
- Prüft nicht auf fehlende Felder (ruft `ensure_card` immer auf)
- Setzt `changed = 1` auch wenn nichts geändert wurde
- `--model --dry-run` (Zeile 113) nutzt `_card_path(for_write=True)` statt `_find_card()`
  → findet suffixed Cards nicht, meldet "alle Felder fehlen"

## Fix-Strategie

### 1. Primary Fix: `run_for_card()` — `card_path` durchreichen

**Datei:** `scripts/dev/ensure_card_structure.py:90`

```python
# Vorher:
ensure_card(model_id)

# Nachher:
ensure_card(model_id, card_path=card_path)
```

`ensure_card` mit `card_path` patcht die existierende Datei in-place, anstatt einen
neuen Pfad via `_card_path()` aufzulösen. Dies ist das etablierte Pattern:
- `unified_runner.py:314` → `ensure_card(model, card_path=card_path)`
- `probe_thinking.py:116` → `ensure_card(model_id, card_path=existing_path)`
- `generate_model_cards.py:163` → `ensure_card(model_id, card_path=target_path)`

### 2. `--model`-Modus konsistent machen

**Datei:** `scripts/dev/ensure_card_structure.py:108-121`

Aktuell hat `--model` zwei völlig unterschiedliche Codepfade für `--dry-run` und
non-dry-run. Beide sollen vereinheitlicht werden:

```python
if args.model:
    from utils.model_utils import _find_card  # noqa: PLC0415
    existing = _find_card(args.model)
    if existing.exists():
        changed += run_for_card(existing, dry_run=args.dry_run)
    else:
        # Keine existierende Card → neu erstellen
        if args.dry_run:
            logger.info("DRY  (neu) %s.json", args.model)
            changed += 1
        else:
            ensure_card(args.model)
            logger.info("NEW %s", args.model)
            changed += 1
```

- `_find_card()` findet suffixed Cards (probiert alle Shortcodes)
- Existiert eine Card → `run_for_card()` prüft fehlende Felder und patcht in-place
- Existiert keine → `ensure_card(args.model)` erstellt eine neue (Base-Card, kein Suffix,
  da Provider unbekannt — korrektes Verhalten für `--model`)
- `changed` wird nur inkrementiert, wenn tatsächlich Felder fehlen (via `run_for_card`)

### 3. Filename-Fallback: Shortcode-Suffix strippen

**Datei:** `scripts/dev/ensure_card_structure.py:85-88`

Wenn `model_id` in der Card fehlt, wird es aus dem Dateinamen abgeleitet. Für suffixed
Cards wie `qwen3_5-9b--SPRK.json` würde der Stem `qwen3_5-9b--SPRK` als model_id verwendet
— das ist falsch (enthält den Provider-Suffix).

```python
if not model_id:
    stem = card_path.stem
    # Provider-Shortcode-Suffix strippen (z.B. "--SPRK", "--VSPK", "--M4APL", "--GR")
    stem = re.sub(r"--[A-Z0-9]+$", "", stem)
    model_id = stem.replace("_", "/", 1) if "/" not in stem else stem
```

Erfordert `import re` am Dateianfang.

## Edge Cases

| Szenario | Verhalten nach Fix |
|---|---|
| `--all`, suffixed Card mit fehlenden Feldern | `ensure_card(model_id, card_path=card_path)` patcht in-place — **kein Duplikat** |
| `--all`, suffixed Card ohne fehlende Felder | Skip ( unverändert) |
| `--all`, Base-Card (unsuffixed) mit fehlenden Feldern | `card_path == _card_path()` → patcht in-place — unverändert |
| `--model qwen3_6-27B`, `--VSPK` Card existiert | `_find_card` findet `qwen3_6-27B--VSPK.json` → `run_for_card` patcht in-place |
| `--model qwen3_6-27B`, keine Card existiert | `ensure_card("qwen3_6-27B")` erstellt `qwen3_6-27B.json` (Base, korrekt) |
| `--model qwen3_6-27B`, SPRK + VSPK Cards existieren | `_find_card` findet erste (SPRK) → patcht nur diese. Hinweis: Nutzer muss `--all` für beide nutzen |
| Namespaced Card (`z-ai/glm-5.json`) | `_find_card` → `_try_namespaced_lookup` → unprefixed Pfad — unverändert |

## Regression-Test

**Datei:** `tests/test_ensure_card_structure.py` (neu)

Test-Szenario: suffixed Card mit fehlenden Feldern → `run_for_card()` ausführen →
assert: nur die suffixed Datei existiert, keine Base-Card erstellt.

```python
def test_run_for_card_does_not_create_duplicate_base_card(tmp_path, monkeypatch):
    """run_for_card() darf keine Base-Card erstellen, wenn eine suffixed Card existiert."""
    # 1. Suffixed Card mit fehlenden Feldern anlegen
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    suffixed = card_dir / "qwen3_6-27B--VSPK.json"
    suffixed.write_text(json.dumps({"model_id": "qwen3_6-27B"}), encoding="utf-8")

    # 2. CARD_DIR patchen + run_for_card aufrufen
    monkeypatch.setattr("scripts.dev.ensure_card_structure.CARDS_DIR", card_dir)
    from scripts.dev.ensure_card_structure import run_for_card
    changed = run_for_card(suffixed, dry_run=False)

    # 3. Assert: nur suffixed Card existiert, keine Base-Card
    assert changed is True
    assert suffixed.exists()
    base = card_dir / "qwen3_6-27B.json"
    assert not base.exists(), f"Duplicate base card created: {base}"
    # model_id-Feld unverändert (Base-ID, kein Suffix)
    data = json.loads(suffixed.read_text(encoding="utf-8"))
    assert data["model_id"] == "qwen3_6-27B"
```

Zusätzlich: Test für `--model`-Modus, der eine existierende suffixed Card findet und
in-place patcht (kein Duplikat).

## Validierung

1. `ruff check scripts/dev/ensure_card_structure.py` — 0 violations
2. `python -m pytest tests/test_ensure_card_structure.py -v` — neue Tests grün
3. `python -m pytest tests/test_ensure_card_with_provider.py -v` — keine Regression
4. `python scripts/dev/ensure_card_structure.py --all --dry-run` — Vorschau, keine
   Base-Cards in der Ausgabe
5. `python scripts/dev/ensure_card_structure.py --missing --dry-run` — gleiche Vorschau
6. `python scripts/dev/ensure_card_structure.py --model qwen3_6-27B --dry-run` — findet
   `qwen3_6-27B--VSPK.json` (nicht `qwen3_6-27B.json`)
7. `make test` — 1457+ passed, 0 failed
8. Git-Status: keine neuen JSON-Dateien in `benchmark_scores/model_cards/`

## Out of Scope

- `ensure_card()` selbst (utils/card_utils.py) — Funktion korrekt, nur Aufrufer falsch
- `generate_review.py:276` — `ensure_card(model_id)` ohne `card_path` ist dort korrekt
  (erstellt bewusst eine neue Card, wenn keine existiert)
- `model_id.py:173` — `ensure_card(canonical)` ohne `card_path` — separater Kontext
  (Card-Erstellung beim Model-Import, nicht Batch-Patching)
- Konsistenz des `model_id`-Felds (Base-ID vs. suffixed ID) zwischen alten und neuen
  Cards — pre-existing, separater Task
