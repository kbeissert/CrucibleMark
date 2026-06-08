.PHONY: \
	help install install-dev \
	benchmark political-compass political-compass-safe benchmark-cross-model benchmark-auto benchmark-human \
	review reviews-auto reviews-auto-legacy reviews-bias-auto reviews-tooluse-auto reviews-all reviews-check review-new model-cards model-card provider-cards leaderboard provider-stats \
	validate validate-single validate-assets validate-structure validate-cards validate-cards-template cards-sync provider-cards-update model-cards-update test diff-results analyze-costs update-prices sync-cost-limits \
	list-models judge-health list-modules \
	probe-thinking probe-all-thinking \
	ensure-card ensure-cards \
	web-export web-export-dev \
	mcp-start mcp-stop mcp-health mcp-mock \
	tooluse-leaderboard tooluse-run tooluse-report tooluse-report-summary tooluse-report-json \
	benchmark-tooluse benchmark-tooluse-local benchmark-tooluse-force \
	clean clean-csv clean-model clean-module clean-all clean-runs consolidate-csv prune-orphans clean-bak clean-reviews \
	backup backup-prep

# Python-Interpreter aus .venv verwenden
PYTHON := .venv/bin/python

# Phase 27: Anzahl Benchmark-Runs, die pro Modell behalten werden.
# Spiegelung von utils.backup_targets.RUNS_KEEP_DEFAULT (SSoT).
# Ueberschreibbar via  make clean-runs RUNS_KEEP=10
RUNS_KEEP ?= 5


# Phase 29: Help-Text komplett neu strukturiert — alle 83 Targets dokumentiert,
# Format vereinheitlicht (Spalte 1: Target, Spalte 2: Beschreibung),
# Sektionen entsprechen der Recipe-Reihenfolge im Makefile.

