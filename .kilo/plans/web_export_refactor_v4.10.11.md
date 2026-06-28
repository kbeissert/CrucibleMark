# web_export.py Refactor-Plan (Folge-Audit v4.10.11)

**Scope:** 5 verbleibende Schwächen aus skeptischem Audit (Tests, Types, Hardcoded Paths, Helper-Extraktion, SSoT-Wrapper)
**Risiko-Klasse:** Niedrig bis Mittel — keine Verhaltensänderung, nur Code-Qualität
**Strategie:** Ein-Punkt-Refactor mit Test-Validation pro Schritt (kein Skript-basiertes Bulk-Replace — siehe Lesson-Learned aus v4.10.11-Session)

---

## Schwächen (priorisiert)

### Schwachstelle 1: Test-Coverage (0/16 Helper direkt getestet)
**Impact:** Mittel — Refactor-Risiko, Regressionen unentdeckt
**Scope:**
- 16 Helper ohne direkten Test (Stand v4.10.11)
- Bekannt: `_atomic_write_json` hat 5 Tests, `_is_blacklisted` 11, `_collect_vendor_cards` 10
- Lücken: `build_provider_map`, `_build_vendor_alias_map`, `_build_community_alias_map`, `slugify`, `sanitize_audit_log`, `parse_tests_run`, `parse_star_float`, `extract_badge_tier`, `extract_version`, `clean_float`, `_strip_emojis`, `_normalize_vendor`, `_normalize_community`, `_load_pc_block_meta`, `_build_block_scores`, `_build_benchmark_run_dates`

### Schwachstelle 2: Type-Hints unvollständig (3 Return-Types, 8 Arg-Types)
**Impact:** Niedrig — IDE-Hilfe fehlt, mypy-Lücken
**Scope:**
- Arg-Types fehlen: `_atomic_write_json(path, data)` — beide Argumente
- Return-Types fehlen: `_collect_community_cards` (`list[dict]`), `sanitize_audit_log` (str), `parse_tests_run` (`dict | None` ist da), `normalize_pending` (None), `parse_star_float` (`float | None` ist da), `extract_badge_tier` (`str | None` ist da), `extract_version` (`str | None` ist da), `clean_float` (None)
- Manche sind `-> None` implizit ohne Annotation

### Schwachstelle 3: `_BLACKLIST_PATH = Path("config/web_export_blacklist.yaml")` hardcoded relativ
**Impact:** Niedrig — kann bei falschem CWD scheitern
**Fix:** `ROOT_DIR` verwenden (analog zu anderen Skripten) oder per CLI-Flag überschreibbar machen

### Schwachstelle 4: `_process_leaderboard` ist 195 Zeilen (Z.1395-1589)
**Impact:** Mittel — schwer zu testen, schwer zu warten
**Extraktion möglich:**
- `_enrich_provider_metadata()` — Vendor-Card-Lookup + community + privacy
- `_resolve_benchmark_run_dates()` — run_dates Dict
- `_attach_audit_log_context()` — Audit-Log Resolution
- `_attach_review_context()` — Reviews-Resolution
- `_compose_model_entry()` — Final-Dict-Komposition
- Hauptfunktion wird Orchestrator (~30 Zeilen)

### Schwachstelle 5: `_safe_name` Normalisierung verstreut (5 Stellen)
**Impact:** Niedrig — DRY-Verletzung, kein Verhaltensbug
**SSoT-Wrapper in `utils/model_utils.py`:**
- `safe_name_for_filesystem(model_id: str) -> str` — _safe_name wrapper
- `safe_slugify(model_id: str) -> str` — slugify(_safe_name(...)) wrapper
- `normalize_for_comparison(model_id: str) -> str` — _safe_name + lowercase

---

## Refactor-Strategie

### Phase 1: Foundation (Schwachstelle 5 — SSoT-Wrapper) ⏱️ 30 min
**Risiko:** Niedrig — neue Helper, keine Änderung an Aufrufern
**Commit:** `refactor(model_utils): SSoT-Wrapper für _safe_name/slugify`

