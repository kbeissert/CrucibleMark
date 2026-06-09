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


help:
	@printf "\033[1;36mCrucibleMark - Makefile Help\033[0m\n\n"
	@printf "\033[1;33m%-25s %s\033[0m\n" "Flag" "Beschreibung"
	@printf "%-25s %s\n" "MODULE=name" "Modul-Key (z.B. cli_benchmark)"
	@printf "%-25s %s\n" "MODEL=name"  "Model-ID (z.B. qwen2.5:14b)"
	@printf "%-25s %s\n" "PROVIDER=name" "Provider-Key (z.B. ollama_local)"
	@printf "%-25s %s\n" "FORCE=1"     "Erzwingt Neustart (ignoriert Cache)"
	@printf "%-25s %s\n" "SILENT=1"    "Nur Scores, keine Audit-Logs"
	@printf "%-25s %s\n" "DRY=1|YES=1" "Vorschau-Modus|Auto-Bestätigung"
	@printf "%-25s %s\n" "JSON=1"      "Strukturierte CLI-Ausgabe"
	@printf "\n"
	@printf "\033[1;32mBenchmarking (Standard, Auto, Cross, Human)\033[0m\n"
	@printf "  %-25s %s\n" "benchmark"       "Standard-Benchmark"
	@printf "  %-25s %s\n" "benchmark-auto"  "Full-Auto-Benchmark (Smart Autofill)"
	@printf "  %-25s %s\n" "benchmark-cross" "Module vs ALL LLMs"
	@printf "  %-25s %s\n" "benchmark-human" "Human Baseline Test (PC)"
	@printf "\n"
	@printf "\033[1;32mTool-Use (Benchmarking, Leaderboard, Reporting)\033[0m\n"
	@printf "  %-25s %s\n" "benchmark-tooluse" "Tool-Use-Batch-Run (MCP)"
	@printf "  %-25s %s\n" "tooluse-run"       "Schnelllauf (start/stop MCP)"
	@printf "  %-25s %s\n" "tooluse-leaderboard" "CSV-Leaderboard Update"
	@printf "  %-25s %s\n" "tooluse-report"    "Markdown-Reports"
	@printf "\n"
	@printf "\033[1;32mPolitical Compass\033[0m\n"
	@printf "  %-25s %s\n" "political-compass"      "Standalone PC-Audit"
	@printf "  %-25s %s\n" "political-compass-safe" "Sicherheits-Check (Triple-Run)"
	@printf "\n"
	@printf "\033[1;32mReporting & Reviews\033[0m\n"
	@printf "  %-25s %s\n" "leaderboard"     "Generiere CSV"
	@printf "  %-25s %s\n" "review"          "Generiere Modell-Review (MODEL=)"
	@printf "  %-25s %s\n" "reviews-auto"    "Alle Review-Typen (Sequenziell)"
	@printf "  %-25s %s\n" "provider-stats"  "System-Performance"
	@printf "\n"
	@printf "\033[1;32mCard-Lifecycle & Validierung\033[0m\n"
	@printf "  %-25s %s\n" "model-cards"     "Erstelle/Update-Vorlagen"
	@printf "  %-25s %s\n" "validate-cards"  "Schema-Prüfung"
	@printf "  %-25s %s\n" "cards-sync"      "SSoT-Synchronisierung"
	@printf "\n"
	@printf "\033[1;32mCleanup & Maintenance\033[0m\n"
	@printf "  %-25s %s\n" "backup"          "Snapshot-Pipeline (Tar + Clean)"
	@printf "  %-25s %s\n" "clean-all"       "Cache/CSV Bereinigung"


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
