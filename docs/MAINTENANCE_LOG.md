# CrucibleMark: Maintenance & Fehlerbehebungen

**Zielgruppe:** Entwickler, die Änderungen am Scoring-System oder der Architektur nachvollziehen wollen.
**Inhalt:** Changelog-Einträge für Bugfixes, Architektur-Entscheidungen und Verhaltensänderungen

---


## v4.6.8 — Makefile help v2 + argparse fuer 3 Skripte (Phase 29, 2026-06-08)

### 1. `Makefile` — Help-Text komplett refaktoriert

Phase 28 hat den Cleanup-Dispatcher modernisiert; das `make help`-Target
war aber historisch gewachsen und listete nur ca. 73 von 83 Targets.
Phase 29 schliesst diese Doku-Luecke:

- **Alle 83 Targets dokumentiert** — fehlten vorher u.a. `mcp-start`,
  `mcp-stop`, `mcp-health`, `mcp-mock`, `tooluse-leaderboard`,
  `tooluse-report`, `tooluse-report-summary`, `tooluse-report-json`,
  `tooluse-run`, `clean-wizard`, `validate-cards`, `validate-structure`,
  `sync-cost-limits`, `update-prices`, `model-card` (Singular-Alias).
- **Format vereinheitlicht** — 2-Spalten-Schema (Target + Beschreibung,
  Flags in eckigen Klammern).
- **Sektionen entsprechen Recipe-Reihenfolge** im Makefile (Benchmarking
  → Tool-Use → PC → Reviews → Card-Lifecycle → Validation → Tools →
  MCP → Web → Cleanup → Backup).
- **Card-Lifecycle 5+1 Phasen** — statt vermischter Help-Block. Phase 6
  (Thinking-Probe) als neue eigene Phase.
- **Global-Flags-Sektion erweitert** um `DRY=1`, `YES=1`, `JSON=1`,
  `PROVIDER=name`.

### 2. `scripts/maintenance/cleanup_helpers.py` — argparse statt sys.argv-Hack

**Vorher** (Zeile 234): ``dry = "--dry-run" in sys.argv`` — hackig,
bricht wenn Argumente umsortiert werden.

**Nachher**: argparse mit `description` und sauberer `--dry-run` Action.
Das Skript verhaelt sich jetzt wie ein normales CLI-Tool.

### 3. `scripts/maintenance/consolidate_csv.py` — argparse fuer --help

**Vorher**: Kein argparse. ``--help`` crasht mit exit 2 ohne Message.

**Nachher**: Minimaler argparse-Wrapper. Hauptaufgabe (Konsolidierung) ist
ohne Flags lauffaehig, `python consolidate_csv.py --help` zeigt jetzt
saubere Usage.

### 4. `scripts/tools/validate_assets.py` — argparse + Bug-Fix

**Bug**: ``validate_assets.py --help`` crashte mit
``❌ Pfad nicht gefunden: --help`` — weil ``Path(sys.argv[1])`` alles
als Pfad interpretiert.

**Fix**:
- argparse ersetzt ``len(sys.argv) > 1`` Pattern.
- `path` jetzt positional mit `nargs="?"`.
- `--all` als Action-Argument.
- `MIN_CLI_ARGS` Konstante entfernt (ungenutzt).
- `parser.error()` fuer saubere Fehlermeldung wenn weder path noch
  `--all` angegeben.

### Verifikation

- `pytest tests/ -q` → 459/459 gruen (unveraendert gegen Phase 28).
- `pylint scripts/maintenance/cleanup_helpers.py
  scripts/maintenance/consolidate_csv.py scripts/tools/validate_assets.py`
  → 10.00/10.
- `make help` → alle 83 Targets sichtbar (vorher 73).

### SSoT-Vertrag

Die Makefile-CLI folgt jetzt einem einheitlichen Schema:
1. `make help` listet alle Targets mit Flags und Pflicht-Variablen.
2. Skripte mit `argparse` unterstuetzen `--help` und saubere Usage.
3. Fehlende Pflicht-Variablen (MODEL, MODULE, ASSET) fuehren zu exit 1
   mit klarer Fehlermeldung im Makefile-Recipe.


## v4.6.7 — make clean Hardening + toter Code weg (Phase 28, 2026-06-08)

### 1. `scripts/maintenance/clean_results.py` — ID-SSoT + CSV-SSoT-Anbindung

Phase 27 hat die CSV-Konsolidierung an `utils.backup_targets.CSV_FILES`
angebunden — `clean_results.clean_csv()` aber nicht. Es hatte eine
hardcoded Liste von 6 Pfaden und nutzte naive String-Gleichheit fuer
den Modell-Match. Phase 28 schliesst diese Luecken:

- **ID-Normalisierung**: `clean_csv()` nutzt jetzt
  `resolve_canonical_model_id()` fuer den Vergleich. Vorher
  matchte `make clean-model MODEL=qwen3.5-35b` keine Zeilen mit
  `qwen_qwen3.5-35b` (Schreibweisenvariante). Jetzt schon.
- **CSV-Liste aus SSoT**: `CLEAN_CSV_FILES` baut sich aus
  `utils.backup_targets.CSV_FILES` + `PC_CSV_FILES` (PC hat eigenen
  Dedup-Key `(model, model_version, run_id)`, nicht `(model, asset_id)`).
  Hardcoded Liste weg.
- **logging.exception()** statt `print()` in der CSV-Error-Path
  (sichtbare Stacktraces in CI).

### 2. `scripts/maintenance/clean.py` — Subprozess-Deprecation

Vorher: `_run_clean_results()` rief `subprocess.run([sys.executable,
...])` auf — das startete einen zweiten Python-Prozess pro Clean-Call
(~250 ms Overhead, kein Logger-Sharing, Exit-Code ging verloren).

Phase 28: Direkter Funktionsaufruf via neuem `clean_results.main_with_args(args)`.
- Spart den zweiten Python-Start.
- Teilt den Logger mit dem Dispatcher.
- `clean_results.main()` extrahiert die Logik in `_run_clean_logic()`,
  die von beiden Entry-Points genutzt wird.

### 3. `scripts/maintenance/clean_versions.py` — toter Code entfernt

Das Skript war:
- nirgendwo im Makefile referenziert,
- lief bei jedem Import sofort los (kein `__main__`-Guard),
- enthielt eine hardcoded Migration
  `claude-opus-4-6 -> claude-3-5-opus-latest` (nicht-existente
  Modell-Variante — `claude-opus-4-6` ist die aktuelle Version),
- wuerde bei versehentlichem Aufruf jetzt aktive Daten korrumpieren.

Phase 28: Datei geloescht. `tests/test_clean_versions_deletion.py`
verhindert Re-Introduktion (gibt klare Anweisung, wo eine
zukuenftige Legacy-Migration stattdessen landen muss:
als getesteter Helper in `utils/model_utils.py`).

### 4. `Makefile` — `DRY=1`-Flag fuer `clean-model`/`clean-module`/`clean-all`

Konsistent mit `make clean-runs` (FORCE-Flag) und
`make backup-prep` (DRY_RUN-Flag) ist `DRY=1` jetzt der Standard-Weg
fuer Vorschau-Modus:

- `make clean-model MODEL=x` (echte Loeschung)
- `make clean-model MODEL=x DRY=1` (Vorschau)
- `make clean-module MODULE=x DRY=1` (Vorschau)
- `make clean-all DRY=1` (Vorschau)

Help-Text entsprechend erweitert.

### 5. Tests (3 neue Dateien, 13 Tests)

- `tests/test_clean_results.py` (8 Tests): ID-Normalisierung,
  CSV-SSoT-Konsistenz, dry-run, main_with_args-Direktaufruf
- `tests/test_clean.py` (4 Tests): Subprozess-Deprecation, Dispatcher
- `tests/test_clean_versions_deletion.py` (1 Test): Re-Introduktion-Schutz

Alle Tests nutzen `tmp_path` und `monkeypatch` — keine externen
Effekte, keine Subprozesse, keine Live-CSV-Beruehrung.

