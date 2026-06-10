# Web-Exporter Model-Card-Compatibility-Audit

**Datum:** 2026-06-10
**Auditor:** KI-Assistent
**Scope:** Welche Felder der standardisierten Model-Cards werden vom Web-Export (`scripts/web_export.py`) tatsächlich verarbeitet?
**Status:** Audit abgeschlossen — **8 Findings**, davon 1 kritisch, 4 hoch, 3 niedrig

---

## Methodik

1. Code-Inspektion `scripts/web_export.py`, Funktion `_build_leaderboard_entry()` (Zeile 581–704)
2. Cross-Check mit `config/card_template_model.yaml` (SSoT für Pflicht-/Optionalfelder)
3. Test-Export in `outputs/web_export_check/raw/` (92 Modelle, 91 mit Card, 1 ohne)
4. Field-by-Field-Vergleich: `data.json` vs. Quell-Card

**Tooling:** Python 3.14 (.venv), pandas, json

---

## Befund-Übersicht

| # | Schweregrad | Feld | In Card | Im Export | Template-Status |
|---|-------------|------|---------|-----------|-----------------|
| 1 | **KRITISCH** | `input_modalities` | 91× | 0× | required since v4.7.0, `consumers: [web_export, …]` |
| 2 | **KRITISCH** | `output_modalities` | 91× | 0× | required since v4.7.0, `consumers: [web_export, leaderboard]` |
| 3 | **HOCH** | `judge_context_hint` | 91× | 0× | required, `consumers: [judge, scoring]` |
| 4 | **HOCH** | `primary_focus` | 91× | 0× | required, `consumers: [leaderboard, review]` |
| 5 | **HOCH** | `unknown` | 91× | 0× | required, `consumers: [risk_calc, leaderboard, review]` |
| 6 | MITTEL | `generated_at` | 91× | 0× | required, `consumers: [index, web_export]` |
| 7 | NIEDRIG | `model_id` | 91× | 0× (in sub-dict) | required, bereits im Top-Level |
| 8 | NIEDRIG | `model_version` | 91× | 0× (in sub-dict) | required, bereits im Top-Level als `version` |

**Zusätzliche Befunde:**

| # | Schweregrad | Befund |
|---|-------------|--------|
| 9 | MITTEL | `cot_marker_family` & `cot_tags_detected` (optional, v4.7.1, `consumers: [web_export, …]`) sind in **0 von 113 Karten** gesetzt — Card-Schema hat sie, Prober schreibt sie nicht |
| 10 | NIEDRIG | `gpt-5_4` hat **keine Model-Card** im `model_cards/`-Ordner (Existenz-Lücke), Web-Export loggt stillschweigend `model_card: None` statt WARNING |

---

## Detailanalyse

### Befund 1 + 2: `input_modalities` / `output_modalities` fehlen im Export

**Symptom:** Diese beiden Felder wurden in v4.7.0 als **required** eingeführt, mit explizitem `consumers: [web_export, …]`-Eintrag im Template. Sie liegen in allen 113 Karten sauber vor:

```
input_modalities Verteilung (n=113):
  text                 52
  image+text           47
  audio+image+text     14

output_modalities Verteilung (n=113):
  text                113
```

**Code-Beleg:** `scripts/web_export.py:660–703` — das `model_card` sub-dict listet diese Felder nicht auf. Zeile 668 referenziert `architecture_tags`, Zeile 705 springt direkt zum Top-Level ohne Modalitäten.

**Impact:** 11ty-Frontend kann **keine Vision-/Audio-Badges** anzeigen, obwohl 61 Karten Bild-Verarbeitung können. Direkter Bruch der `consumers: [web_export]`-Zusage.

### Befund 3: `judge_context_hint` fehlt

**Symptom:** Required-Feld mit `consumers: [judge, scoring]`. Wird vom Judge-Prompt verwendet, ist aber im Web-Export nicht sichtbar.

**Code-Beleg:** Fehlt komplett in `_build_leaderboard_entry()`.

**Impact:** Niedrig fürs Frontend, hoch für Reviewer-Audit (sollte auf Detail-Seite sichtbar sein, ist aber strenggenommen kein web_export-consumer).

### Befund 4: `primary_focus` fehlt

**Symptom:** Required-Feld (`general | reasoning | code | multimodal | …`), `consumers: [leaderboard, review]`. Existiert zusätzlich zu `use_case_primary` und ist **nicht identisch** mit diesem (siehe Template).

**Code-Beleg:** Fehlt. Im Export vorhanden: `use_case_primary` (generalist | coding | reasoning | vision-language | agentic).

**Impact:** Frontend kann die Leaderboard-Granularität von `primary_focus` nicht nutzen. Audit-Risiko: möglicher Redundanz-Konflikt mit `use_case_primary`.

### Befund 5: `unknown` fehlt

