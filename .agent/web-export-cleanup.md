# Web Export & Cleanup

Web-Export-Subsystem, Cleanup-Workflows, ID-Migration.

## WebExport None-Stripping

`strip_none()` in `utils/text_helpers.py` entfernt `None`-Werte rekursiv aus allen exportierten Dicts. Neue Felder zum Export hinzufügen: `card.get("feld")` reicht — `None` wird automatisch entfernt.

Test `test_web_export_card_field_coverage.py` prüft Required-Felder gegen Sample-Card — wenn ein Required-Feld `None` sein kann, muss es in der Sample-Card einen Wert haben.

## WebExport Vendor-Dedup Defense-in-Depth (ab v4.10.11)

`_collect_vendor_cards()` in `scripts/web_export/filters.py` filtert **immer** Placeholder-Karten (`unknown=true` ODER `vendor_id in _PLACEHOLDER_VENDOR_IDS = {"todo", "unknown"}`). Community-Karten gehen über `exclude_community=True` ausschließlich in `community_cards.json`.

Symptom bei Bruch: Wenn `vendor_cards.json` Placeholder oder Community enthält, ist die SSoT-Filter-Pipeline gebrochen — entweder Caller nutzt `exclude_community=False` falsch, oder neue Card-Generierung umgeht die Validierung.

Workflow beim Anlegen neuer Vendor-Cards:
1. `vendor_id` MUSS kanonisch sein (siehe `classification_taxonomy.json → manufacturers.values[*].vendor_card_id`).
2. Fine-Tune/Quant-Varianten MÜSSEN `card_subtype: "community"` haben.
3. Niemals `vendor_id: "todo"` oder `"unknown"` als Platzhalter — das löst Filter aus und Card verschwindet still.

## WebExport Vendor-Card-Drift (ab v4.10.11)

Wenn die Taxonomie (`classification_taxonomy.json → manufacturers.values[*].vendor_card_id`) auf IDs verweist, die nicht als Vendor-Card-Datei in `benchmark_scores/vendor_cards/` existieren, zeigen die `vendor_card_ref`-Felder in `data.json` ins Leere. Symptom: Modell-Templates haben keinen Vendor-Namen/Vendor-Beschreibung (z.B. 13 Qwen-Modelle nach Cleanup von `alibaba_cloud.json`).

**Defense-in-Depth (Python):** `_init_export_context()` sammelt `existing_vendor_card_ids` einmalig und loggt WARN wenn Taxonomie-IDs fehlen; `_process_leaderboard()` loggt pro Modell WARN bei `vendor_card_ref`-Drift.

**Web-Loader-Fix (out of scope Python-Repo):** bidirektionale Alias-Map in `vendorCards.11tydata.js` — `aliasToCanonical` muss in beide Richtungen aufgelöst werden.

## WebExport Provider-Cards Schema (ab v4.10.11)

Der Python-Export schreibt seit v4.10.11 zwei separate Files:

- `vendor_cards.json` — vollständige Vendor-Cards mit allen Feldern, inkl. Stats/Profile-Metadaten.
- `provider_cards.json` — gefiltertes Sub-Set für Web-Display.

Provider-Schema (display-relevant): `vendor_id, display_name, company, headquarters, founding_year, description, deployment (Dict mit GDPR/Cloud-Act/Sovereign-Risk-Metadaten), pricing_model, api_base_url, api_documentation_url, notable_models, profile_verified, last_verified_at`.

KEIN Export: `stats, profile_verified_by, profile_verified_at, generated_at, last_modified_at, verification_source, unknown` — interne Profile-Metadaten.

Web-Loader: `CrucibleMark-Web/src/_data/providerCards.11tydata.js` liest `provider_cards.json`, filtert Placeholder (`todo`/`unknown`) und `unknown=true`, mergt `provider_stats.json`. `.eleventy.js` registriert `providerCards` UND `vendorCards` als Global-Data + passthrough zu `_site/data/`.

## WebExport Blacklist-ID-Normalisierung (ab v4.10.11)

Die Blacklist (`config/web_export_blacklist.yaml`) enthält Einträge in der kanonischen Underscore-Form (`deepseek_deepseek-chat-v3_1`), während `raw_model_id` aus dem Leaderboard Provider-Prefix und Punkte enthält (`deepseek/deepseek-chat-v3.1`).

**Symptom:** 12/34 Blacklist-Einträge (~35%) matchten NICHT und Modelle wurden trotz Blacklist-Eintrag exportiert (z.B. DeepSeek V3.1 wurde 4 Tool-Use-Monate lang ungewollt im Web-Export angezeigt).