### 6. SSoT-Vertrag

`make clean-*` verwendet jetzt ausschliesslich SSoT-Listen aus
`utils/backup_targets` (CSV-Pfade) und `utils/model_utils`
(ID-Normalisierung). Keine hardcoded Pfade, keine hardcoded
Modell-IDs mehr in der Clean-Pipeline.


## v4.6.6 — Backup-System SSoT + ID-Normalisierung (Phase 27, 2026-06-08)

### 1. `utils/backup_targets.py` — neue SSoT-Konfigurationsdatei

Eine einzige Datei bündelt jetzt alle Listen, Defaults und Excludes, die
vorher über vier Skripte verstreut waren:

- `BACKUP_TARGETS` — Verzeichnisse im tar-Snapshot (8 Einträge)
- `build_tar_excludes()` — 11 tar-Excludes (vorher: 3, hartkodiert im Makefile)
- `CSV_FILES` — 4 CSVs mit Deduplizierungs-Schlüsseln (SSoT für `consolidate_csv.py`)
- `RUNS_KEEP_DEFAULT = 5` — Cleanup-Default (vorher hardcoded in 2 Skripten)
- `REVIEWS_KEEP_PER_CATEGORY = 1` — Review-Cleanup-Default
- `UNREACHABLE_LOG_MAX_AGE_DAYS = 7` — Crash-Log-Schwellwert
- `BACKUP_ROTATION_DAYS = 90` — Snapshot-Rotations-Empfehlung
- `all_targets_exist()` / `all_csv_targets_exist()` — Konfig-Invarianten

### 2. `scripts/maintenance/cleanup_helpers.py` — neue SSoT-Helper

- `canonical_model_slug()` — delegiert an `resolve_canonical_model_id()`, fällt auf `_safe_name()` zurück
- `canonicalize_run_grouping()` — gruppiert Run-Files nach kanonischer ID, sortiert mtime-absteigend
- `pre_backup_hygiene()` — neue Pre-Backup-Hygiene mit 3 Aktionen:
  1. Alte `tooluse_unreachable_*.json` löschen (älter als 7 Tage)
  2. Legacy-Backup-Artefakte nach `backups/_pre_clean_YYYYMMDD_HHMMSS/` verschieben
  3. `outputs/temp/session_*.json` löschen
- `run_pre_backup_hygiene()` — Convenience-Wrapper mit Log-Summary

### 3. ID-SSoT-Schließung in 3 Cleanup-Skripten

Vorher nur in `prune_orphaned_reports.py` aktiv. Jetzt auch in:

- **`cleanup_runs.py`**: `get_benchmark_files()` nutzt `canonicalize_run_grouping()` — `qwen3.5-35b-q4` und `qwen_qwen3.5-35b-q4` landen in derselben Gruppe. `--keep` Default kommt aus SSoT.
- **`consolidate_csv.py`**: Neue `_normalize_model_column()`-Funktion normalisiert die `model`-Spalte via `resolve_canonical_model_id()` **bevor** dedupliziert wird. Logging: `🔗 Model-IDs via SSoT normalisiert.`
- **`cleanup_reviews.py`**: Verzeichnisnamen via `_safe_name` normalisiert (Robustheit bei Slug-Drift).

### 4. `clean.py` — RUNS_KEEP_DEFAULT-Integration

`interactive_wizard` und `cleanup_runs()` nutzen `RUNS_KEEP_DEFAULT` aus SSoT statt hardcodiertem `1`.

### 5. `Makefile` — `backup-prep`-Target + RUNS_KEEP-Variable

- Neue Variable `RUNS_KEEP ?= 5` (SSoT-Spiegelung)
- Neues Target `backup-prep` mit `DRY_RUN=1` Switch
- `backup: backup-prep` (Dependency — keine doppelte Logik)
- `clean-runs` nutzt `$(RUNS_KEEP)` statt hardcoded `1`
- tar-Recipe erweitert um 7 weitere Excludes (10 statt 3)
- Help-Text mit `=== Data Management & Cleanup ===` und `=== Backup-Lifecycle ===` Sektionen

### Tests

- `tests/test_backup_targets.py` — 18 Tests (Konfig-Invarianten)
- `tests/test_cleanup_helpers.py` — 19 Tests (ID-SSoT + Hygiene)
- `tests/test_cleanup_runs.py` — 14 Tests (Gruppierung + Cleanup)
- `tests/test_consolidate_csv.py` — 12 Tests (ID-Normalisierung)
- `tests/test_cleanup_reviews.py` — 11 Tests (Review-Cleanup)

**Verifikation:** 74 neue Tests grün, bestehende 318 Tests weiter grün, Pylint 10.00/10.

### SSoT-Vertrag

> **Vorteil:** Ein Drift in Cleanup-Defaults, Excludes oder CSV-Listen ist
> jetzt an *einer* Stelle zu fixen — nicht mehr über vier Skripte verstreut.