1. `utils/model_utils.py` 3 Helper hinzufügen:
   ```python
   def safe_name_for_filesystem(model_id: str) -> str:
       """SSoT: _safe_name() für Filesystem-Operationen."""
       return _safe_name(model_id)

   def safe_slugify(model_id: str) -> str:
       """SSoT: slugify(_safe_name(...)) für URL- und Ordner-Slugs."""
       return slugify(_safe_name(model_id))

   def normalize_for_comparison(model_id: str) -> str:
       """SSoT: Normalisierung für Cross-List-Vergleiche (Blacklist, etc)."""
       return _safe_name(model_id).lower()
   ```
2. `tests/test_model_utils_wrappers.py` — 5 Tests (1 pro Helper + Edge-Cases)
3. web_export.py Aufrufer ändern (5 Stellen): NICHT in diesem Schritt (nur Helper-Anlage)

### Phase 2: Type-Hints (Schwachstelle 2) ⏱️ 20 min
**Risiko:** Sehr niedrig — nur Annotationen
**Commit:** `chore(web_export): type-hints für 11 Helper-Funktionen`

1. `_atomic_write_json(path: Path, data: Any, *, indent: int = 2, ensure_ascii: bool = False) -> None`
2. `_collect_community_cards(root_dir: Path) -> list[dict[str, Any]]`
3. `sanitize_audit_log(content: str) -> str`
4. `normalize_pending(val: Any) -> Any`
5. `clean_float(val: Any) -> float | None`
6. mypy clean (lassen laufen)
7. Keine Test-Änderung nötig

### Phase 3: Hardcoded Path (Schwachstelle 3) ⏱️ 10 min
**Risiko:** Niedrig — Default-Verhalten ändert sich nicht
**Commit:** `fix(web_export): _BLACKLIST_PATH relativ zu ROOT_DIR auflösen`

1. `ROOT_DIR` Import (falls noch nicht)
2. `_BLACKLIST_PATH = ROOT_DIR / "config" / "web_export_blacklist.yaml"`
3. Existierender Aufruf-Code unverändert (Pfad-Auflösung passiert automatisch)
4. CLI-Flag `--blacklist-config` ergänzen (optional, default = _BLACKLIST_PATH)
5. Test: 1 Test für `Path-Relativ-Auflösung`

### Phase 4: Test-Coverage (Schwachstelle 1) ⏱️ 90 min
**Risiko:** Niedrig — nur neue Tests
**Commit:** `test(web_export): Coverage für 16 Helper-Funktionen`

Pro Helper-Funktion 1-3 Tests in `tests/test_web_export_helpers.py`:
- `test_build_provider_map` (1)
- `test_slugify` (3: edge cases — empty, mit Sonderzeichen, mit Provider-Prefix)
- `test_sanitize_audit_log` (2: mit/ohne sensible Daten)
- `test_parse_tests_run` (2: int input, dict input)
- `test_normalize_pending` (2: True, False)
- `test_parse_star_float` (3: valid, None, malformed)
- `test_extract_badge_tier` (2: gold, unknown)
- `test_extract_version` (2: 4-stellig, fehlt)
- `test_clean_float` (2: valid, "n/a")
- `test_strip_emojis` (3: nested dict, list, plain string)
- `test_load_model_card` (2: hit, miss)
- `test_normalize_vendor` (2: alias hit, canonical)
- `test_normalize_community` (2: alias hit, canonical)
- `test_load_pc_block_meta` (2: existiert, nicht existiert)
- `test_build_block_scores` (2: mit/ohne missing modules)
- `test_build_benchmark_run_dates` (2: alle Models, leere Liste)

Total: ~30 neue Tests, 1 File.

### Phase 5: Helper-Extraktion (Schwachstelle 4) ⏱️ 60 min
**Risiko:** Mittel — größte Refactor-Funktion, erfordert Sorgfalt
**Commit:** `refactor(web_export): _process_leaderboard in 5 Helper aufteilen`