**Fix:** `_is_blacklist()` in `scripts/web_export/filters.py` normalisiert BEIDE Seiten via `_safe_name()` und prüft Wildcard-Patterns in beiden Formen (roh + normalisiert). Tests in `tests/test_web_export_blacklist_normalization.py` (11 Tests).

**Caveat:** 100% Effektivität nicht erreichbar, weil einige Blacklist-Einträge Tippfehler enthalten (`gpt-5_5-pro-2026-04-23` statt `gpt-5_5-2026-04-23`) oder auf nicht-existierende Modelle zeigen.

## WebExport Blacklist-Restructure (ab v4.10.16)

`config/web_export_blacklist.yaml` hat ein Zwei-Sektion-Layout:

- **`blacklist:`** — 24 aktive Einträge, vom Loader gelesen via `data.get("blacklist", [])`.
- **`kept_overrides:`** — 22 dokumentierte Modelle in 5 Gruppen (NVFP4/Wordsmith, Uncensored/Abliterated, Cross-Provider-Reference, Best-Quant-Wins, Thinking-Variant). Jeder Eintrag hat `rank`, `score`, `size`, `mode`, `reason` — dokumentiert WARUM ein Modell trotz Filter-Logik (gleiche Param-Size, stärkere Quant) behalten wurde.

`kept_overrides` ist reine Audit-Dokumentation — der Loader ignoriert zusätzliche Top-Level-Keys. Eliminiert das alte `# -`-Kommentar-Konvention für dokumentierte Ausnahmen (war unstrukturiert und fehleranfällig).

**Filter-Logik (im Kopf des Nutzers, NICHT im Code):** Für jede Param-Size-Klasse wird die stärkste Quant behalten. Ausnahmen: Thinking/Non-Thinking-Varianten beide behalten; Uncensored/Abliterated/Wordsmith-Finetunes behalten; Cross-Provider-Referenz (z.B. `google/gemma-4-31b-it` API neben vLLM-lokal) behalten.

## WebExport Slug-SSoT (ab v4.10.16)

Slug-Generierung in `_process_leaderboard` nutzt `slugify(raw_model_id)` statt `slugify(model_name)`.

**Warum:** `model_id` ist die stabile Identität (eindeutig pro CSV-Zeile), `model_name` ist ein veränderlicher Display-Wert. Hybrid-Paare (Thinking/Standard) haben denselben Display-Namen aber unterschiedliche model_ids — z.B. `gemma-4-31b` (Standard) vs `gemma-4-31b-thinking` (Thinking). Mit `model_name`-Slugs kollidierten beide → `data.json`-Überschreibung (last-row-wins). Mit `model_id`-Slugs sind beide eindeutig.

**Kollision-Safety-Net:** Wenn identische `model_id`s auftreten (sollte bei korrekter CSV nicht vorkommen), greift Provider-Suffix-Disambiguierung (`_seen_slugs`-Set, Provider-Code-Suffix, dann Counter). Defense-in-Depth, kein Normalfall.

**Web-Projekt-Konsequenz:** `slug` = `model_id` (Routing/Identität), `model_name`/`display_name` = Display nur. Web-Projekt kann `?? model_name` Fallbacks in Chart-Handlern entfernen — Slug ist jetzt stabil.

## WebExport `normalize_pending` Sentinel-Hardening (ab v4.10.16)

`normalize_pending()` nutzt `_PENDING_SENTINELS` frozenset statt hardcoded Tuple. Bekannte CSV-Platzhalter-Strings werden zu `None`:

`Pending`, `—` (Em-Dash U+2014), `–` (En-Dash U+2013, separater Codepoint!), `""`, `n/a`, `N/A`, `NA`, `null`, `None`, `none`, `nan`

**Wichtig:** En-Dash (`–` U+2013) und Em-Dash (`—` U+2014) sind verschiedene Unicode-Codepoints. Der alte Code kannte nur Em-Dash — En-Dash leckte als String in den JSON-Export. Beide müssen separat in der Sentinel-Set stehen.

Rückgabewert: `float | str | None`. Zahlen → `float`. Sentinels → `None`. Andere Strings → durchgereicht (CSV-Datenproblem, nicht stillschweigend schlucken).

## WebExport `leaderboard.json` Scores-Contract (ab v4.10.16)

`_write_top_level_outputs()` erzwingt den 9-Key Scores-Contract für `leaderboard.json` direkt vor dem Write (zuvor nur `data.json` hatte Contract-Enforcement).

**Problem:** `strip_none()` entfernte null-Werte aus Model-Einträgen. `leaderboard.json` zeigte dann 7-9 Score-Keys statt 10. `data.json` hatte bereits seit Session-49-Folge Contract-Enforcement via `_SCORES_CONTRACT_KEYS` Re-Injection nach `strip_none`.