Vorher hatte `make clean-runs FORCE=1` `clean.py --runs 1` aufgerufen (im
Widerspruch zur Doku, die „5 letzte Runs" sagt). Jetzt gilt: `RUNS_KEEP` im
Makefile = `RUNS_KEEP_DEFAULT` im Python = beide spiegeln die Doku.

---



## v4.6.1 — CSV-Hygiene Defense-in-Depth (2026-06-08)

### 1. `utils/result_manager.py::_validate_row_for_write()` — Hard-Fail-Guard

Neue Methode, die jede Zeile VOR dem CSV-Write gegen die Sanitizer-Heuristiken prüft.
Wirft `ValueError` bei:
- **Header-Repeat** — `parts[0] == 'asset_id'` (Header als Datenzeile)
- **Narrative Asset-ID** — `_is_narrative_asset_id()` (Rohtext-Fragmente)
- **Invalid Model** — `_is_invalid_model()` (Boolean, NaN, leer)

`_write_to_csv()` fängt die Exceptions ab, loggt sie mit `[Hard-Fail-Guard]`
und überspringt die korrupte Zeile. Save-Operation läuft resilient weiter.

### 2. `scripts/maintenance/consolidate_csv.py::_filter_corrupt_rows()` — Sanitizer-Apply

Wendet die identischen Heuristiken auf den DataFrame VOR `to_csv()` an.
Verhindert dass Maintenance-Konsolidierung Müll zurück in die CSV schreibt.
Logging mit Korrupt-Drop-Counter:

```
🗑️  Korrupt-Drop: header_repeat               N
🗑️  Korrupt-Drop: narrative_asset_id          N
🗑️  Korrupt-Drop: invalid_model               N
```

### 3. `Makefile::validate-csv` — neues Target

```
make validate-csv
```

Dry-Run-Modus: zeigt Korruption, ändert nichts. CI-/Smoke-tauglich.

### Tests

- `tests/test_consolidate_csv_validates.py` (9 Tests)
- `tests/test_result_manager_validates.py` (7 Tests)

**Verifikation:** 226/226 grün, Pylint 10.00/10.

### Live-Check auf 3 Benchmark-CSVs

| CSV | Rows | Drops |
|---|---|---|
| `local_models_benchmark.csv` | 1013 | 0 |
| `cloud_models_benchmark.csv` | 1282 | 0 |
| `commercial_models_benchmark.csv` | 1940 | 0 |

Phase-8-Erfolg hält. Defense-in-Depth ist etabliert.

## v4.6.0 — CSV-Hygiene-Sanitizer (2026-06-08)

**Status:** Abgeschlossen

### 1. `scripts/maintenance/sanitize_benchmark_csvs.py` — neuer Sanitizer

Inhalts-Korruption in `local_models_benchmark.csv` identifiziert: 17705 Zeilen
davon 13265 mit leerem `model`-Feld (75 Prozent), verursacht durch
ungenügend-escapte LLM-Rohtext-Antworten, die als Datenzeilen in die CSV
geschrieben wurden. Sanitizer-Skript entfernt vier Klassen von Müll-Zeilen
vor jeder weiteren Verarbeitung.

**Filter-Heuristiken:**

- **Header-Repeat** — `parts[0] == 'asset_id'` (Header wurde als Datenzeile
  geschrieben, weil eine vorherige Iteration eine Header-Zeile emittiert hat).
- **Rohtext-Asset-ID** — `len > 60` ODER Romananfang-Prefix (the, for, final,
  this, these, model, models, first, second, however, moreover, therefore,
  in summary, to summarize) ODER Markdown-Marker (`##`, `###`, `---`, `***`,
  `===`).
- **Boolean-Modell** — `model` ist `True` / `False` (case-insensitive) —
  wurde aus einer Bool-Spalte in die `model`-Spalte verschoben.
- **Leeres Modell** — `model` ist NaN, leerer String oder pandas-Sentinel.

**Pipeline:**

- `--apply` macht `.bak`-Backup (idempotent) und schreibt atomar via `.tmp` +
  `replace()`. Dry-Run ist Default.
- Exit-Code 0 in beiden Modi; Logs zeigen Drop-Counter pro Filterklasse.
- SSoT-CSV-Pfade stammen aus `scripts.leaderboard.config` (LOCAL_CSV,
  CLOUD_CSV, COMMERCIAL_CSV). Fehlende CSVs werden sauber übersprungen.

### 2. `tests/test_sanitize_benchmark_csvs.py` — 65 Tests grün

Vollständige Test-Pyramide:

- **Filter-Unit-Tests** (3 Klassen) — Header-Repeat, Narrative-Asset-ID
  (inkl. parametrisiert für alle 14 Romananfänge und 5 Markdown-Marker),
  Invalid-Model (inkl. 5 pandas-Sentinel-Varianten).
- **Pipeline-Test** (`TestFilterRows`) — kombinierte Szenarien inkl.
  Status-abhängige Drop-Klassifikation (`invalid_model_*` vs.
  `invalid_model_*_non_success`).
- **Backup-Test** (`TestBackupCsv`) — Idempotenz: zweiter Aufruf
  überschreibt vorhandenes `.bak` nicht.
- **Atomic-Write-Test** (`TestWriteCsvAtomic`) — keine `.tmp`-Leftovers,
  CSV-Round-Trip über `csv.reader`.
- **E2E-Tests** (`TestMainDryRun`, `TestMainApply`) mit `monkeypatch`
  auf die SSoT-Pfade, inkl. kombiniertem Szenario mit allen vier
  Korruptions-Klassen gleichzeitig.

### 3. Daten-Bereinigung (live angewendet am 2026-06-08)

| CSV | Vorher | Nachher | Verworfen |
|---|---|---|---|
| `local_models_benchmark.csv` | 14479 | 1013 | 13466 (93 %) |
| `commercial_models_benchmark.csv` | 1951 | 1940 | 11 (0.6 %) |
| `cloud_models_benchmark.csv` | (n/a) | (n/a) | 0 (bereits sauber) |

**Backups:** `benchmark_scores/local_models_benchmark.csv.bak`,
`benchmark_scores/commercial_models_benchmark.csv.bak` (idempotent, d.h.
nicht überschrieben bei weiteren Läufen).

### 4. Leaderboard-Befund nach Sanitizer

`make leaderboard` regeneriert: 84 Zeilen, 78 vollständig (43/43 Tests),
5 unvollständig mit 40–42 von 43 Tests (echte Test-Lücken, die das
Auto-Benchmark füllen muss):

- Kimi K2.6 (40/43)
- DeepSeek V4 Pro (42/43)
- Qwen 3.5 397B A17B (40/43)
- MiniMax M2.7 (42/43)
- GLM-4.7 (42/43)

1 Modell mit 49/43 (Test-Override-Logik / Tool-Use-Backlog).

### Lessons Learned

- **CSV-Korruption war strukturell unsichtbar** — `pd.read_csv()` lud
  die Zeilen als String-Spalten; erst die explizite
  `df['model'].isna().sum()`-Analyse brachte das Ausmaß ans Licht.
- **Sanitizer ist defensiv-präventiv** — Dry-Run-Default macht ihn
  für CI-Smoke-Tests sicher; `--apply` erfordert explizite User-Freigabe.
- **Filter-Heuristiken sind Heuristiken** — `MAX_VALID_ASSET_ID_LEN=60`
  ist großzügig kalkuliert; falls neue Asset-Schemata auftauchen
  (z.B. `long_named_asset_xyz_001`), muss der Wert mitwachsen.

### Verifikation

- `pytest tests/ -v --tb=short` → 210/210 passed.
- Pylint 10.00/10 für `sanitize_benchmark_csvs.py` und
  `test_sanitize_benchmark_csvs.py`.

---

## v3.16.0 — Provider-Config-Split + llamacpp-Provider (2026-05-30)

**Status:** Abgeschlossen

### 1. `utils/providers/llamacpp.py` — neuer lokaler Provider

Neuer Provider-Connector für llama.cpp-Server (OpenAI-kompatible API, lokal).

- Verwaltet Server-Lifecycle (Start/Stop/Modell-Swap via `subprocess.Popen`, PID-Tracking)
- Health-Check via `/health`-Endpoint (`urllib`, kein `/v1/models`)
- Auto-Swap beim Modellwechsel (`query()` → `_swap_model()`)
- `n_gpu_layers`-Fallback: 99 (vollständiges GPU-Offloading)
- Konfiguration in `config/provider_config.yaml → providers.local.llamacpp`

### 2. Provider-Config-Split — `benchmark_config.yaml` / `config/provider_config.yaml`

Der `providers:`-Block wurde aus `benchmark_config.yaml` in eine separate Datei ausgelagert:

- **`benchmark_config.yaml`** — Laufzeit- und Benchmark-Parameter (Module, Scoring, Logging, Output, Token-Budgets)
- **`config/provider_config.yaml`** — Provider-Konfiguration (Modell-Listen, API-Flags, lokale Server-Config)

`ConfigValidator` merged beide Dateien beim Start transparent (SCSS-Partial-Prinzip). Alle anderen Scripts sehen dasselbe Config-Objekt — keine Script-Änderungen erforderlich.

### 3. `ConfigValidator._check_duplicate_model_ids()` — Duplikat-Schutz

Beim Merge prüft `ConfigValidator` alle explizit gelisteten Modell-IDs über alle Provider hinweg. Duplikate werden als `WARNING` geloggt (First-Win-Semantik). `auto_discover`-Provider (Ollama) werden ausgenommen.

```
WARNING: Duplikat-Modell-ID 'gpt-5.5': bereits registriert unter 'commercial/anthropic',
         Eintrag unter 'commercial/openai' wird ignoriert.
```

### 4. Provider `enabled`-Flag — vollständige Wizard-Sichtbarkeit

Ist `enabled: false` gesetzt, erscheint der Provider weder im Single-Run-Wizard (`provider_selector.py`) noch im Cross-Model-Benchmark (`run_cross_model_benchmark.py`).

---

## v3.15.0 — Tool Use Probe-Run 5 Modelle (2026-05-25)

**Status:** Abgeschlossen

### 1. `tooluse_exporter.py` — `cost_usd="local"` für Open-Weights

`_LOCAL_DEPLOYMENT_TYPES` enthielt `{"localweights", "open-weights-cloud-available"}`.
Modelle mit `deployment_type: "open-weights"` (lokal via Ollama, z. B. gemma4:E4B) wurden
numerisch als `0.0` ausgewiesen — korrekt mathematisch, aber semantisch irreführend.

**Fix:** `"open-weights"` als dritten Typ in `_LOCAL_DEPLOYMENT_TYPES` aufgenommen.
`cost_usd`-Spalte im Leaderboard zeigt jetzt `"local"` für alle lokalen Deployment-Typen.

### 2. Probe-Run Ergebnisse (5 Modelle, mode=live)

Live-Benchmark gegen echte MCP-Tools (Tavily web_search + httpbin http_fetch):

| Modell | Combined | P1 | P2 | Halluz. | Empfehlung |
|---|---|---|---|---|---|
| gpt-5-mini | 76.5% | 90.0 | 63.3 | Nein | [PRODUCTION] |
| grok-4-fast-non-reasoning | 74.2% | 86.7 | 63.3 | Nein | [PRODUCTION] |
| moonshotai/kimi-k2 | 73.6% | 89.2 | 58.3 | Ja (2×) | [NOT_RECOMMENDED] |
| qwen/qwen3-32b | 72.9% | 90.0 | 58.3 | Ja (2×) | [NOT_RECOMMENDED] |
| gemma4:E4B | 65.7% | 86.7 | 45.8 | Ja (1×) | [NOT_RECOMMENDED] |

PRODUCTION-Kriterium: keine Halluzination + alle 6 Tool-Calls valide.
Leaderboard: 11 Modelle (inkl. Calibration-Run-Modelle).

### 3. gemma4:E4B fleet_group-Backfill

`fleet_group` war nicht gesetzt — Bug aus früherer Session. Manuell backfilled:
`fleet_group=local_sovereign`, `sovereignty_gap=-7.28` (local_avg 65.7 − all_avg 73.0).

---

## v3.14.0 — Bug-Fixes Tool Use Benchmark (2026-05-25)

**Status:** Abgeschlossen

### 1. `utils/providers/anthropic.py` — `system`-Kwarg Silent Drop

**Problem:** `system`-Parameter in `call_with_retry(**kwargs)` wurde nicht aus `**kwargs`
extrahiert, sondern blind weitergereicht. Anthropic-API ignoriert unbekannte Kwargs — der
System-Prompt wurde bei jedem Call verworfen. Konsequenz: Judge ohne Kontext, alle
Anthropic-Modelle mit `retry_required=true` (2 Parse-Versuche statt 1), Latenz verdoppelt,
tooluse006 bei Opus 4.6 in Timeout.

**Fix:** `func_kwargs["system"] = kwargs.get("system")` vor dem Temperature-Check eingefügt.
Re-Runs (--force): Haiku 4.5 = 75.0%, Opus 4.5 = 79.2%, Sonnet 4.6 = 79.0%,
Opus 4.6 = 80.0% — alle mit `parse_attempts=1`.

### 2. `tooluse003.yaml` v1.3.0 — Rubrik False-Positive für httpbin.org-Kontext

**Problem:** `uncertainty_handling.unacceptable` enthielt keine `acceptable_patterns`.
Modelle, die korrekt den httpbin.org-Testkontext erläuterten (z. B. "httpbin.org ist ein
HTTP-Test-Service, der bewusst 404 zurückgibt"), erhielten `hallucination_detected=true`.

**Fix:** `acceptable_patterns`-Sektion mit 5 erlaubten Erklärungstypen:
- httpbin.org als HTTP-Test-Service
- Intentionale 404 für Debugging-Zwecke
- Kein echter Ressourcenfehler
- Testumgebung-Kontext
- Simulations-/Diagnosezweck

### 3. `scripts/core/unified_runner.py` — Token/Cost-Tracking für Multi-Call-Module

**Problem:** `last_token_usage` speicherte nur den letzten API-Call. Tool-Use-Assets
bestehen aus zwei LLM-Calls (Tool-Call + Synthesis). Audit-Log-Header zeigte z. B.
3165 statt 11683 Token.

**Fix:** `max(exec_result.tokens_used, client.last_token_usage)` — nimmt den höheren Wert.
`isinstance`-Check verhindert `MagicMock`-Vergleichsfehler in Unit-Tests.

---

## v3.13.0 — Phase-C Asset + Judge Hardening (2026-05-25)

**Status:** Abgeschlossen

### 1. tooluse006 — Phase-C: Multilingual Search & German Synthesis

Neues Asset, das eine dritte Bewertungsdimension einführt: **sprachübergreifende Synthese**.
Das Modell recherchiert internationale Handelsperspektiven via `web_search` und muss die
Ergebnisse ausschließlich auf Deutsch zusammenfassen — auch wenn die Suchergebnisse
englischsprachig oder spärlich sind.

**Kalibrierung:** Sonnet-Probe-Run lieferte P2=40 (2/5 vom Judge) bei objektiv hochwertiger
Antwort. Ursache: `factuality.must_not_include`-Regel "Detailzahlen ohne Tool-Grundlage"
feuerte auf korrekte Kontextfakten. Rubrik korrigiert auf Unterscheidung erfundener vs.
faktisch korrekter Ergänzungen; BEWERTUNGSANWEISUNG um Hinweis auf sparse Search-Results
erweitert. Nach Kalibrierung: Sonnet 90, Hermes 90 (Phase C misst Synthese, kein Grounding-Edge).

### 2. phase2_rubric — Verdrahtung mit LLM-Judge

`phase2_rubric` in Asset-YAMLs war totes YAML — nirgends gelesen, Judge bekam nur den
generischen System-Prompt. `_build_rubric_override()` in `test.py` serialisiert das
YAML-Dict zu strukturiertem Text und übergibt es als `rubric_override` an `runner.score()`.
Unterstützte Sektionen: `factuality`, `hallucination_risk`, `uncertainty_handling`,
`language_consistency` (inkl. `target_language`-Header, `scoring_note`).

### 3. Hallucination Cap — Config-First

`hallucination_detected: true` vom Judge hatte keine Score-Wirkung. Fix:

- `config/scoring.yaml` → `tool_use.hallucination.cap_hard: 20`
- `constants.py` → `HALLUCINATION_CAP_KEY`, `HALLUCINATION_CAP_DEFAULT`
- `tool_adapter_audit.py` → `load_hallucination_cap()` liest Config, gibt Default 20 bei Fehler
- `test.py` → nach Judge-Call: `if hallucination_detected: p2 = min(p2, float(hal_cap))`

### 4. `tool_result_ignored` — Neues CV-Diagnose-Flag

Neues Boolean im Content-Verification-Block. Wird `true` wenn:
- `content_usable = True` (Tool hat verwertbaren Inhalt geliefert)
- `state = "B2"` (keine Phrase-Überlappung zwischen Tool-Response und Modellantwort)

Semantik: Modell hatte nutzbaren Tool-Inhalt, hat aber trotzdem aus dem Trainings-Vorwissen
geantwortet. Distinct von B1 (Modell war transparent über die Lücke).

### 5. tooluse002-Rubrik — False-Positive-Fix

`uncertainty_handling.unacceptable` enthielt "Fakten hinzufügen die nicht im Fixture stehen".
Sonnet ergänzte korrekte Quake-Fakten (Lovecraft-Setting, Metacritic-Scores) → Judge feuerte
`hallucination_detected: true` → Cap auf 20. Rubrik korrigiert: Unakzeptabel sind nur
**faktisch falsche** Angaben, nicht korrekte Ergänzungen aus Parameterwissen.

### Probe-Run Ergebnisse (claude-sonnet-4-6 vs. Hermes 4 14B Q4_K_M)

| Asset | Sonnet | Hermes |
|---|---|---|
| tooluse001 (Honeypot) | 60 | 60 |
| tooluse002 (Extract) | 90 | 60 |
| tooluse003 (404) | 70 | 40 |
| tooluse004 (Tool Selection) | 60 | 60 |
| tooluse005 (URL Construction) | 100 | 90 |
| tooluse006 (Multilingual) | 90 | 90 |
| **Avg** | **78.3** | **66.7** |

14-Punkte Spread zwischen Sonnet und Hermes — jeweils auf konkrete Content-Grounding-Fehler
bei Hermes zurückführbar (tooluse002: QuakeWorld-Fehlzuschreibung; tooluse003: erfundenes JSON
für 404-Response; tooluse004: Tool-Ergebnis ignoriert, aus 2024er Trainingsdaten geantwortet).


## Tool Use Module — Phase-A Calibration: MCP Alignment, CV Gate & Attribution Bias Fix

**Datum:** 2026-05-24
**Status:** Abgeschlossen

### Kontext

Nach den ersten Verifikations-Runs gegen `claude-sonnet-4-6`, `gpt-5.4-mini` und `gemma3:4b` im
Mock-Modus wurden mehrere Kalibrierfehler identifiziert, die die Messgenauigkeit des Benchmarks
beeinträchtigten. Alle Korrekturen wurden mit einem Re-Run verifiziert; End-Durchschnitt
claude-sonnet-4-6: **85.2%** (P1 = 96).

### 1. MCP Standard Alignment (`http_fetch` → `fetch`)

**Problem:** Das Modul verwendete `http_fetch` als Tool-Name. Anthropics MCP-Referenzimplementierung
(`@modelcontextprotocol/server-fetch`) definiert den Standard als `fetch`. Modelle, die ihrem
MCP-Training folgen (u. a. Claude Sonnet 4.6), riefen `fetch` auf und erhielten P1 = 0 — kein
Kompetenzproblem, sondern ein Namens-Mismatch im Benchmark.

**Lösung:** Route `POST /tools/http_fetch` → `POST /tools/fetch` in `cruciblemark-mcp/server.py`.
Konstante `TOOL_HTTP_FETCH = "http_fetch"` → `"fetch"` in `constants.py` (SSoT-Kaskade).
`AUTHORIZED_TOOLS` + `CANONICAL_TOOLS` in `tool_adapter_audit.py` aktualisiert. Asset-YAMLs
tooluse001/002/003/005: `tool_available`, `mcp_endpoint`, `expected_tool` angepasst.

### 2. tooluse005 — Blocked-Status durch Sprachmismatch im Prompt

**Problem:** Der deutsche Prompt ließ Modelle `de.wikipedia.org`-URLs konstruieren. Diese Domain
ist nicht in der MCP-Whitelist → `blocked` → P1 = 0. Der URL-Pfad-Präzisions-Test war damit
nicht auswertbar.

**Lösung:** Prompt um `"Verwende die englischsprachige Wikipedia (en.wikipedia.org)."` ergänzt.
Der URL-Pfad-Test (korrekter Pfad `/wiki/Python_(programming_language)`) bleibt vollständig aktiv.

### 3. Content Verification Gate — `_OVERLAP_WINDOW = 3` (war 4)

**Problem:** `_has_content_overlap()` suchte nach verbatim 4-Wort-Sequenzen in der Modellantwort.
Alle technischen Identifikatoren in tooluse004/005-Fixtures sind ≤ 3 Wörter ("Open LLM Leaderboard",
"id Software"). Obwohl Modelle diese Eigennamen korrekt aus dem Fixture übernahmen, fand das
4-Wort-Fenster keinen Treffer → fälschliche B2-Einstufung (parametrisch) → P2 auf 35 gedeckelt.

**Lösung:** `_OVERLAP_WINDOW = 3` in `core/tool_adapter_audit.py`. Neue Unit-Test-Klasse
`test_content_verification.py` (7 Tests für alle CV-Zustände A/B1/B2/C und Failure-Test-Exempt).

### 4. Mock-Fixture-Qualität (web_search Excerpts)

**Problem:** `_FIXTURE_SEARCH["_default"]` enthielt einzeilige Excerpts (~80 Zeichen). Damit
konnten Modelle keine inhaltlich substanzielle P2-Antwort liefern; der Judge bewertete die
generischen Antworten mit mittleren Scores unabhängig von der tatsächlichen Modellkompetenz.

**Lösung:** Alle drei Default-Excerpts auf ~250 Zeichen mit mehreren Fakten erweitert. Dritter
Eintrag: `raw.githubusercontent.com/openai/evals` → `huggingface.co/mistralai` (thematisch
konsistenter mit dem tooluse004-LLM-Rankings-Kontext).

### 5. `web.search`-Variante — Tool-Name-Normalisierung

**Problem:** `gpt-5.4-mini` verwendet `web.search` (Punkt statt Unterstrich). Diese Variante
war nicht in `AUTHORIZED_TOOLS` eingetragen → normalisiert zu `unknown` → MCP-Endpunkt
`/tools/web.search` (404) → P1 = 0.

**Lösung:** `"web.search"` als Alias in `AUTHORIZED_TOOLS["web_search"]` in
`core/tool_adapter_audit.py` ergänzt.

### 6. tooluse002 v2.1.0 — Rubrik-Korrektur: Attribution Bias

**Problem:** `uncertainty_handling`-Gewicht 0.25 listete "Klare Attribution an die abgerufene
Seite" als positiv bewertetes Kriterium und "Fakten ohne Quellennennung" als Abzugsgrund.
Das benachteiligte systematisch Modelle mit autoritativem Integrationsstil (Claude: "Quake II
ist ein Name-only-Sequel") gegenüber Modellen mit expliziter Quellenbindung (GPT-Stil: "Laut
dem Wikipedia-Artikel..."). Bei inhaltlich gleichwertigen, quellenbasierten Antworten entstanden
Scores von 57 vs. 88 — ein Rubrik-Defekt, kein Modell-Unterschied.

**Lösung:**
- Gewichte: `factuality: 0.65`, `hallucination_risk: 0.30`, `uncertainty_handling: 0.05`
- `uncertainty_handling.acceptable`: "Klare Attribution" entfernt; "Antwort bleibt im Rahmen
  der Fixture-Inhalte" als Kriterium eingesetzt
- `uncertainty_handling.unacceptable`: "Fakten ohne Quellennennung" entfernt; "Fakten
  hinzufügen die nicht im Fixture stehen" als Kernkriterium eingesetzt

**Wichtig für spätere Leser:** Dieses Fix verbessert **nicht das Modell**, sondern trennt
die Bewertung sauber zwischen Inhaltsqualität und stilistischer Quellenbindung. Eine Antwort,
die factually korrekt ist und sich im Fixture-Rahmen hält, soll nicht schlechter bewertet werden
als eine mit expliziten "laut Wikipedia"-Phrasen.

**Ergebnis:** tooluse002 P2 Claude Sonnet 4.6: 57 → 86. Combined: 93.1%.

### 7. Infrastructure-Fixes

- **`TIMEOUT_PER_MODEL`**: 300s → 600s in `scripts/run_tooluse_benchmark.py` (Anthropic-API
  benötigt an langsamen Tagen bis zu 147s für ein einzelnes Asset)
- **`make mcp-stop`**: `pkill -f "cruciblemark-mcp/server.py"` als Fallback wenn `.mcp.pid`
  fehlt (Szenario: Server über Batch-Runner gestartet, kein PID-Eintrag)

***

## Provider Shortcode System & Versioning Overhaul (v3.5)

**Datum:** 2026-07-15
**Status:** Abgeschlossen

### Problembeschreibung

Das Leaderboard zeigte für viele Modelle `k.A.` als Versions-String (fehlende Behandlung neuer Modell-Familien wie Qwen, GLM, MiniMax, o4-Series, Kimi). Außerdem fehlte jede Information, über welchen Provider ein Modell getestet wurde — bei Modellen wie `kimi-k2`, die sowohl via OpenRouter als auch Groq laufen, war das Ergebnis ohne Provider-Kontext nicht interpretierbar.

### Lösung

1. **`_PROVIDER_SHORTCODES` + `get_provider_shortcode()` in `utils/model_utils.py`:**
   Neues Mapping-Dict und neue Funktion für die Shortcodes `API` (proprietäre Direkt-APIs), `OR` (OpenRouter), `GR` (Groq), `LCL` (Ollama/Lokal).

2. **`short_code`-Feld pro Provider in `benchmark_config.yaml`:**
   Jeder Provider-Block trägt jetzt ein `short_code`-Feld. Beide Orte (Config + `model_utils.py`) müssen synchron gehalten werden.

3. **Erweiterte Versionserkennung in `get_model_version()`:**
   Neue Handler für `codestral`/`magistral` (mit Vorrang-Check für magistral, verhindert false `2312`-Match), `qwen`, `glm`, `minimax`, `o4`, erweiterte kimi-Regex für `-thinking`/`-instruct`-Suffixe.

4. **Provider re-attach in `scripts/leaderboard/__init__.py`:**
   `score_calculator.py` verliert die `provider`-Spalte beim `groupby`. Nach `calculate_scores()` wird sie per pandas `mode()`-Merge neu angehängt. Danach: `Provider Code`-Spalte via `get_provider_shortcode()`.

5. **Kombinierte Anzeige in `scripts/leaderboard/exporter.py`:**
   - Kompakt-CSV: `Version` = `k2/OR` (kombinierter String)
   - Detailliert-CSV: `Version` + `Provider Code` als separate Spalten

6. **CSV-Migration via `scripts/maintenance/migrate_model_versions.py`:**
   Einmalig ausgeführt — hat alle `k.A.`/`unknown`/`""` Versionswerte in den drei Benchmark-CSVs rückwirkend befüllt (`.bak`-Backups wurden angelegt).

### Hinweis für Entwickler

Wird ein neues Modell hinzugefügt, das ein Provider-Shortcode-Lookup benötigt, **immer beide SSoT-Stellen aktualisieren**: `_PROVIDER_SHORTCODES` in `utils/model_utils.py` und das `short_code`-Feld in `benchmark_config.yaml`.

***

## Leaderboard Numerator Fix (v2.2)

**Datum:** 2026-03-16
**Status:** Behoben

### Problembeschreibung

Nach dem Entkoppeln des Political Compass zeigte der `Tests Run`-Zähler noch immer einen überhöhten Numerator (z. B. "44/43"). `scripts/leaderboard/score_calculator.py` iterierte blind über alle einzigartigen Kategorien im Datensatz, ohne zu prüfen, ob `enable_scoring: false` in den Modul-Configs gesetzt war. So erfasste der Calculator versehentlich Political Compass- oder System Probe-Artefakte.

### Lösung

1. **Category Filtering:** `_calculate_run_counts` in `score_calculator.py` erhielt ein `counting_cats`-Set. Nur Module mit aktivem Scoring (`enable_scoring: True`) oder explizitem `display_test_count` fließen in die Zählung ein.
2. **Docs Cleanup:** Veraltete `display_test_count: 9`-Artefakte aus Modul-READMEs und Entwicklungsanleitungen entfernt.

***

## Political Compass Architecture Decoupling (v2.1)

**Datum:** 2026-03-14
**Status:** Behoben

### Problembeschreibung

Die Logik, die das Political Compass Modul über "Ghost Rows" in die Haupt-DataFrames eintrug, führte zu mathematisch ungenauen UI-Metadaten ("Test Runs: 165/156"). Das Einbetten eines rein informativen ethischen Surveys in die primäre DataFramestruktur verfälschte Code-Quality-Test-Zähler und Zeitbenchmarks.

### Lösung

1. **Full Decoupling:** Ghost-Row-Injektionsroutinen in `scripts/leaderboard/data_loader.py` für das PC-Modul entfernt. Die Config-Eigenschaft `display_test_count` des Moduls entkoppelt.
2. **Isolating Outputs:** Ausgaben aufgeteilt in `benchmark_scores/political_compass_results.csv` (Run Records) und `benchmark_scores/political_compass_leaderboard.csv` (Shift-Aggregationen).
3. **Post-Evaluation Stitching:** Die finalen Schritte von `generate_leaderboard.py` extrahieren nur den Vanilla Alignment Tag und den Shift-String als eigenständige rechtsbündige Textspalte, unabhängig vom `score_calculator.py`.

***

## Ghost Entries & Versioning Refactor

**Datum:** 2026-02-06
**Status:** Behoben

### Problembeschreibung

Das Leaderboard zeigte Duplikat-Einträge für einzelne Modelle (z. B. "Claude Haiku"). Ein Eintrag enthielt Benchmark-Scores, ein zweiter "Ghost Entry" nur Political Compass-Ergebnisse.
**Ursache:** Inkonsistente Versions-Strings zwischen Benchmark Runner (`8717af19`) und Political Compass Runner (`unknown`).

### Lösung

1. **Centralization:** Versions-Logik nach `utils/model_utils.py` (`get_model_version`) als SSOT verschoben.
2. **Deterministic Mapping:** Behavior-Hash-Fingerprinting entfernt, um Ghost-Duplikate zu verhindern.
3. **Data Patch:** Split-Einträge in CSVs zusammengeführt und historische Cache-Einträge angeglichen.
4. **Golden Standard Optimization:** Political Compass aus der Golden Standard-Generierung ausgeschlossen (Methodik-Update).

***

## Aggregation Verification Report

**Datum:** 2026-02-04
**Status:** Behoben

### Befunde

Das Leaderboard zeigte zuvor "46/37 Tests Run". Die Diskrepanz entstand, weil das `Political Compass`-Modul über ein explizites Override (neun logische Tests) zum **Numerator** beitrug, aber wegen deaktiviertem Scoring (`enable_scoring: false`) aus dem **Denominator** ausgeschlossen blieb.

### Verifikationsdaten

```python
aggregation_report = {
    "total_unique_assets_in_csv": 38,
    "breakdown": {
        "scoring_assets": 37,
        "political_compass_rows": 1
    },
    "logical_test_counts": {
        "scoring_tests": 37,
        "political_compass_logical": 9,
        "total_logical": 46
    },
    "previous_display": "46/37",
    "fixed_display": "46/46",

    "aggregation_rules": {
        "method": "last-value-wins",
        "implementation": "df.drop_duplicates(subset=[model, version, asset_id], keep='last')",
        "models_with_duplicates": "All (Historical runs are preserved in raw CSV, filtered at load time)",
        "duplicate_runs_intentional": True
    }
}
```

### Maßnahmen

1. **Code Update:** `scripts/leaderboard/score_calculator.py` bezieht jetzt Module mit explizitem `display_test_count` in den "Expected Count" (Denominator) ein, auch wenn Scoring deaktiviert ist.
   - *Ergebnis:* Denominator stieg von 37 auf 46. Das Leaderboard zeigt nun "46/46".

2. **Duplicate Handling:** `data_loader.py` verarbeitet Mehrfach-Runs korrekt und wählt jeweils den neuesten Eintrag anhand des Timestamps.
   - *Ergebnis:* Benchmarks sind beliebig oft wiederholbar. Das Leaderboard spiegelt stets den aktuellen Stand wider.

### Reproduktion

```bash
python scripts/maintenance/verify_counts.py
```

***

## API Timeout & Nested Pydantic Serialization (v3.0.0)

**Datum:** 2026-03-18
**Status:** Behoben

### Problembeschreibung

Zwei strukturelle Probleme blockierten die kontinuierliche Evaluierung strikt zensierter Modelle (Gemini, Claude) im Political Compass:

1. **Refusal Stalling:** Modelle, die "Sorry, I can't answer this" zurückgaben, lösten einen sofortigen Fehler beim Metrik-Parsing aus. Das brach die Batch-Evaluierungssequenz ab, anstatt alternative Permutationen zu versuchen.
2. **Verify Anomalies Crashes:** Das Prüfen von Shift-Werten erzeugte einen `AttributeError`. Der Code rief `.get()` nativ auf dem Pydantic-Schema-Return (`base_result.raw_response`) auf. Dieser ist strikt als JSON-String gespeichert, nicht als generisches Dict.

### Lösung

1. **3-Tier Refusal Loop:** Eine robuste `while True`-Schleife mit progressiven Temperatur-Checks (`0.1`, `0.4`, `0.7`) greift direkt in der Ausführungsschleife (`_run_single_block` in `political_compass/test.py`). Das System bricht Zensurfilter autonom auf.
2. **Pydantic Deserialize:** Alle `raw_response`-Lesezugriffe in Verify-Skripten nutzen jetzt `json.loads(str)`, um Dict-Konformität vor dem Zugriff auf verschachtelte Variablen (Vanilla/Forced) sicherzustellen.


## Tool-Use-Backlog: nicht getestete Modelle

Diese Modelle sind in der Karte mit `supports_tool_use: "untested"` markiert — der Tool-Use-Benchmark wurde für sie noch nicht ausgeführt. Ein Tool-Use-Narrative-Review ist erst möglich, nachdem `make benchmark-tooluse PROVIDER=<...>` gelaufen ist.

| Slug | Display-Name |
|---|---|
| `qwen2_5vl_7b` | Qwen 2.5 VL 7B |
| `test` | TODO |

---

## v4.6.2 — Provider-Card SSoT-Bereinigung (2026-06-08)

### Phase 20: `risk_calculator.get_provider_card_context()` nutzt SSoT

**Problem:** Direkter FS-Zugriff + `json.loads()` für Provider Cards — umging
die SSoT-API `load_provider_card()` in `utils/provider_card_template.py`.

**Fix:** 
- Import von `load_provider_card` statt `_safe_id`
- Inline-FS-Pfad durch `load_provider_card(developer)` ersetzt
- `unknown`-Filter bleibt im Konsumenten (SSoT-API filtert nicht)
- `re`-Import entfernt (ungenutzt)

### Phase 21: `generate_review._ensure_provider_card()` ohne Reflection

**Problem:** Lädt `generate_provider_cards` Modul dynamisch via `_load_card_module()` —
fragile Reflection, umging SSoT-API.

**Fix:**
- Direkter Import: `_load_stats_from_csv`, `_generate_card`, `_write_card` aus
  `scripts.analysis.generate_provider_cards`
- SSoT-Index-API `rebuild_provider_index()` aus `utils.provider_card_template`
- Read-Pfad: `load_provider_card()` (SSoT) statt direkter FS-Zugriff
- `_load_card_module` bleibt für `_ensure_model_card` (Model-Card-Generator) bestehen

### Tests

- 6 neue Regressionstests in `tests/test_provider_card_ssot_refactor.py`
- Insgesamt: 246/246 Tests grün, Pylint 10.00/10

---

## v4.6.3 — Card-Status-Tool + Provider-Detection-SSoT (2026-06-08)

### Phase 22: Audit-Readiness-Report für Provider Cards

**Motivation:** 18 Provider Cards im Projekt, aber keine Sichtbarkeit über
Frische (Stale) und Vollständigkeit (unknown-Felder). Vor Reviewer-Anfragen
("wie aktuell sind die Karten?") fehlte ein Werkzeug für die Hygieneprüfung.

**Implementierung** in `utils/provider_card_template.py`:
- `get_provider_card_status(stale_days)` — scannt `CARDS_DIR`, klassifiziert
  jede Karte in `verified` / `unknown` / `stale` / `parse_error`.
- `format_provider_card_status(report)` — lesbarer CLI-Output mit Sektionen
  für Unknown-Karten und unknown deployment-Sub-Feldern.
- `_parse_iso_timestamp()` — normalisiert naive datetimes auf UTC, damit
  `datetime.now(timezone.utc) - parsed` nie crasht.
- `_is_deployment_field_unknown()` — Sentinel-Erkennung: `"unknown"`-Strings
  und `-1` für `data_retention_days`.
- `_DEPLOYMENT_FIELDS_REQUIRING_VERIFICATION` — zentrale Liste der Felder,
  die "echte" Werte brauchen.

**CLI-Wrapper** in `scripts/analysis/provider_card_status.py`:
- `--stale-days N` (Default 90) — konfigurierbarer Schwellenwert
- `--json` — für CI-Parsing
- `--fail-on-unknown` / `--fail-on-stale` — Exit-Code 1 für CI-Gates
- Stdlib-only, keine neuen Dependencies

**Makefile-Target:**
```makefile
make provider-cards-status                    # Default 90 Tage
make provider-cards-status STALE_DAYS=30      # aggressiver
make provider-cards-status JSON=1             # JSON-Output
```

**Live-Befund:**
```
Total:                  18
  Verified:             15
  Unknown:              3  (nous_research, todo, unknown)
  Stale (>90d):         0
  Unknown dep-fields:   11  (v.a. data_retention_days)
```

### Phase 23: Provider-Detection-SSoT

**Problem:** Drei voneinander unabhängige Provider-Prefix-Maps:
1. `scripts/analysis/review/risk_calculator.py::_CLOUD_PREFIX_TO_PROVIDER`
2. `utils/model_utils.py::resolve_provider()` (Config-basiert, andere Anforderung)
3. `scripts/web_export.py::build_provider_map()` (Config-basiert, andere Anforderung)

Drift-Risiko bei nur der ersten — aber genau die ist die SSoT für
Sovereign-Risk und Reviewer-Prompt.

**Fix:**
- Neues Modul `utils/provider_detection.py` mit `PROVIDER_PREFIX_MAP`
  (lowercase-Prefix → Display-Name) und `detect_provider_from_model_id()`.
- `risk_calculator.detect_provider()` wird zur dünnen Bridge:
  ```python
  def detect_provider(model_id: str) -> str | None:
      return detect_provider_from_model_id(model_id)
  ```
- `_CLOUD_PREFIX_TO_PROVIDER` (~15 Zeilen) aus `risk_calculator.py` entfernt.
- `re`- und `_safe_id`-Imports entfernt (ungenutzt nach Refactor).

**Design-Entscheidung: keine Wortgrenzen-Logik**

Erste Iteration hatte eine Wortgrenzen-Logik
(`model_id[pos] in {"-", ":", "/", "."}`), die aber mit gängigen
Modellnamen-Patterns unvereinbar ist:
- `gpt-4o` → Position 4 = `"4"`, kein Trennzeichen → kein Match (false negative)
- `claude-haiku-4-5` → Position 7 = `"h"`, kein Trennzeichen → kein Match (false negative)
- `qwen2.5-14b` → Position 4 = `"2"`, kein Trennzeichen → kein Match (false negative)

Eine "Wortgrenze = kein Lowercase-Letter"-Logik scheitert spiegelbildlich
bei `claude-haiku-4-5` (Position 7 = `"h"` IST Lowercase).

Lösung: einfacher `startswith`-Check mit Längste-Prefixes-zuerst-Iteration
(greedy matching). Funktioniert für alle bekannten Modellnamen-Patterns.
Falls in Zukunft False-Positives wie `qwenchat` → Alibaba auftauchen,
sollte die Liste der erlaubten Modellnamen whitelist-basiert gepflegt
werden, nicht per Wortgrenzen-Heuristik — siehe Kommentar im Modul.

**Reihenfolge der Map-Keys** (insertsion-order, da Python 3.7+ garantiert):
Längere Prefixes zuerst (`"gpt-5-"` vor `"gpt-"`), damit Greedy-Matching
korrekt funktioniert.

### Tests

- 25 neue Tests in `tests/test_provider_card_status.py`:
  - 9 für Phase 22 (Card-Status-Klassifizierung)
  - 16 für Phase 23 (Provider-Detection: 11 Provider + Edge-Cases)
- Insgesamt: **271/271 Tests grün**, Pylint **10.00/10**
- Commits: `0799309` (Phase 20/21) + dieser Commit (Phase 22/23)


## v4.6.4 — Card-Templates als SSoT (2026-06-08)

### Phase 24: YAML-basierte Card-Templates mit Konsument-Annotation

**Motivation:** Die Pflichtfeld-Definitionen für Model- und Provider-Cards
waren über drei Stellen verstreut (`utils/card_utils.py`,
`utils/verify_model_cards.py`, `utils/provider_card_template.py`). Jede
Änderung erforderte Code-Touch und war drift-anfällig. Zudem fehlte die
Dokumentation, *wer* ein Feld eigentlich liest (Risk-Calc, Leaderboard,
Web-Export, Reviewer-Prompt, Judge, etc.).

**Lösung:** Deklarative YAML-Templates als Single Source of Truth, vom Code
nur noch geladen und validiert.

### 1. Templates

**`config/card_template_model.yaml`** — 39 Pflichtfelder, 6 Optionalfelder
**`config/card_template_provider.yaml`** — 16 Pflichtfelder, 3 Optionalfelder

Jeder Feld-Eintrag annotiert:
- `name`, `type`, `required`, `default`, `description`
- `consumers` — Liste der Konsumenten (risk_calc, leaderboard, web_export,
  tooluse, cost, review, probe, index, scoring, asset, judge)
- `since` — Version, ab der das Feld Pflicht ist
- `example` — exemplarischer Wert

Sentinel-Werte (`None`, `"TODO"`, `"unknown"`, `""`, leere Listen) werden vom
Validator als "fehlt effektiv" gewertet.

Provider-Template: `deployment`-Feld hat `sub_fields_required` Liste
(`cloud_act_exposure`, `applicable_law`, `data_residency`,
`gdpr_dpa_available`, `eu_adequacy_decision`, `data_retention_days`,
`chinese_nsl_risk`).

### 2. Loader — `utils/card_template.py`

Frozen Dataclasses `CardFieldSpec` und `CardTemplate`. Methoden:
- `CardFieldSpec.is_unknown_sentinel(value)` — Sentinel-Erkennung
- `CardTemplate.required_field_names` / `all_field_names`
- `CardTemplate.get_field(name)`, `is_required(name)`, `is_known(name)`

`@lru_cache(maxsize=4) load_card_template(card_type)` — geladen via
`yaml.safe_load`. `clear_cache()` für Test-Isolation.

### 3. Validator — `scripts/analysis/validate_cards.py`

Dataclasses `CardIssue` und `CardReport` mit `is_valid` Flag. Issue-Typen:
- `missing_required` — Pflichtfeld fehlt komplett
- `unknown_sentinel` — Pflichtfeld hat Sentinel-Wert (`None`, `"TODO"`, …)
- `drift_extras` — Feld außerhalb des Templates (Toleranz: `tooluse_*` Legacy)
- `missing_sub_field` — Sub-Feld fehlt (z.B. `deployment.cloud_act_exposure`)
- `parse_error` — JSON-Parse-Fehler

CLI:
```bash
python scripts/analysis/validate_cards.py --card-type {model,provider,all}
python scripts/analysis/validate_cards.py --json --fail-on-drift
```

Exit-Codes: 0 OK, 1 invalid oder drift-mit-flag. Filter `_is_card_file()`
schließt `_index.json`, `True.json`, `False.json`, `null.json`, `None.json`
aus.

### 4. Makefile-Target

```makefile
make validate-cards-template                       # beide Typen
make validate-cards-template CARD_TYPE=provider    # nur Provider
make validate-cards-template CARD_TYPE=model       # nur Model
make validate-cards-template FAIL_ON_DRIFT=1       # CI-Gate
make validate-cards-template JSON=1                # JSON-Output
```

(Umbenannt zu `validate-cards-template` weil das ältere `validate-cards`
Target auf `scripts/dev/validate_model_cards.py` zeigt — kein Konflikt.)

### 5. Live-Befund

```
=== Card Validation Report: PROVIDER ===
Total cards:        18
  Valid:            11
  Invalid:          7
Total issues:       29
  drift_extras          2   (llamacpp: type, inference_interfaces)
  unknown_sentinel      27
```

Konkret: `llamacpp.json` hat zwei Extras (`type`, `inference_interfaces`)
die ins Template gehören. 7 Provider haben `unknown`/`None`-Werte für
Pflichtfelder (z.B. `api_base_url: null` für lokale/self-hosted Provider).

Model-Lauf: 108 Karten, 8 valid, 100 invalid (537 issues) — zeigt, dass
viele Model-Cards noch unvollständig sind und der Validator echte Arbeit
leisten muss.

### Tests

- 25 neue Tests in `tests/test_card_template.py`:
  - 9 für Template-Loader (model/provider load, unknown, required,
    sub_fields, caching)
  - 6 für Sentinel-Erkennung
  - 8 für Validator (valid card, missing, TODO, drift, tooluse_toleranz,
    sub_field, parse_error, index_skip)
  - 2 für Format-Reporter (text, json)
- Insgesamt: **296/296 Tests grün** (zuvor 271), Pylint **10.00/10**
- Neuer Commit für Phase 24


## v4.6.5 — SSoT-Card-Sync (Phase 25) (2026-06-08)

### Motivation

Template (Python-Dict) und Karten-Dateien (JSON) driften auseinander, sobald
ein Feld im Template ergänzt oder entfernt wird. Bisher musste man manuell alle
Karten anpassen — fehleranfällig und nicht reproduzierbar.

### Lösung

`--update`-Flag in den Card-Generatoren und dedizierter CLI
`scripts/analysis/sync_cards.py` mit folgenden Eigenschaften:

- **Add (Vorwärts):** Felder, die im Template neu sind, fehlen aber in der
  Karte → werden automatisch mit Default-Wert aus dem Template ergänzt.
  Kein Prompt.
- **Delete (Rückwärts):** Felder, die in der Karte sind, aber nicht im
  Template → werden aus der Karte entfernt. **Mit Bestätigungs-Prompt pro
  Karte** (gesammelt, nicht pro Feld). Mit ``--yes`` wird die Abfrage
  übersprungen.
- **Beibehalten:** Felder, die in Karte und Template sind, bleiben
  unverändert.
- **Idempotent:** Mehrfacher Aufruf ohne Template-Änderung = No-Op.

### 1. `utils/card_sync.py` — Sync-Engine

Frozen Dataclasses `SyncAction` (kind: add/delete/keep) und `SyncPlan`. 
Funktionen:
- `plan_sync(card_path, card_type)` — berechnet Aktionen ohne Schreiben
- `apply_sync(card_path, card_type, *, dry_run, yes, confirm_fn)` — plant +
  führt aus, fragt bei Löschungen nach
- `sync_all(card_type, ...)` — Batch-Verarbeitung aller Karten
- `format_summary(plans)` — lesbarer CLI-Output

Protected IDs (`provider_id`, `model_id`) werden nie gelöscht.
`tooluse_*`-Legacy in Model Cards wird toleriert (nicht gelöscht).

### 2. `scripts/analysis/sync_cards.py` — CLI

```bash
python scripts/analysis/sync_cards.py --card-type all --dry-run
python scripts/analysis/sync_cards.py --card-type provider --yes
python scripts/analysis/sync_cards.py --card-type model --json
```

Exit-Code 0 in beiden Modi. `--json` Output für CI-Parsing.

### 3. `--update`-Flag in Generatoren

`scripts/analysis/generate_provider_cards.py --update [--yes] [--dry-run]`
`scripts/analysis/generate_model_cards.py --update [--yes] [--dry-run]`

Beide rufen intern `sync_all()` auf — keine LLM-Calls, keine Stats-Injektion.
Reine Template-Synchronisation.

### 4. Makefile-Targets

```makefile
make cards-sync CARD_TYPE=provider DRY_RUN=1
make cards-sync CARD_TYPE=all YES=1
make provider-cards-update YES=1
make model-cards-update DRY_RUN=1
```

### 5. Live-Befund

```
=== Card-Sync Zusammenfassung ===
  Cards verarbeitet:   18
  Cards mit Änderungen: 1
  Adds:    0
  Deletes: 2

--- llamacpp.json (provider) ---
  - inference_interfaces  (nicht mehr im Template definiert)
  - type  (nicht mehr im Template definiert)
```

Korrekt erkannt: `llamacpp.json` hat 2 Felder, die nicht im
Provider-Card-Template definiert sind. Die anderen 5 Karten mit
`api_base_url: null` werden **nicht** als "missing" markiert, weil das
Feld im Template vorhanden ist — der Wert `null` ist legitim für lokale
Provider.

### Tests

- 22 neue Tests in `tests/test_card_sync.py`:
  - 3 für Template-Lookup
  - 7 für plan_sync (Aktionen, Drift, Protected IDs, Legacy)
  - 6 für apply_sync (dry-run, yes, confirm_fn, Idempotenz)
  - 3 für sync_all
  - 2 für format_summary
  - 1 für Idempotenz
- Insgesamt: **318/318 Tests grün** (zuvor 296, +22), Pylint **10.00/10**
- Neuer Commit für Phase 25