help:
	@echo "CrucibleMark - Makefile Commands (Phase 29 Help-Text v2)"
	@echo ""
	@echo "=== Global Flags ==="
	@echo "  MODULE=name       Modul-Key (z.B. MODULE=cli_benchmark)"
	@echo "  MODEL=name        Model-ID (z.B. MODEL=qwen2.5:14b)"
	@echo "  PROVIDER=name     Provider-Key (z.B. PROVIDER=ollama_local)"
	@echo "  FORCE=1           Erzwingt Neustart (ignoriert Cache/Scores)"
	@echo "  SILENT=1          Ueberspringt Audit-Logs (nur Scores)"
	@echo "  DRY=1 / DRY_RUN=1 Vorschau-Modus fuer Clean-/Backup-Skripte"
	@echo "  YES=1             Bestaetigungs-Abfragen automatisch mit 'ja' beantworten"
	@echo "  JSON=1            Strukturierte JSON-Ausgabe (CI-tauglich)"
	@echo ""
	@echo "=== Benchmarking (Standard + Auto + Cross-Model + Human Baseline) ==="
	@echo "  make benchmark              Standard-Benchmark"
	@echo "                              [Flags: SILENT, FORCE, MODEL, MODULE]"
	@echo "  make benchmark-auto         Auto-Fill Benchmark (Smart Autofill)"
	@echo "                              [Flags: SILENT, FORCE, MCP_MODE]"
	@echo "                              Pre-Step [0/2]: fuellt Tool-Use-Backlog"
	@echo "  make benchmark-cross-model  Module vs ALL LLMs"
	@echo "                              [Flags: FORCE, MODULE]"
	@echo "  make benchmark-human        Human Baseline Test (PC)"
	@echo ""
	@echo "=== Tool-Use Benchmark (Wizard + Batch + Local + Force) ==="
	@echo "  make benchmark-tooluse      Tool Use Benchmark"
	@echo "                              [Flags: MODEL, MODELS, ALL, PROVIDER, FORCE, SILENT, MCP_MODE]"
	@echo "  make benchmark-tooluse-local  Nur lokale Ollama-Modelle (PROVIDER=ollama)"
	@echo "  make benchmark-tooluse-force  Alle Modelle (FORCE=1, ignoriert Cache)"
	@echo "  make tooluse-run            Quick-Run (startet/stoppt MCP, fuehrt aus)"
	@echo "                              [Flags: MODEL]"
	@echo "  make tooluse-leaderboard    Tool-Use Leaderboard (CSV-Update)"
	@echo "  make tooluse-report         Generiert Markdown-Reports"
	@echo "                              [Flags: MODEL]"
	@echo "  make tooluse-report-summary Fleet-Summary (eine Markdown-Datei)"
	@echo "  make tooluse-report-json    JSON-Export fuer Web-Frontend"
	@echo "                              [Flags: MODEL]"
	@echo ""
	@echo "=== Political Compass (Standard + Safe + Anomaly) ==="
	@echo "  make political-compass      Eigenstaendiger PC-Test (Audit ON)"
	@echo "                              [Flags: MODEL, FORCE]"
	@echo "  make political-compass-safe Sicherheits-/Anomaliepruefung (Triple-Run)"
	@echo "                              [Flags: MODEL]"
	@echo ""
	@echo "=== Reporting & Reviews ==="
	@echo "  make leaderboard            Generate Leaderboard CSV"
	@echo "  make review                 Generate Review"
	@echo "                              [Flags: MODEL=name, ALL=1, TYPE=bias|tooluse|provider, AUTO=1, FORCE=1]"
	@echo "  make review-new             Einzelnen Review mit Auto-Card"
	@echo "                              (MODEL=name erforderlich)"
	@echo "  make reviews-all            ALLE Review-Typen fuer ALLE Modelle"
	@echo "  make reviews-auto           ALLE Review-Typen pro Modell (sequenziell)"
	@echo "                              [Flags: FORCE=1]"
	@echo "  make reviews-auto-legacy    Nur Benchmark-Reviews (Legacy-Modus)"
	@echo "  make reviews-bias-auto      PC-Bias-Reviews fuer Modelle mit Bias-Report"
	@echo "  make reviews-tooluse-auto   Tool-Use-Reviews fuer supports_tool_use=true"
	@echo "  make reviews-check          Zeigt fehlende Cards (kein Schreiben)"
	@echo "  make provider-stats         System-Latenzen + Provider Landscape Review"
	@echo ""
	@echo "=== Card-Lifecycle (5 Phasen: erstellen -> ergaenzen -> validieren -> synchronisieren -> status) ==="
	@echo "  Detail-Doku:  docs/CARD_MANAGEMENT.md"
	@echo ""
	@echo "  Phase 1 — Erstellen:"
	@echo "    make model-cards MODEL=<id>             Neue Model-Card-Vorlage"
	@echo "    make model-cards PROVIDER=<key>         Model-Card mit Provider-Kontext"
	@echo "    make model-card                          Alias fuer model-cards"
	@echo "    make provider-cards PROVIDER=<name>      Provider-Card (LLM-generiert)"
	@echo "    make provider-cards                      ALLE fehlenden Provider-Cards"
	@echo ""
	@echo "  Phase 2 — Ergaenzen (Defaults befuellen):"
	@echo "    make ensure-card MODEL=<id>             Eine Card mit Defaults befuellen"
	@echo "    make ensure-cards                        ALLE Cards (DRY=1 = Vorschau)"
	@echo ""
	@echo "  Phase 3 — Validieren (YAML-Schema-Pruefung):"
	@echo "    make validate-cards-template            Beide Typen pruefen"
	@echo "      CARD_TYPE=model|provider|all         Nur einen Typ"
	@echo "      FAIL_ON_DRIFT=1                       CI-Gate (Exit 1 bei Drift)"
	@echo "      JSON=1                                JSON-Report fuer CI"
	@echo "    make validate-cards                     Konsistenz tier/summary/commercial"
	@echo ""
	@echo "  Phase 4 — Synchronisieren (SSoT-Sync, add automatisch + delete mit Bestaetigung):"
	@echo "    make cards-sync                          Vorschau + Bestaetigungs-Abfrage"
	@echo "      DRY_RUN=1                             Nur Vorschau, nichts schreiben"
	@echo "      YES=1                                 Loesch-Bestaetigung automatisch"
	@echo "      JSON=1                                JSON-Report fuer CI"
	@echo "    make provider-cards-update              --update via Provider-Generator"
	@echo "    make model-cards-update                 --update via Model-Generator"
	@echo ""
	@echo "  Phase 5 — Status (Provider-Card-Hygiene):"
	@echo "    make provider-cards-status              Verifiziert/stale/unknown Report"
	@echo "      STALE_DAYS=N                          Schwellwert (default 90)"
	@echo "      JSON=1                                JSON-Output fuer CI"
	@echo "  Phase 6 — Thinking-Probe (LLM-Reasoning-Erkennung):"
	@echo "    make probe-thinking MODEL=<id>          Thinking-Probe fuer ein Modell"
	@echo "    make probe-all-thinking                 Retro-aktiv fuer alle Cards ohne Probe"
	@echo ""
	@echo "=== Validation & QA ==="
	@echo "  make validate                Validate alle test assets (--all)"
	@echo "  make validate-assets MODULE=<key>"
	@echo "                               Prueft benchmark_modules/<key>/assets"
	@echo "  make validate-single ASSET=<pfad>"
	@echo "                               Prueft einen einzelnen Asset-Pfad"
	@echo "  make validate-structure       Prueft Modul-Struktur"
	@echo "  make validate-csv            CSV-Hygiene-Check (Dry-Run, mit FIX=1 anwenden)"
	@echo "  make test                    Pytest-Suite (validate ist Abhaengigkeit)"
	@echo "  make diff-results            Vergleicht Runs (REF=, TEST=, THRESH=)"
	@echo ""
	@echo "=== Tools (Info, Diagnostics, Maintenance) ==="
	@echo "  make list-models             List alle Modelle"
	@echo "  make list-modules            List aktive Module"
	@echo "  make judge-health            Judge-Provider Connectivity-Check"
	@echo "                              [Flags: PROVIDER]"
	@echo "  make audit-markdown          Markdown/YAML Audit + Fix"
	@echo "                              [Flags: FIX=1]"
	@echo "  make analyze-costs           Token-Cost Analyse (Pricing + Prompts)"
	@echo "  make update-prices           Pricing-Cache Update (LiteLLM DB)"
	@echo "  make sync-cost-limits        cost_limits.yaml vs Config sync"
	@echo "                              [Flags: FIX=1]"
	@echo ""
	@echo "=== MCP Server (Local) ==="
	@echo "  make mcp-start MODE=<live|mock>"
	@echo "                               Startet MCP-Server (Hintergrund-Prozess)"
	@echo "  make mcp-stop                Stoppt MCP-Server (PID + pkill Fallback)"
	@echo "  make mcp-health              /health-Endpoint check"
	@echo "  make mcp-mock                Alias: mcp-start MODE=mock"
	@echo ""
	@echo "=== Web Export ==="
	@echo "  make web-export              Exportiert Daten fuer Web-Frontend"
	@echo "                              [Flags: WEB_DATA_DIR]"
	@echo "  make web-export-dev          Direkter Export ins 11ty-Projekt"
	@echo ""
	@echo "=== Data Management & Cleanup ==="
	@echo "  make backup                  Komplette Pipeline (backup-prep + tar + cleanup-chain)"
	@echo "                              [Flags: RUNS_KEEP=N]"
	@echo "  make backup-prep             Pre-Backup-Hygiene (DRY_RUN=1 = Vorschau)"
	@echo "  make consolidate-csv         CSVs deduplizieren + ID-normalisieren (SSoT)"
	@echo "  make prune-orphans           Verwaiste Reports loeschen (FORCE=1 = echt)"
	@echo "  make clean                   PyCache + Standard-Dumps"
	@echo "  make clean-csv               ALLE Benchmark-CSVs loeschen"
	@echo "  make clean-model MODEL=x     Modell-Ergebnisse loeschen (DRY=1 = Vorschau)"
	@echo "  make clean-module MODULE=x   Modul-Ergebnisse loeschen (DRY=1 = Vorschau)"
	@echo "  make clean-all               Cache + CSVs loeschen (DRY=1 = Vorschau)"
	@echo "  make clean-runs              Alte Run-JSONs loeschen (RUNS_KEEP=N, FORCE=1)"
	@echo "  make clean-reviews           Reviews bereinigen (FORCE=1 = echt)"
	@echo "  make clean-bak               .bak_* / .backup_* Dateien loeschen"
	@echo "  make clean-wizard            Interaktiver Cleanup-Wizard"
	@echo ""
	@echo "=== Backup-Lifecycle (Snapshot -> Prune -> Consolidate) ==="
	@echo "  Backup laeuft in 3 Phasen:  backup-prep (hygiene) -> tar-snapshot -> cleanup-chain"
	@echo "  Detail-Doku:  docs/BACKUP_STRATEGY.md (v3.2.0)"
	@echo ""
	@echo "  Hygiene vor dem Snapshot:"
	@echo "    make backup-prep DRY_RUN=1            Vorschau"
	@echo "    make backup-prep                      Echtlauf"
	@echo ""
	@echo "  Snapshot + Cleanup-Chain (volle Pipeline):"
	@echo "    make backup                           Komplette Pipeline"
	@echo "    make backup RUNS_KEEP=10              Mit abweichendem Keep-Count"
	@echo ""
	@echo "  Rotation (manuell, monatlich empfohlen):"
	@echo "    find backups/ -name '*.tar.gz' -mtime +90 -delete"