**Fix:** In `_write_top_level_outputs`: für jedes Modell in `models_list` — `scores.setdefault(key, None)` für alle `_SCORES_CONTRACT_KEYS` bei bestehender Dict; `dict.fromkeys(_SCORES_CONTRACT_KEYS, None)` bei fehlender Dict.

**SSoT:** `_SCORES_CONTRACT_KEYS` (abgeleitet aus `_SCORE_COLUMN_TO_KEY`) ist die einzige Quelle für die 9 Modul-Keys. Beide Write-Pfade (`data.json` via `_process_leaderboard`, `leaderboard.json` via `_write_top_level_outputs`) referenzieren dieselbe Konstante. `political_bias` ist KEIN Score-Modul (v4.10.16 entfernt) — Political Compass-Daten in separater `data.json.political_compass` Section.

## WebExport Score-Spalten-Vollständigkeit (ab v4.10.11)

`LdbCols` in `scripts/web_export/constants.py` MUSS eine Konstante für JEDE CSV-Modul-Spalte in `benchmark_scores/benchmark_leaderboard_detailed.csv` haben, sonst wird die Spalte stillschweigend ignoriert und landet nicht in `data.json.leaderboard.scores`.

Stand v4.10.11: 9 Spalten (Code Quality, CLI Badge, UX Writing, Documentation Quality, Content Transformation, Cultural Intelligence, Logical Reasoning, Synthesis Quality, Tool Execution). Political Bias wurde in v4.10.16 entfernt (separate `data.json.political_compass` Section).

**Symptom bei Drift:** Radar-Charts auf Webseite zeigen "Tool Execution" nicht an.

**Defense-in-Depth:** `tests/test_web_export_field_coverage.py::TestLeaderboardScoreMapping::test_no_silent_csv_column_loss` prüft, dass jede CSV-Spalte einem `LdbCols`-Eintrag zugeordnet ist und im Export landet.

## Tool-Use-Cleanup-Atomarität (ab v4.10.11)

Das Sanitize-Skript `scripts/legacy/sanitize_8_models_tooluse.py` muss ALLE Tool-Use-Datenquellen ATOMAR bereinigen, sonst entsteht Drift zwischen LB, Audit-Logs und narrativen Reviews.

**Symptom (User-Beobachtung 2026-06-26):** DeepSeek V3.1 hatte Tool-Use-Scores im Leaderboard und narrative Reviews, aber keine Audit-Files im `outputs/audit_logs/<dir>/` — der Web-Export zeigte Tool-Use-Daten ohne nachvollziehbaren Audit-Trail.

**Pflicht-Reihenfolge:**
1. Card-Reset auf `supports_tool_use: untested`.
2. Audit-Files löschen.
3. Leaderboard-Rows löschen (mit Backup).
4. Narrative Reviews löschen (mit Backup in `.bak_pre8_narrative/`).
5. Konsistenz-Check: alle Review-Dirs gegen Leaderboard-Einträge verifizieren (auch über versionierte IDs wie `gpt-5_5-2026-04-23` ↔ `gpt-5_5/`).

Niemals nur Teile ausführen.

## Cleanup-Architektur-Vollständigkeit `clean_results.py --model` (ab v4.10.11)

Wenn ein Modell via `make clean-model MODEL=X` entfernt wird, müssen ALLE Datenquellen bereinigt werden. Variant-aware integriert in `clean_model_output_directories()` und `clean_csv()`:

1. `outputs/audit_logs/<dir>/`
2. `docs/reviews/<dir>/`
3. `outputs/runs/results_<model>_<date>.json`
4. `outputs/runs/dispatch_summaries/{political_compass,tooluse,score_<module>}_<model>.json`

Sub-Family-Leaderboards (`SUB_FAMILY_LEADERBOARD_CSVS`) inkludieren: `gemma_leaderboard.csv`, `qwen_leaderboard.csv`, `provider_leaderboard.csv`.

Nach Card-Löschung werden Leaderboard und Web-Export direkt aus den Einzelkarten-Dateien (`glob("*.json")`) neu generiert — ein separater Index-Rebuild ist nicht mehr nötig (früher `_index.json`, wurde wegen Silent-Drift entfernt).

**Vergessene Pfade führen zu Web-Export-Drift** (Sub-LBs sichtbar nach Rebuild, dispatch_summaries von `_build_benchmark_run_dates` und `_build_tooluse_entry` gelesen).

Test-Suite: `tests/test_clean_results_arch_coverage.py` (13 Tests für alle Datei-Formate + Listen-Coverage + Dry-Run-Integration).

## `clean-results` Variant-Handling (v4.10.7)

