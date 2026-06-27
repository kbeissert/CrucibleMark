# Web-Export-Audit (Post-Refactor v4.10.11)

**Datum:** 2026-06-27
**Scope:** `scripts/web_export.py` nach Phase 1-5 Refactor
**Code-Basis:** 1740 Zeilen, 53 Funktionen, 972 Tests grün
**Auditor:** Skeptische Code-Review nach "MiniMax M3 Refactoring"

---

## ✅ Positiv (Bestätigt funktionierend)

### Struktur
- 53 Funktionen, modular aufgebaut, klare Trennung: Helper (CSV-parsing), 
  Lookup-Maps, Export-Logik, Orchestrator
- `_process_leaderboard` 166 Zeilen (vorher 195) — 2 Helper extrahiert
- Atomic Writes via `_atomic_write_json` an allen 7 JSON-Write-Stellen
- Type-Hints für 5 Helper ergänzt, `Callable` für DI-Testbarkeit
- Defense-in-Depth: `_PLACEHOLDER_VENDOR_IDS`, `unknown=true` Filter
- Blacklist-Normalisierung via `_safe_name()` an beiden Seiten

### Tests
- 972 Tests, alle grün
- Test-Coverage für 12 Helper (Phase 4) + 2 extrahierte Helper (Phase 5)
- 3 SSoT-Wrapper-Tests (Phase 1)
- 3 Blacklist-Path-Tests (Phase 3)

### Real-World
- Export: 75 Models, 17 Providers, 0 Errors
- Hugo-Build: 319 Files, 0.81s

---

## 🔴 Hochpriorisierte Befunde (Bug / Behavior)

### BUG 1: `provider_landscape_review.md` Fallback ist ein No-Op
**Ort:** `_write_top_level_outputs` Z.1295-1307
**Symptom:** Legacy-Fallback ist identisch zum Primary-Pfad → Fallback tot

```python
# In main(): comparisons_path = root_dir / "docs" / "reviews"
provider_md = comparisons_path / "provider_landscape_review.md"
if not provider_md.exists():
    legacy_md = comparisons_path.parent / "reviews" / "provider_landscape_review.md"
    # ↑ comparisons_path.parent = docs/
    # ↑ docs/"reviews"/"provider_landscape_review.md" == comparisons_path/"provider_landscape_review.md"
```

`comparisons_path = docs/reviews/`, dann ist `comparisons_path.parent / "reviews" / ...` identisch zu `comparisons_path / ...` — der Fallback ist ein No-Op.

**Fix:** Beide Pfade direkt prüfen, unabhängig von `comparisons_path`:
```python
primary = root_dir / "docs" / "comparisons" / "provider_landscape_review.md"
legacy = root_dir / "docs" / "reviews" / "provider_landscape_review.md"
provider_md = primary if primary.exists() else (legacy if legacy.exists() else None)
```

`root_dir` muss als zusätzlicher Parameter an `_write_top_level_outputs` übergeben werden (ist bereits vorhanden).

### BUG 2: Warning-Spam für geskippte Modelle
**Ort:** `_resolve_model_dirs_and_card` Z.1473-1479
**Symptom:** Für geskippte Modelle (blacklisted / no_benchmark) wird WARNING geloggt,
obwohl das Model ohnehin nicht im Export landet

Reihenfolge in `_process_leaderboard`:
1. `_resolve_model_dirs_and_card` (logt WARNING bei fehlender Card)
2. `_should_skip_model` (entscheidet Skip)

Bei 30+ geskippten Modellen mit fehlender Card → 30+ WARNING-Zeilen im Log.

**Fix:** Entweder:
- Option A: Warning erst NACH Skip-Prüfung loggen (Card-Suche verzögern)
- Option B: `_resolve_model_dirs_and_card` Parameter `warn_on_missing_card: bool = True`,
  im Skip-Pfad auf False setzen

Option B ist minimal-invasiv.

### BUG 3: Non-atomic writes für Markdown-Dateien
**Ort:** `_export_model_files` Z.826, 836, 839; `_write_top_level_outputs` Z.1302
**Symptom:** 4× `write_text` / `shutil.copy2` ohne Atomic-Write-Pattern

Bei Crash mid-write → korrupte Markdown-Datei (Audit-Logs, Reviews, Provider-Landscape).

**Fix:** `_atomic_write_text` und `_atomic_copy` Helper einführen
(Generalisierung von `_atomic_write_json`).

---

## 🟡 Mittelpriorisierte Befunde (Code Quality)

### BEFUND 4: `_collect_vendor_cards` doppeltes Lesen
**Ort:** `_write_top_level_outputs` Z.1280, 1288
**Symptom:** `_collect_vendor_cards(exclude_community=True)` liest alle Karten,
dann `_collect_community_cards(root_dir)` liest nochmal alle Karten (via internen
`_collect_vendor_cards(root_dir)` ohne Filter).

Bei 27 Vendor-Cards → 54 File-Reads statt 27.

**Fix:** Einmal lesen, dann in Memory splitten:
```python
all_cards = _collect_vendor_cards(root_dir)
vendor_cards = [c for c in all_cards if c.get("card_subtype") != "community"]
community_cards = [c for c in all_cards if c.get("card_subtype") == "community"]
```

### BEFUND 5: `_strip_none` inkonsistent für Listen
**Ort:** Z.1730-1736
**Symptom:** Dict-None-Werte werden entfernt, Listen-None-Items bleiben erhalten.
Dokumentiert, aber inkonsistent.