# === BENCHMARKING ===

benchmark:
	@echo "Starting Benchmark ($(if $(SILENT),Silent Mode,Standard Audit Mode))..."
	$(PYTHON) scripts/run_score_benchmark.py $(if $(SILENT),--silent,) $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--modules "$(MODULE)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass:
	@echo "Starting standalone Political Compass benchmark (Audit Logs ON)..."
	$(PYTHON) scripts/run_political_compass_benchmark.py $(if $(MODEL),--model "$(MODEL)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass-safe:
	@echo "Starting Anomaly Verification Protocol (Make Political Compass Safe Test)..."
	$(PYTHON) scripts/core/verify_compass_anomalies.py $(if $(MODEL),--model "$(MODEL)" --threshold 0.0)

benchmark-cross-model:
	@echo "Starting Cross-Model Benchmark..."
	@$(PYTHON) scripts/core/run_cross_model_benchmark.py $(if $(MODULE),--module $(MODULE)) $(if $(FORCE),--force)

benchmark-auto:
	@echo "Starting Full Auto Benchmark (Smart Autofill $(if $(SILENT),Silent Mode,with Audit Logs))..."
	$(PYTHON) scripts/core/benchmark_auto.py $(if $(SILENT),--silent,) $(if $(FORCE),--force) $(if $(MCP_MODE),--mcp-mode $(MCP_MODE))

benchmark-human:
	@echo "Starting Human Baseline Test..."
	$(PYTHON) scripts/tools/run_human_compass.py

# === REPORTING & STANDARDS ===

model-cards:
	$(PYTHON) scripts/analysis/generate_model_cards.py $(if $(MODEL),--model "$(MODEL)") $(if $(PROVIDER),--provider "$(PROVIDER)") $(if $(FORCE),--force)

model-card: model-cards

ensure-card:
	@if [ -z "$(MODEL)" ]; then echo "Fehler: MODEL=<model-id> ist erforderlich."; exit 1; fi
	$(PYTHON) scripts/dev/ensure_card_structure.py --model "$(MODEL)" $(if $(DRY),--dry-run)

ensure-cards:
	$(PYTHON) scripts/dev/ensure_card_structure.py --missing $(if $(ALL),--all) $(if $(DRY),--dry-run)

provider-cards:
	@if [ -n "$(PROVIDER)" ]; then \
		echo "Generiere Provider Card fuer $(PROVIDER)..."; \
		$(PYTHON) scripts/analysis/generate_provider_cards.py --provider "$(PROVIDER)" $(if $(FORCE),--force); \
	else \
		echo "Generiere alle fehlenden Provider Cards..."; \
		$(PYTHON) scripts/analysis/generate_provider_cards.py $(if $(FORCE),--force); \
	fi

provider-cards-status:
	@echo "Pruefe Provider Card Status (stale nach $(or $(STALE_DAYS),90) Tagen)..."
	@$(PYTHON) scripts/analysis/provider_card_status.py $(if $(STALE_DAYS),--stale-days $(STALE_DAYS),) $(if $(JSON),--json,)

validate-cards-template:
	@echo "=== Card-Template-Validierung (SSoT: config/card_template_*.yaml) ==="
	@echo "Prueft alle Model- und Provider-Cards gegen die Template-Schemata."
	@echo "Issues: missing_required | unknown_sentinel | drift_extras | missing_sub_field | parse_error"
	@echo ""
	@$(PYTHON) scripts/analysis/validate_cards.py \
		$(if $(CARD_TYPE),--card-type $(CARD_TYPE),) \
		$(if $(JSON),--json,) \
		$(if $(FAIL_ON_DRIFT),--fail-on-drift,)

cards-sync:
	@echo "=== Card-Sync mit Python-Dict-Template (utils/card_utils + utils/provider_card_template) ==="
	@echo "Add:  fehlende Felder mit Default ergaenzen (automatisch)."
	@echo "Del:  Felder ohne Template entfernen (mit Bestaetigung)."
	@echo ""
	@$(PYTHON) scripts/analysis/sync_cards.py \
		$(if $(CARD_TYPE),--card-type $(CARD_TYPE),--card-type all) \
		$(if $(DRY_RUN),--dry-run,) \
		$(if $(YES),--yes,) \
		$(if $(JSON),--json,)

provider-cards-update:
	@echo "=== Provider Card Update (--update in generate_provider_cards.py) ==="
	@$(PYTHON) scripts/analysis/generate_provider_cards.py --update \
		$(if $(YES),--yes,) \
		$(if $(DRY_RUN),--dry-run,)

model-cards-update:
	@echo "=== Model Card Update (--update in generate_model_cards.py) ==="
	@$(PYTHON) scripts/analysis/generate_model_cards.py --update \
		$(if $(YES),--yes,) \
		$(if $(DRY_RUN),--dry-run,)


probe-thinking:
	@if [ -z "$(MODEL)" ]; then echo "Fehler: MODEL=<model-id> ist erforderlich."; exit 1; fi
	$(PYTHON) scripts/tools/probe_thinking.py --model "$(MODEL)" $(if $(PROVIDER),--provider $(PROVIDER))

probe-all-thinking:
	@echo "Probe fuer alle Cards ohne Probe-Feld..."
	$(PYTHON) scripts/tools/probe_thinking.py --missing

provider-stats:
	@echo "Aggregating Provider Stats (Ping vs System Speed)..."
	$(PYTHON) scripts/analysis/generate_provider_stats.py
	@echo "Generating Provider Landscape Review..."
	$(PYTHON) scripts/analysis/generate_review.py -t provider

review:
	@if [ -n "$(ALL)" ]; then \
		echo "Generating $(if $(TYPE),$(TYPE),benchmark)-Reviews for ALL models..."; \
		$(PYTHON) scripts/analysis/generate_review.py --all $(if $(TYPE),--type $(TYPE)) $(if $(AUTO),--auto) $(if $(FORCE),--force); \
	elif [ -n "$(MODEL)" ]; then \
		echo "Generating $(if $(TYPE),$(TYPE),benchmark)-Review for $(MODEL)..."; \
		$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)" $(if $(TYPE),--type $(TYPE)) $(if $(AUTO),--auto) $(if $(FORCE),--force); \
	else \
		echo "Fehler: Bitte gib MODEL=name oder ALL=1 an. Optional: TYPE=bias|tooluse AUTO=1 FORCE=1"; \
		exit 1; \
	fi