**Symptom:** Required-Feld (`bool`), `consumers: [risk_calc, leaderboard, review]`. Markiert "Card ist unvollständig / unbekannt".

**Code-Beleg:** Fehlt im `model_card` sub-dict.

**Impact:** Frontend kann Draft-Status nicht von Complete-Status visuell unterscheiden via `unknown`-Flag. `card_status` ist zwar exportiert, aber die bool'sche Tri-State-Semantik (`unknown: true` + `card_status: complete` ist ein Widerspruch) geht verloren.

### Befund 6: `generated_at` fehlt

**Symptom:** Required-Feld (`str`, ISO-8601), `consumers: [index, web_export]`. Card-Generation-Timestamp.

**Code-Beleg:** Fehlt. Top-Level `leaderboard.json` hat `generated_at` (vom Export selbst), aber pro-Card-Timestamp fehlt.

**Impact:** Niedrig — `leaderboard.json.generated_at` ist für Cache-Invalidierung ausreichend.

### Befund 7 + 8: `model_id` und `model_version` fehlen im sub-dict

**Symptom:** Beide Felder sind bereits im Top-Level (`model_id` direkt, `model_version` als `version`) vorhanden. Im `model_card` sub-dict fehlen sie.

**Code-Beleg:** `model_id`: Zeile 601 (Top-Level), fehlt Zeile 660–703.
`model_version`: Zeile 604 (Top-Level als `version`), fehlt Zeile 660–703.

**Impact:** Niedrig. Konsistenz-Frage: Soll das sub-dict self-contained sein (dann müssen `model_id` + `model_version` rein) oder referenziell (Top-Level reicht)?

### Befund 9: CoT-Felder ungesetzt in allen Karten

**Symptom:** `cot_marker_family` und `cot_tags_detected` (optional since v4.7.1) sind in **0 von 113 Karten** gefüllt.

**Bereits im Audit dokumentiert:** v4.7.1 hat das SSoT-Quartett erweitert, der `probe_thinking`-Workflow setzt diese Felder offenbar nicht (oder erst nach Probe-Recompute). Kein Web-Export-Bug, sondern Card-Pipeline-Lücke.

**Impact für Web-Export:** Die Felder sind im Template als `consumers: [web_export, …]` markiert, würden also gerendert sobald Daten da sind. Code-seitig muss nichts geändert werden — nur der Probe-Workflow muss sie schreiben.

### Befund 10: `gpt-5_4` hat keine Card-Datei

**Symptom:** Im Leaderboard (Rank 18, 74.31 Punkte), aber `benchmark_scores/model_cards/gpt-5_4.json` existiert nicht. Im Web-Export-Output für `gpt-5_4` ist `model_card: None` — kein WARNING-Log.

**Root Cause:** `load_model_card()` (Zeile 197–243) gibt stillschweigend `None` zurück, wenn `_find_card()` und der Directory-Scan-Fallback beide scheitern. Web-Export setzt `model_card: None` ohne Diagnose.

**Impact:** Niedrig (1 Modell). Sollte aber dokumentiert sein — entweder Blacklist-Eintrag oder `enforce_card_first()`-Aufruf im Web-Export.

---

## Empfohlene Fixes

### Fix-Priorität 1 (KRITISCH) — Modalitäten

In `scripts/web_export.py:660–703` (das `model_card` sub-dict) ergänzen:

```python
"input_modalities": card.get("input_modalities"),
"output_modalities": card.get("output_modalities"),
```

### Fix-Priorität 2 (HOCH) — `judge_context_hint`, `primary_focus`, `unknown`

Ebenda ergänzen:

```python
"primary_focus": card.get("primary_focus"),
"unknown": card.get("unknown"),
"judge_context_hint": card.get("judge_context_hint"),
```

### Fix-Priorität 3 (MITTEL) — Konsistenz

```python
"model_id": card.get("model_id"),     # bereits im Top-Level, für self-contained sub-dict
"model_version": card.get("model_version"),  # bereits als "version" im Top-Level
"generated_at": card.get("generated_at"),
```

### Fix-Priorität 4 (NIEDRIG) — Edge-Case-Logging

In `load_model_card()` (Zeile 197–243): WARNING loggen, wenn keine Card gefunden wurde und weder `card_status="complete"`-Blacklist-Treffer noch Verzeichnis-Fallback hilft. Alternativ: `enforce_card_first()` aufrufen.

### Fix-Priorität 5 (separat) — CoT-Pipeline

Nicht im Web-Export-Scope. Gehört in `probe_thinking`-Workflow: `cot_marker_family` und `cot_tags_detected` mitschreiben, sobald Thinking-Detection läuft.

---

## Tests

Vorhandene Tests: `tests/test_web_export_blacklist.py`, `tests/test_web_export_ssot.py`.
**Lücke:** Kein Test prüft, dass alle Template-Pflichtfelder auch im Export-Sub-Dict landen.