`clean_results.py` muss ALLE Schreibweisen einer Model-ID bereinigen (Underscore `_`, Hyphen `-`, Punkt `.`). SSoT: `_collect_model_id_variants()` sammelt Varianten über `_safe_name()` + Card-Inhalt-Scan.

**Reihenfolge kritisch:** CSVs werden VOR Cards bereinigt — `resolve_canonical_model_id()` braucht die Card für die Variant-Auflösung.

`clean_cost_log()` ist separat von `clean_csv()` (cost_log ist keine Benchmark-CSV). `--dry-run` muss explizit in `clean.py` argparse ergänzt werden (Makefile erwartet es).

## Modell-ID-Migration nach Umbenennung (ab v4.10.12)

Das System hat **keinen automatischen Migrations-Pfad** für Modell-Umbenennungen in `config/provider_config.yaml`. Wenn ein Modell-ID geändert wird (z.B. `ornith-1_0-35b-Q8_0_gguf` → `ornith-1-0-35b`), bleiben CSV-Zeilen, Audit-Logs und Reviews der alten ID unberührt.

**Symptome:**
- Zwei Leaderboard-Einträge für dasselbe physische Modell (einer mit `display_name="TODO"` aus Draft-Card).
- Doppelte Review-Dirs (`docs/reviews/<old_safe_name>/` und `docs/reviews/<new_safe_name>/`).
- Doppelte Audit-Log-Dirs.

`consolidate-csv` und `reviews-auto` deduplizieren NICHT über ID-Varianten — `_safe_name()` macht den Merge unmöglich (Punkt vs. Bindestrich an gleicher Position ergeben unterschiedliche Safe-Names).

**Erkennung:**
```
ls outputs/audit_logs/ | grep -E "\.|_gguf|_q[0-9]"
grep -l '"model_id": "[^"]*\.[^"]*"' benchmark_scores/model_cards/*.json
```
(Punkt im model_id-Feld ist verdächtig.)

**Manuelle Cleanup-Sequenz nach ID-Umbenennung:**
1. CSV-Migration: alle Zeilen mit alter ID auf neue ID umbenennen via atomarem Python-Script (`tempfile.mkstemp + os.replace`, alle Felder prüfen, NICHT nur `model`-Spalte).
2. Draft-Card mit alter ID löschen (`benchmark_scores/model_cards/{old_id}.json`).
3. Alte Audit-Log-Dirs löschen (`outputs/audit_logs/{old_safe_name}/`).
4. Alte Review-Dirs löschen (`docs/reviews/{old_safe_name}/`).
5. ~~Card-Index rebuild~~ — entfällt, `_index.json` wurde entfernt. Web-Export und Leaderboard lesen direkt aus den Einzelkarten.
6. `make consolidate-csv` (dedupliziert physisch auf 1 Zeile pro `(model, asset_id)`, `keep="last"` hält neueren Timestamp).
7. `make leaderboard` (regeneriert `benchmark_leaderboard*.csv` aus konsolidierter CSV).
8. `make review MODEL=<new_id> AUTO=1 FORCE=1` (regeneriert Reviews mit korrektem Modellnamen).

**Defense-in-Depth (TODO):** `_load_results()` in `result_manager.py` könnte eine `resolve_canonical_model_id()` mit Variant-Auflösung via `_collect_model_id_variants()` aufrufen BEVOR CSV geschrieben wird — würde zukünftige Migrationen verhindern.

**Praxisbeispiel (2026-06-29):** Ornith wurde erst über Wizard mit alter ID gestartet, dann nach Korrektur via Auto-Benchmark mit neuer ID — Ergebnis war Duplikation über 5 Stellen, behoben in ~10 Min.

## Doku-Stempel-Drift-Schutz

Pro Session/Commit `make docs-version-check` ausführen, um Drift zwischen `CHANGELOG.md` (Code-Version, SSoT) und `**Dokumenten-Version:**`-Stempeln in `docs/*.md` zu erkennen.

Bei Drift: `make docs-version-sync YES=1` aktualisiert alle Stempel auf die aktuelle CHANGELOG-Version (mit Backup via `sed -i.bak`).

Beim Anlegen eines neuen CHANGELOG-Eintrags IMMER beide Targets laufen lassen — verhindert Drift, die in Session 40 (2026-06-27) 5 Docs gleichzeitig betraf (USER_GUIDE v3.1.0, ARCHITECTURE/DEVELOPER_GUIDE v3.8.1, BACKUP_STRATEGY v3.2.0, MODEL_CLASSIFICATION v3.0.0 statt v4.10.8).

Stempel-Format: `**Dokumenten-Version:** X.Y.Z (Überarbeitung YYYY-MM)`.

Targets in `Makefile` ab Zeile 539.