reviews-auto:
	@echo "Generiere ALLE Review-Typen (Benchmark + PC-Bias + Tool-Use) pro Modell..."
	@echo "  Reihenfolge: pro Modell benchmark -> bias -> tooluse, dann naechstes Modell."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto --type all --per-model $(if $(FORCE),--force)

reviews-auto-legacy:
	@echo "Generiere nur Benchmark-Reviews fuer alle Modelle (Legacy-Verhalten)..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto $(if $(FORCE),--force)

reviews-bias-auto:
	@echo "Generiere PC-Bias-Reviews fuer alle Modelle mit 00_bias_report.md..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto --type bias

reviews-tooluse-auto:
	@echo "Generiere Tool-Use-Reviews fuer alle Modelle mit supports_tool_use=true..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto --type tooluse $(if $(FORCE),--force)

reviews-all:
	@echo "Generiere alle Review-Typen (Benchmark + PC-Bias + Tool-Use) fuer alle Modelle..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto --type all $(if $(FORCE),--force)

reviews-check:
	@echo "Pruefe Abhaengigkeiten (Cards) fuer alle Modell-Reviews (kein Schreiben)..."
	$(PYTHON) scripts/analysis/generate_review.py --all --dry-run

review-new:
	@if [ -z "$(MODEL)" ]; then echo "Fehler: MODEL=name erforderlich (z.B. make review-new MODEL=claude-3-5-haiku)"; exit 1; fi
	@echo "Generiere Review fuer $(MODEL) (fehlende Cards werden automatisch erstellt)..."
	$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)" --auto