**Vorgeschlagene Tests** (`tests/test_web_export_card_field_coverage.py`):

```python
def test_model_card_subdict_covers_all_web_export_consumer_fields():
    """Alle Card-Felder mit consumers: [web_export] müssen im Export landen."""
    required = load_template_required_fields()
    expected = {f["name"] for f in required if "web_export" in f.get("consumers", [])}
    actual = set(_build_leaderboard_entry(...).get("model_card", {}).keys())
    missing = expected - actual
    assert not missing, f"Card-Felder fehlen im Export: {missing}"
```

---

## Side-Check: Card-Datenqualität

| Aspekt | Status |
|--------|--------|
| `input_modalities` Backfill (v4.7.6) | ✅ 113/113 Karten, Verteilung plausibel (text:52, image+text:47, audio+image+text:14) |
| `output_modalities` Backfill | ⚠️ 113/113 mit `text` only — konservativ, evtl. zu konservativ |
| `architecture_tags` DEPRECATED-Filter | ✅ Funktioniert via `_normalize_export_tags()` |
| `supports_tool_use` Tri-State | ✅ `_supports_tool_use_state()` liefert `"true"` / `"false"` / `None` |
| Emoji-Stripping | ✅ `_strip_emojis()` läuft auf allen Outputs |
| Web-Export-Blacklist | ✅ Funktioniert (exakt + fnmatch-Patterns) |
| Slugify & Card-Lookup | ✅ Funktioniert (mit Fallbacks für Naming-Mismatches) |

**Fazit Datenqualität:** Die Migration v4.7.6 hat die Cards erfolgreich standardisiert. Der Web-Exporter verarbeitet sie weitgehend korrekt — mit der einen **kritischen Lücke**, dass `input_modalities` / `output_modalities` (v4.7.0-Pflicht) nicht durchgereicht werden, obwohl sie explizit als web_export-consumer markiert sind.

---

## Test-Reproduktion

```bash
.venv/bin/python scripts/web_export.py --output outputs/web_export_check
.venv/bin/python -c "
import json
from pathlib import Path
mdl = Path('outputs/web_export_check/raw/models')
for d in sorted(mdl.iterdir()):
    p = d / 'data.json'
    if not p.exists(): continue
    card = json.loads(p.read_text()).get('leaderboard', {}).get('model_card')
    if card is None: print(f'no card: {d.name}'); continue
    for f in ('input_modalities', 'output_modalities', 'judge_context_hint', 'primary_focus', 'unknown'):
        if f not in card: print(f'{d.name}: missing {f}')
"
```

**Erwartetes Ergebnis (nach Fix):** Keine "missing …"-Zeilen.
**Aktuelles Ergebnis (vor Fix):** Jede exportierte Card fehlt 8 Felder.

---

## Post-Fix-Status (v4.7.7, 2026-06-10)

**8 von 10 Findings behoben.** Beide kritischen Befunde (input/output_modalities) sind resolved.

### Was geändert wurde

| Finding | Schweregrad | Status | Fix |
|---------|-------------|--------|-----|
| WEBEXP-001 input_modalities | kritisch | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-002 output_modalities | kritisch | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-003 judge_context_hint | hoch | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-004 primary_focus | hoch | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-005 unknown | hoch | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-006 generated_at | mittel | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-007 model_id | niedrig | ✅ resolved | Im `model_card` sub-dict ergänzt (self-contained) |
| WEBEXP-008 model_version | niedrig | ✅ resolved | Im `model_card` sub-dict ergänzt |
| WEBEXP-009 cot_marker_family/tags | mittel | ⏳ open | Nicht im Web-Export-Scope — Conditional include ist implementiert, Prober muss schreiben |
| WEBEXP-010 gpt-5_4 fehlende Card | niedrig | ⏳ open | Nicht in v4.7.7 — Web-Export loggt `model_card: null`, Ensure-Card-Hook oder Blacklist-Eintrag nötig |

### Verifikation

- **11/11 neue Tests grün** in `tests/test_web_export_card_field_coverage.py`
- **Re-Export:** 92/92 Modelle verarbeitet, 91 mit vollständigen Card-Sub-Dicts
- **Pre-existing Failures:** 14 Tests in `cruciblemark-mcp/tests/test_server.py` (HTTP-404, MCP-Server — nicht durch v4.7.7 verursacht, mit `git stash` reproduziert)

### Bonus: Card-Reparatur

`benchmark_scores/model_cards/gemma-4-12b-it-ud-q8_k_xl.json` wurde während der v4.7.7-Session von einem Card-Generator (Side-Effect) repariert:
- TODO-Platzhalter → echte Werte
- `card_status: complete`, `unknown: false`
- Alle 38 Pflichtfelder vorhanden, 0 TODO-Platzhalter

Eigener Commit `feat(cards): complete gemma-4-12b Q8 K_XL + regenerate _index.json` trennt diese Änderung sauber vom Web-Export-Fix.