```python
_strip_none({"a": None, "b": "x"})  # → {"b": "x"}
_strip_none([None, "a", None])      # → [None, "a", None]  ← None bleibt!
```

Bei `heritage_ids: [None, "old-id"]` (kaputte Card) → JSON-Liste mit `null`-Item.

**Fix:** Listen-Filter optional via Parameter, oder dokumentiert lassen
(wahrscheinlich absichtlich, weil leere Listen verschieden von `null` sind).

### BEFUND 6: `_resolve_dir` Fallback 3 (-latest) fängt nur ImportError
**Ort:** Z.748-757
**Symptom:** `get_model_version()` kann `ValueError`/`KeyError` werfen,
die propagieren und Export crashen.

```python
try:
    from utils.model_utils import get_model_version as _gmv
    _ver = _gmv(raw_slug, provider="api")
except ImportError:
    _ver = None
```

**Fix:** `except (ImportError, Exception)` oder spezifischere Exceptions.

### BEFUND 7: Logging f-string statt lazy %-formatting
**Ort:** 8 Stellen (siehe grep)
**Symptom:** f-strings werden immer formatiert, auch bei disabled Log-Level.

```python
logging.debug(f"  [{count}/{total}] {model_name} -> SKIP")  # immer formatiert
logging.debug("  [%s/%s] %s -> SKIP", count, total, model_name)  # lazy
```

**Fix:** Alle f-string-Logs zu %-formatting migrieren (Standard-Pattern).

### BEFUND 8: Tautologie-Assert in `_setup_output_dirs`
**Ort:** Z.772
**Symptom:** `assert models_dir == (out_dir / "models")` ist immer True,
weil `models_dir = out_dir / "models"` in Z.771 gesetzt wurde. Kein echter
Safety-Check.

**Fix:** Assert durch echten Pfad-Check ersetzen:
```python
assert out_dir.name == "raw", f"out_dir muss in raw/ enden, ist: {out_dir}"
assert out_dir.parent != Path("/"), "out_dir darf nicht Root sein"
```

### BEFUND 9: `_lookup_pc_row` O(n*m) Komplexität
**Ort:** Z.1036-1042
**Symptom:** Für jedes Modell wird über alle AVG-Rows iteriert (mit Suffix/Prefix-Match).
Bei 100 Modellen × 100 AVG-Rows = 10000 String-Vergleiche.

**Fix:** Pre-built slug→row Map (ähnlich `pc_lb_slug_map`).

---

## 🟢 Niedrigpriorisierte Befunde (Out-of-Scope)

### BEFUND 10: SSoT-Wrapper ungenutzt
`safe_name_for_filesystem` und `normalize_for_comparison` in `utils/model_utils.py`
haben keine Production-Caller. Empfehlung aus v4.10.11-Audit: Migration in
`_resolve_model_dirs_and_card` und `_is_blacklisted`.

### BEFUND 11: `_build_vendor_alias_map` + `_build_community_alias_map` DRY-Verletzung
Fast identische Implementation (nur `manufacturers` vs `communities` Key).
Könnte zu `_build_alias_map(config_dir, section)` konsolidiert werden.

### BEFUND 12: Test-Coverage-Lücken
11 Funktionen ohne direkte Tests:
- `_resolve_dir`, `_build_compass_entry`, `_lookup_pc_row`
- `_build_tooluse_entry`, `_export_model_files`, `_review_date_range`
- `_build_benchmark_run_dates`, `find_latest_markdown`
- `_setup_output_dirs`, `_init_export_context`, `_write_top_level_outputs`
- `compute_is_retest`, `_supports_tool_use_state`, `_read_latest_tooluse_narrative`

### BEFUND 13: `parse_tests_run`, `extract_badge_tier`, `extract_version` ohne Type-Hints
```python
def parse_tests_run(val) -> dict | None:        # val: Any fehlt
def extract_badge_tier(val) -> str | None:      # val: Any fehlt
def extract_version(val) -> str | None:         # val: Any fehlt
```

### BEFUND 14: `_collect_vendor_cards(exclude_community=True)` nicht getestet
Filter-Verhalten ist nur über `_collect_vendor_cards` (ohne Filter) getestet.

### BEFUND 15: `compute_is_retest` ohne Type-Hints
```python
def compute_is_retest(lb_row):  # kein Return-Type, kein Param-Type
```

---

## 📊 Fazit

**Gesamturteil:** Skript ist funktional korrekt, Produktion läuft fehlerfrei.
ABER 3 echte Bugs (Hoch-Prio) + 6 Code-Quality-Issues identifiziert.

**Dringlichkeit:**
- BUG 1 (provider_landscape_review Fallback): SOFORT fixen — Datei ist 2,5 Monate veraltet,
  Fallback-Logik ist kaputt, Warning wird immer getriggert
- BUG 2 (Warning-Spam): Beeinträchtigt nur Logs, nicht Funktionalität — mittlere Dringlichkeit
- BUG 3 (Non-atomic Markdown writes): Niedrige Dringlichkeit (Markdown-Korruption weniger kritisch als JSON)

**Empfehlung:** BUG 1 sofort fixen (5-Zeilen-Änderung), BUG 2 + 3 in nächstem Sprint.
Rest dokumentiert für zukünftigen Refactor-Pass.