leaderboard:
	@echo "Generating Leaderboard..."
	$(PYTHON) scripts/core/generate_leaderboard.py

# === VALIDATION & QA ===

validate:
	@echo "Validating all modules..."
	$(PYTHON) scripts/tools/validate_assets.py --all

validate-assets:
	@if [ -z "$(MODULE)" ]; then \
		echo "Error: MODULE variable not set (e.g. make validate-assets MODULE=tooluse)"; \
		exit 1; \
	fi
	$(PYTHON) scripts/tools/validate_assets.py benchmark_modules/$(MODULE)/assets

validate-single:
	@if [ -z "$(ASSET)" ]; then \
		echo "Error: ASSET variable not set"; \
		exit 1; \
	fi
	$(PYTHON) scripts/tools/validate_assets.py $(ASSET)

validate-structure:
	@echo "Checking Module Structure..."
	$(PYTHON) scripts/tools/validate_structure.py

validate-cards:
	@echo "Checking Model Card consistency (tier, summary, commercial)..."
	$(PYTHON) scripts/dev/validate_model_cards.py

test: validate
	@echo "Running Unit Tests..."
	$(PYTHON) -m pytest benchmark_modules/ utils/scoring/llm_judge/tests/ -v --tb=short

diff-results:
	@echo "Comparing Benchmark Results..."
	$(PYTHON) scripts/analysis/compare_baselines.py $(if $(REF),--ref $(REF)) $(if $(TEST),--test $(TEST)) $(if $(THRESH),--threshold $(THRESH))