**Vorbereitung:** _process_leaderboard mit Print-Statements umklammern (welche Zeile produziert welchen Output) → Baseline schaffen

**Schritt 5.1 — `_enrich_provider_metadata` extrahieren:**
```python
def _enrich_provider_metadata(
    model_id: str,
    raw: dict[str, Any],
    vendor_card_lookup: dict[str, dict],
    community_card_lookup: dict[str, dict],
) -> dict[str, Any]:
    """Vendor- + Community-Metadaten aus Cards anreichern."""
    # ~50 Zeilen aus _process_leaderboard
```

**Schritt 5.2 — `_resolve_benchmark_run_dates` extrahieren:**
```python
def _resolve_benchmark_run_dates(model_id: str, root_dir: Path) -> dict[str, Any]:
    """Datum-Informationen aus dispatch_summaries extrahieren."""
    # ~40 Zeilen
```

**Schritt 5.3 — `_attach_audit_log_context` extrahieren:**
```python
def _attach_audit_log_context(model_id: str, root_dir: Path) -> dict[str, Any]:
    """Letzter Audit-Log + Token-Stats + Thinking-Probe."""
    # ~50 Zeilen
```

**Schritt 5.4 — `_attach_review_context` extrahieren:**
```python
def _attach_review_context(model_id: str, root_dir: Path) -> dict[str, Any]:
    """Reviews (regular + bias + tooluse) auflösen."""
    # ~30 Zeilen
```

**Schritt 5.5 — `_process_leaderboard` orchestrator:**
```python
def _process_leaderboard(...) -> dict[str, Any]:
    """Orchestrator: Komponiert Leaderboard-Eintrag aus Sub-Helpern."""
    return {
        **_base_fields,
        **_enrich_provider_metadata(...),
        **_resolve_benchmark_run_dates(...),
        **_attach_audit_log_context(...),
        **_attach_review_context(...),
        "scores": _build_scores(...),
    }
```

Pro Schritt:
1. Test-Suite laufen lassen (Baseline grün = 902/902)
2. Helper extrahieren (manuell, eine Funktion nach der anderen)
3. Test-Suite validieren
4. Falls Regression: Revert + Diff-Analyse

Total: ~30-50 Zeilen pro Schritt-Verschiebung, kein Bulk-Replace.

---

## Lesson-Learned (aus v4.10.11-Session)

⚠️ **NIEMALS `python3 << EOF`-Skript für Web-Export-Refactoring verwenden.** Vorheriger Versuch hat 417 Zeilen gelöscht, weil Bulk-Replace auch umliegende Funktionen ersetzt hat.

**Regel:** Refactor = manuell + pro Schritt + Test-Validation. Kein Skript-basiertes Bulk-Replace.

---

## Reihenfolge

1. **Phase 1** (SSoT-Wrapper) — Foundation, alle anderen Phasen nutzen sie
2. **Phase 2** (Type-Hints) — Quick-Win, kein Risiko
3. **Phase 3** (Hardcoded Path) — Quick-Win, kein Risiko
4. **Phase 4** (Test-Coverage) — Schafft Sicherheitsnetz für Phase 5
5. **Phase 5** (Helper-Extraktion) — Größter Hebel, braucht Tests als Sicherheitsnetz

**Geschätzter Aufwand:** 3.5 Stunden, 5 Commits
**Empfehlung:** Erst alle Quick-Wins (Phase 2+3) als Bulk-Commit, dann Test-Phase 4, dann Phase 5 mit Sicherheitsnetz.

---

## Out-of-Scope (separater Audit nötig)

- `_build_vendor_alias_map` + `_build_community_alias_map` — fast identisch (DRY-Verletzung)
- Hardcoded String-Konstanten ("todo", "unknown", "community", "vendor") — Enum-Kandidaten
- `_init_export_context()` 40+ Zeilen — Setup-Pattern auch in anderen Scripts dupliziert
- Dataclass statt TypedDict für `_CardMetadata`, `_RunDates` — würde Type-Safety deutlich verbessern
