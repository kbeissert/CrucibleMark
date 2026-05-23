.PHONY: \
	help install install-dev \
	benchmark political-compass political-compass-safe benchmark-cross-model benchmark-auto benchmark-human \
	review reviews-auto reviews-check review-new model-cards model-card provider-cards leaderboard provider-stats \
	validate validate-single validate-assets validate-structure validate-cards test diff-results analyze-costs update-prices sync-cost-limits \
	list-models judge-health list-modules \
	probe-thinking probe-all-thinking \
	web-export web-export-dev \
	mcp-start mcp-stop mcp-health mcp-mock \
	tooluse-leaderboard tooluse-run tooluse-report tooluse-report-summary tooluse-report-json \
	benchmark-tooluse benchmark-tooluse-local benchmark-tooluse-force \
	clean clean-csv clean-model clean-module clean-all clean-runs consolidate-csv prune-orphans clean-bak clean-reviews \
	backup

# Python-Interpreter aus .venv verwenden
PYTHON := .venv/bin/python

help:
	@echo "CrucibleMark - Makefile Commands"
	@echo ""
	@echo "=== Global Flags ==="
	@echo "  MODULE=name   z.B. MODULE=cli_benchmark"
	@echo "  MODEL=name    z.B. MODEL=qwen2.5:14b"
	@echo "  FORCE=1       Erzwingt einen Neustart (ignoriert Cache/Scores)"
	@echo "  SILENT=1      Überspringt Audit-Logs (nur Scores)"
	@echo ""
	@echo "=== Benchmarking ==="
	@echo "  make benchmark            Standard Benchmark (Flags: SILENT, FORCE, MODEL, MODULE)"
	@echo "  make benchmark-auto       Auto-Fill Benchmark (Flags: SILENT, FORCE)"
	@echo "  make benchmark-cross-model Module vs ALL LLMs (Flags: FORCE, MODULE)"
	@echo ""
	@echo "=== Tool Use ==="
	@echo "  make benchmark-tooluse    Tool Use Benchmark — Wizard oder direkt"
	@echo "                            (Flags: MODEL=name, PROVIDER=key, MCP_MODE=live/mock, FORCE=1, SILENT=1)"
	@echo "  make benchmark-tooluse-local  Nur lokale Ollama-Modelle"
	@echo "  make benchmark-tooluse-force  Alle Modelle (Cache ignorieren)"
	@echo ""
	@echo "=== Political Compass ==="
	@echo "  make political-compass    Eigenstaendiger PC-Test (Flags: MODEL=name, FORCE=1)"
	@echo "  make political-compass-safe Sicherheits-/Anomaliepruefung (Triple-Run erzwingen)"
	@echo "  make benchmark-human      Human Baseline Test (PC)"
	@echo ""
	@echo "=== Reporting & Standards ==="
	@echo "  make leaderboard          Generate Leaderboard CSV"
	@echo "  make review               Generate Review (Flags: MODEL=name, ALL=1, TYPE=bias)"
	@echo "  make reviews-auto         Reviews fuer alle Modelle (generiert fehlende Cards automatisch)"
	@echo "  make reviews-check        Zeigt fehlende Cards (kein Review, kein Schreiben)"
	@echo "  make review-new           Einzelnen Review generieren mit Auto-Card (MODEL=name erforderlich)"
	@echo "  make model-cards          Neues Model Card Template anlegen (MODEL=name erforderlich, PROVIDER=key optional)"
	@echo "  make provider-cards       Provider Cards generieren (Flags: PROVIDER=name, FORCE=1)"
	@echo "  make provider-stats       System-Latenzen analysieren (Ping vs. TTFB) und Provider-Review erstellen"
	@echo "  make probe-thinking       Thinking-Probe fuer einzelnes Modell (MODEL=name, PROVIDER=key optional)"
	@echo "  make probe-all-thinking   Thinking-Probe fuer alle Cards ohne Probe-Feld (retro-aktiv)"
	@echo ""
	@echo "=== Validation & QA ==="
	@echo "  make validate             Validate test assets"
	@echo "  make validate-single      Validate single asset (ASSET=path)"
	@echo "  make test                 Run tests"
	@echo "  make diff-results         Compare runs"
	@echo "  make analyze-costs        Calculate costs"
	@echo ""
	@echo "=== Tools & Maintenance ==="
	@echo "  make list-models          List Models"
	@echo "  make judge-health         Check Judges"
	@echo "  make list-modules         List Modules"
	@echo "  make audit-markdown       Audit & fix markdown/yaml files"
	@echo "  make web-export           Export data for Web-Frontend"
	@echo "  make web-export-dev       Export data directly into Web repo"
	@echo ""
	@echo "=== Data Management & Cleanup ==="
	@echo "  make backup               Create full backup of runs and assets"
	@echo "  make clean                Remove PyCache and build artifacts"
	@echo "  make clean-csv            Remove standard CSV results"
	@echo "  make clean-model MODEL=x  Remove results for specific model"
	@echo "  make clean-all            Extreme Cleanup (Cache + CSVs)"
	@echo "  make prune-orphans        Verwaiste Reports loeschen (Dry-Run; FORCE=1 zum echten Loeschen)"