analyze-costs:
	@echo "Analyzing Prompt Token Costs..."
	$(PYTHON) -c "from utils.pricing_updater import PricingUpdater; p=PricingUpdater(); p.ensure_fresh(); print(p.get_status_line())"
	$(PYTHON) scripts/analysis/analyze_prompts.py

update-prices:
	@echo "Updating token pricing cache from LiteLLM Pricing DB..."
	$(PYTHON) scripts/dev/update_prices.py

sync-cost-limits:
	@echo "Checking cost_limits.yaml gegen Modell-Konfiguration ..."
	$(PYTHON) scripts/dev/sync_cost_limits.py $(if $(FIX),--fix)

# === TOOLS & MAINTENANCE ===

list-models:
	@$(PYTHON) scripts/tools/list_models.py

judge-health:
	@echo "Checking LLM Judge provider connectivity..."
	$(PYTHON) scripts/tools/judge_health.py $(if $(PROVIDER),--provider $(PROVIDER))

list-modules:
	@echo "Available Modules:"
	@if [ -f "scripts/tools/list_modules.py" ]; then \
		$(PYTHON) scripts/tools/list_modules.py; \
	else \
		$(PYTHON) -c "import yaml; config=yaml.safe_load(open('benchmark_config.yaml')); [print(f'  {i+1}. {k}: {v[\"name\"]}') for i, (k,v) in enumerate(config.get('modules', {}).items()) if v.get('enabled', True)]"; \
	fi

audit-markdown:
	@echo "Running Markdown & YAML Audit..."
	@$(PYTHON) scripts/maintenance/audit_markdown.py $(if $(FIX),--fix)

clean:
	@if [ -n "$(MODEL)" ] || [ -n "$(MODULE)" ] || [ -n "$(ALL)" ]; then \
		$(PYTHON) scripts/maintenance/clean.py $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(ALL),--all); \
	else \
		$(PYTHON) scripts/maintenance/clean.py --cache; \
	fi

clean-csv:
	@$(PYTHON) scripts/maintenance/clean.py --csv

# Phase 28: DRY=1 reicht --dry-run an clean_results durch
# (Default: echte Loeschung, konsistent mit clean-runs FORCE=1)
clean-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "Use: make clean-model MODEL=name [DRY=1]"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --model "$(MODEL)" $(if $(DRY),--dry-run)

clean-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "Use: make clean-module MODULE=key [DRY=1]"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --module "$(MODULE)" $(if $(DRY),--dry-run)

clean-all:
	@$(PYTHON) scripts/maintenance/clean.py --all $(if $(DRY),--dry-run)

clean-runs:
	@$(PYTHON) scripts/maintenance/clean.py --runs $(RUNS_KEEP) $(if $(FORCE),--force)

clean-wizard:
	@$(PYTHON) scripts/maintenance/clean.py --interactive


prune-orphans:
	@if [ -n "$(FORCE)" ]; then \
		echo "Loesche verwaiste Report-Verzeichnisse..."; \
		$(PYTHON) scripts/maintenance/prune_orphaned_reports.py --delete --force; \
	else \
		echo "Verwaiste Report-Verzeichnisse (Dry-Run)..."; \
		$(PYTHON) scripts/maintenance/prune_orphaned_reports.py; \
	fi

consolidate-csv:
	@if [ -f "scripts/maintenance/consolidate_csv.py" ]; then \
		$(PYTHON) scripts/maintenance/consolidate_csv.py; \
	fi

clean-bak:
	@echo "Entferne .bak_* Dateien aus benchmark_scores/..."
	@find benchmark_scores/ -name "*.bak_*" -delete
	@echo "   -> .bak_* Dateien entfernt."

clean-reviews:
	@if [ -n "$(FORCE)" ]; then \
		echo "Bereinige alte Reviews (behalte je 1 pro Modell)..."; \
		$(PYTHON) scripts/maintenance/cleanup_reviews.py --delete --force; \
	else \
		echo "Alte Reviews (Dry-Run)..."; \
		$(PYTHON) scripts/maintenance/cleanup_reviews.py; \
	fi

# Phase 27: Pre-Backup-Hygiene. Raeumt outputs/ auf, bevor das tar
# geschnappt wird (alte tooluse_unreachable_*.json, verwaiste Backup-
# Artefakte, Session-Files). Delegiert an SSoT-Helper
# (scripts/maintenance/cleanup_helpers.py).
backup-prep:
	@if [ -n "$(DRY_RUN)" ]; then \
		echo "Pre-Backup-Hygiene (Dry-Run)..."; \
		$(PYTHON) scripts/maintenance/cleanup_helpers.py --dry-run; \
	else \
		echo "Pre-Backup-Hygiene..."; \
		$(PYTHON) scripts/maintenance/cleanup_helpers.py; \
	fi