# === BENCHMARKING ===

benchmark:
	@echo "Starting Benchmark ($(if $(SILENT),Silent Mode,Standard Audit Mode))..."
	$(PYTHON) run_benchmark.py $(if $(SILENT),--silent,) $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass:
	@echo "Starting standalone Political Compass benchmark (Audit Logs ON)..."
	$(PYTHON) run_benchmark.py --module political_compass $(if $(MODEL),--model "$(MODEL)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass-safe:
	@echo "Starting Anomaly Verification Protocol (Make Political Compass Safe Test)..."
	$(PYTHON) scripts/core/verify_compass_anomalies.py $(if $(MODEL),--model "$(MODEL)" --threshold 0.0)

benchmark-cross-model:
	@echo "Starting Cross-Model Benchmark..."
	@$(PYTHON) scripts/core/run_cross_model_benchmark.py $(if $(MODULE),--module $(MODULE)) $(if $(FORCE),--force)

benchmark-auto:
	@echo "Starting Full Auto Benchmark (Smart Autofill $(if $(SILENT),Silent Mode,with Audit Logs))..."
	$(PYTHON) scripts/core/benchmark_auto.py $(if $(SILENT),--silent,) $(if $(FORCE),--force)

benchmark-human:
	@echo "Starting Human Baseline Test..."
	$(PYTHON) scripts/tools/run_human_compass.py

# === REPORTING & STANDARDS ===

model-cards:
	$(PYTHON) scripts/analysis/generate_model_cards.py $(if $(MODEL),--model "$(MODEL)") $(if $(PROVIDER),--provider "$(PROVIDER)") $(if $(FORCE),--force)

model-card: model-cards

provider-cards:
	@if [ -n "$(PROVIDER)" ]; then \
		echo "Generiere Provider Card fuer $(PROVIDER)..."; \
		$(PYTHON) scripts/analysis/generate_provider_cards.py --provider "$(PROVIDER)" $(if $(FORCE),--force); \
	else \
		echo "Generiere alle fehlenden Provider Cards..."; \
		$(PYTHON) scripts/analysis/generate_provider_cards.py $(if $(FORCE),--force); \
	fi

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
		$(PYTHON) scripts/analysis/generate_review.py --all $(if $(TYPE),--type $(TYPE)); \
	elif [ -n "$(MODEL)" ]; then \
		echo "Generating $(if $(TYPE),$(TYPE),benchmark)-Review for $(MODEL)..."; \
		$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)" $(if $(TYPE),--type $(TYPE)); \
	else \
		echo "Fehler: Bitte gib MODEL=name oder ALL=1 an. Optional: TYPE=bias"; \
		exit 1; \
	fi


reviews-auto:
	@echo "Generiere Reviews fuer alle Modelle (fehlende Cards werden automatisch erstellt)..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto $(if $(FORCE),--force)

reviews-bias-auto:
	@echo "Generiere PC-Bias-Reviews fuer alle Modelle mit 00_bias_report.md..."
	$(PYTHON) scripts/analysis/generate_review.py --all --auto --type bias

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

clean-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "Use: make clean-model MODEL=name"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --model "$(MODEL)"

clean-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "Use: make clean-module MODULE=key"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --module "$(MODULE)"

clean-all:
	@$(PYTHON) scripts/maintenance/clean.py --all

clean-runs:
	@$(PYTHON) scripts/maintenance/clean.py --runs 1 $(if $(FORCE),--force)

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

backup:
	@echo "Creating full backup..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' --exclude='*.bak_*' -czf backups/cruciblemark_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz benchmark_scores/ outputs/ benchmark_modules/ docs/reviews/ docs/audits/ config/ memory-bank/ benchmark_config.yaml
	@echo "Backup created."
	@$(MAKE) clean-runs FORCE=1
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
		echo "No .mcp.pid found — server may not be running."; \
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
	@$(MAKE) mcp-start MODE=$(or $(MCP_MODE),live)
	@sleep 1.5
	$(PYTHON) scripts/run_tooluse_benchmark.py \
		$(if $(MODEL),--model "$(MODEL)") \
		$(if $(ALL),--all) \
		$(if $(PROVIDER),--provider "$(PROVIDER)") \
		$(if $(FORCE),--force) \
		$(if $(SILENT),--silent) \
		--mcp-mode $(or $(MCP_MODE),live)
	@$(MAKE) mcp-stop
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