backup: backup-prep
	@echo "Creating full backup..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' --exclude='*.bak_*' \
	     --exclude='*.backup_*' \
	     --exclude='audit_logs_backup_*.tar.gz' \
	     --exclude='audit_logs_legacy_backup_*' \
	     --exclude='audit_logs_spurious_archive' \
	     --exclude='audit_logs.zip' \
	     --exclude='model_cards_backup_*.tar.gz' \
	     --exclude='model_cards_spurious_archive' \
	     --exclude='tooluse_unreachable_*.json' \
	     --exclude='outputs/temp/session_*.json' \
	     -czf backups/cruciblemark_backup_$$(date +%Y%m%d_%H%M%S).tar.gz \
	     benchmark_scores/ outputs/ benchmark_modules/ docs/reviews/ docs/audits/ config/ memory-bank/ benchmark_config.yaml
	@echo "Backup created."
	@$(MAKE) clean-runs FORCE=1 RUNS_KEEP=$(RUNS_KEEP)
	@$(MAKE) consolidate-csv
	@$(MAKE) clean-bak
	@$(MAKE) clean-reviews FORCE=1
	@$(MAKE) prune-orphans FORCE=1
	@rm -rf outputs/temp/*
	@echo "Backup chain complete."

# === MCP SERVER ===

mcp-start:
	@echo "Starting CrucibleMark MCP Server (mode=$(or $(MODE),mock))..."
	@if curl -s http://localhost:8765/health > /dev/null 2>&1; then \
		echo "  MCP Server already running — skipped."; \
	else \
		{ [ -f "$$HOME/.api_keys" ] && . "$$HOME/.api_keys" || true; $(PYTHON) cruciblemark-mcp/server.py --mode $(or $(MODE),mock); } & \
	fi

mcp-stop:
	@if [ -f .mcp.pid ]; then \
		kill $$(cat .mcp.pid) 2>/dev/null || true; \
		rm -f .mcp.pid; \
		echo "MCP Server stopped."; \
	else \
		pkill -f "cruciblemark-mcp/server.py" 2>/dev/null || true; \
		echo "MCP Server stopped (pkill fallback)."; \
	fi

mcp-health:
	@curl -s http://localhost:8765/health | $(PYTHON) -m json.tool

mcp-mock:
	@$(MAKE) mcp-start MODE=mock

# === TOOL USE LEADERBOARD ===

tooluse-leaderboard:
	@echo "Calculating Tool Use Leaderboard..."
	$(PYTHON) scripts/tools/tooluse_leaderboard.py

tooluse-run:
	@echo "Running Tool Use Benchmark (requires MCP)..."
	$(MAKE) mcp-start MODE=$(or $(MCP_MODE),mock)
	sleep 1.5
	$(PYTHON) run_benchmark.py --module tooluse $(if $(MODEL),--model "$(MODEL)")
	$(MAKE) mcp-stop
	$(MAKE) tooluse-leaderboard

tooluse-report:
	@echo "Generating Tool Use Reports..."
	$(PYTHON) scripts/analysis/generate_tooluse_report.py $(if $(MODEL),--model "$(MODEL)")

tooluse-report-summary:
	@echo "Generating Tool Use Fleet Summary..."
	$(PYTHON) scripts/analysis/generate_tooluse_report.py --summary-only

tooluse-report-json:
	@echo "Generating Tool Use JSON Web Export..."
	$(PYTHON) scripts/analysis/generate_tooluse_report.py --json-only $(if $(MODEL),--model "$(MODEL)")

# === TOOL USE BENCHMARK (WIZARD / BATCH) ===

benchmark-tooluse:
	@echo "Starting Tool Use Benchmark (MCP: $(or $(MCP_MODE),live))..."
	@$(PYTHON) scripts/run_tooluse_benchmark.py \
		$(if $(MODEL),--model "$(MODEL)") \
		$(if $(MODELS),--models "$(MODELS)") \
		$(if $(ALL),--all) \
		$(if $(PROVIDER),--provider "$(PROVIDER)") \
		$(if $(FORCE),--force) \
		$(if $(SILENT),--silent) \
		--mcp-mode $(or $(MCP_MODE),live)
	@$(MAKE) tooluse-leaderboard
	@$(MAKE) tooluse-report-summary

benchmark-tooluse-local:
	@$(MAKE) benchmark-tooluse PROVIDER=ollama

benchmark-tooluse-force:
	@$(MAKE) benchmark-tooluse FORCE=1

# === WEB EXPORT ===

web-export:
	@echo "Starte Web Export..."
	$(PYTHON) scripts/web_export.py $(if $(WEB_DATA_DIR),--output $(WEB_DATA_DIR),)
	@echo "Export abgeschlossen."

web-export-dev:
	@echo "Exportiere direkt ins 11ty-Projekt..."
	$(PYTHON) scripts/web_export.py --output ../cruciblemark-web/src/_data/raw/
	@echo "Dev-Export abgeschlossen."

# === PHASE 9: CSV HYGIENE (Defense-in-Depth) ===

validate-csv:
	@echo "=== CSV-Hygiene-Check (Dry-Run) ==="
	@echo "Prueft alle Benchmark-CSVs auf Header-Repeats, narrative Asset-IDs und ungueltige Modelle."
	@echo ""
	@$(PYTHON) scripts/maintenance/sanitize_benchmark_csvs.py
	@echo ""
	@echo "Tipp: Mit FIX=1 wird der Sanitizer mit --apply ausgefuehrt (Backup vorher anlegen):"
	@echo "      make backup && make validate-csv FIX=1"
