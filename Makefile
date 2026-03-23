.PHONY: \
	help install install-dev \
	benchmark political-compass political-compass-safe benchmark-political-compass audit-bias benchmark-cross-model benchmark-auto benchmark-human run-benchmark \
	review leaderboard \
	validate validate-single validate-structure test diff-results analyze-costs update-prices \
	list-models judge-health list-modules create-module \
	clean clean-sessions clean-csv clean-model clean-module clean-all clean-runs consolidate-csv \
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
	@echo "  make benchmark            🕵️ Standard Benchmark (Flags: SILENT, FORCE, MODEL, MODULE)"
	@echo "  make benchmark-auto       🤖 Auto-Fill Benchmark (Flags: SILENT, FORCE)"
	@echo "  make benchmark-cross-model 🚀 Module vs ALL LLMs (Flags: FORCE, MODULE)"
	@echo "  make run-benchmark        Interactive Runner"
	@echo ""
	@echo "=== Political Compass ==="
	@echo "  make political-compass    🐺 Eigenständiger PC-Test (immer mit Audit, Opt. Flags: FORCE=1)"
	@echo "  make political-compass-safe 🛡️  Sicherheits-/Anomalieprüfung (Triple-Run erzwingen)"
	@echo "  make benchmark-human      👤 Human Baseline Test (PC)"
	@echo ""
	@echo "=== Reporting & Standards ==="
	@echo "  make leaderboard          Generate Leaderboard CSV"
	@echo "  make review               📰 Generate Review (Flags: MODEL=name, ALL=1, TYPE=bias)"
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
	@echo "  make create-module        🚀 Scaffold module"
	@echo "  make audit-markdown       📝 Audit & fix markdown/yaml files"
	@echo ""
	@echo "=== Data Management & Cleanup ==="
	@echo "  make backup               📦 Create full backup of runs and assets"
	@echo "  make clean                🧹 Remove PyCache and build artifacts"
	@echo "  make clean-csv            🗑️  Remove standard CSV results"
	@echo "  make clean-sessions       🗑️  Remove debug session logs"
	@echo "  make clean-model MODEL=x  🗑️  Remove results for specific model"
	@echo "  make clean-all            🔥 Extreme Cleanup (Cache + CSVs)"


# === BENCHMARKING ===

benchmark:
	@echo "🕵️  Starting Benchmark ($(if $(SILENT),Silent Mode,Standard Audit Mode))..."
	$(PYTHON) run_benchmark.py $(if $(SILENT),,--audit) $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass:
	@echo "🐺 Starting standalone Political Compass benchmark (Audit Logs ON)..."
	$(PYTHON) run_benchmark.py --module political_compass --audit $(if $(MODEL),--model "$(MODEL)") $(if $(FORCE),--force)
	@$(MAKE) leaderboard

political-compass-safe:
	@echo "🛡️  Starting Anomaly Verification Protocol (Make Political Compass Safe Test)..."
	$(PYTHON) scripts/core/verify_compass_anomalies.py $(if $(MODEL),--model "$(MODEL)" --threshold 0.0)

benchmark-political-compass:
	@echo "⚠️  Deprecated alias: forwarding to political-compass"
	@$(MAKE) political-compass MODEL="$(MODEL)" FORCE="$(FORCE)"

audit-bias:
	@echo "⚠️  Deprecated alias: forwarding to political-compass"
	@$(MAKE) political-compass MODEL="$(MODEL)" FORCE="$(FORCE)"

benchmark-cross-model:
	@echo "🚀 Starting Cross-Model Benchmark (with Audit Logs)..."
	@$(PYTHON) scripts/core/run_cross_model_benchmark.py --audit $(if $(MODULE),--module $(MODULE)) $(if $(FORCE),--force)

benchmark-auto:
	@echo "🤖 Starting Full Auto Benchmark (Smart Autofill $(if $(SILENT),Silent Mode,with Audit Logs))..."
	$(PYTHON) scripts/core/benchmark_auto.py $(if $(SILENT),,--audit) $(if $(FORCE),--force)

benchmark-human:
	@echo "👤 Starting Human Baseline Test..."
	$(PYTHON) scripts/tools/run_human_compass.py

run-benchmark:
	$(PYTHON) run_benchmark.py

# === REPORTING & STANDARDS ===

review:
	@if [ -n "$(ALL)" ]; then \
		echo "📰 Generating $(if $(TYPE),$(TYPE),benchmark)-Reviews for ALL models..."; \
		$(PYTHON) scripts/analysis/generate_review.py --all $(if $(TYPE),--type $(TYPE)); \
	elif [ -n "$(MODEL)" ]; then \
		echo "📰 Generating $(if $(TYPE),$(TYPE),benchmark)-Review for $(MODEL)..."; \
		$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)" $(if $(TYPE),--type $(TYPE)); \
	else \
		echo "❌ Fehler: Bitte gib MODEL=name oder ALL=1 an. Optional: TYPE=bias"; \
		exit 1; \
	fi


leaderboard:
	@echo "📊 Generating Leaderboard..."
	$(PYTHON) scripts/core/generate_leaderboard.py

# === VALIDATION & QA ===

validate:
	@echo "🔍 Validating all modules..."
	$(PYTHON) scripts/tools/validate_assets.py --all

validate-single:
	@if [ -z "$(ASSET)" ]; then \
		echo "Error: ASSET variable not set"; \
		exit 1; \
	fi
	$(PYTHON) scripts/tools/validate_assets.py $(ASSET)

validate-structure:
	@echo "🏗️ Checking Module Structure..."
	$(PYTHON) scripts/tools/validate_structure.py

test: validate
	@echo "🧪 Running Unit Tests..."
	$(PYTHON) -m pytest benchmark_modules/ utils/scoring/llm_judge/tests/ -v --tb=short

diff-results:
	@echo "⚖️ Comparing Benchmark Results..."
	$(PYTHON) scripts/analysis/compare_baselines.py $(if $(REF),--ref $(REF)) $(if $(TEST),--test $(TEST)) $(if $(THRESH),--threshold $(THRESH))

analyze-costs:
	@echo "💰 Analyzing Prompt Token Costs..."
	$(PYTHON) -c "from utils.pricing_updater import PricingUpdater; p=PricingUpdater(); p.ensure_fresh(); print(p.get_status_line())"
	$(PYTHON) scripts/analysis/analyze_prompts.py

update-prices:
	@echo "💱 Updating token pricing cache from LiteLLM Pricing DB..."
	$(PYTHON) scripts/dev/update_prices.py

# === TOOLS & MAINTENANCE ===

list-models:
	@$(PYTHON) scripts/tools/list_models.py

judge-health:
	@echo "🩺 Checking LLM Judge provider connectivity..."
	$(PYTHON) scripts/tools/judge_health.py $(if $(PROVIDER),--provider $(PROVIDER))

list-modules:
	@echo "📋 Available Modules:"
	@if [ -f "scripts/tools/list_modules.py" ]; then \
		$(PYTHON) scripts/tools/list_modules.py; \
	else \
		$(PYTHON) -c "import yaml; config=yaml.safe_load(open('benchmark_config.yaml')); [print(f'  {i+1}. {k}: {v[\"name\"]}') for i, (k,v) in enumerate(config.get('modules', {}).items()) if v.get('enabled', True)]"; \
	fi

create-module:
	@$(PYTHON) scripts/dev/scaffold_module.py

audit-markdown:
	@echo "📝 Running Markdown & YAML Audit..."
	@$(PYTHON) scripts/maintenance/audit_markdown.py $(if $(FIX),--fix)

clean:
	@if [ -n "$(MODEL)" ] || [ -n "$(MODULE)" ] || [ -n "$(ALL)" ]; then \
		$(PYTHON) scripts/maintenance/clean.py $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(ALL),--all); \
	else \
		$(PYTHON) scripts/maintenance/clean.py --cache; \
	fi

clean-sessions:
	@$(PYTHON) scripts/maintenance/clean.py --sessions

clean-csv:
	@$(PYTHON) scripts/maintenance/clean.py --csv

clean-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Use: make clean-model MODEL=name"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --model "$(MODEL)"

clean-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Use: make clean-module MODULE=key"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/maintenance/clean.py --module "$(MODULE)"

clean-all:
	@$(PYTHON) scripts/maintenance/clean.py --all

clean-runs:
	@$(PYTHON) scripts/maintenance/clean.py --runs 1 $(if $(FORCE),--force)

clean-wizard:
	@$(PYTHON) scripts/maintenance/clean.py --interactive

consolidate-csv:
	@if [ -f "scripts/maintenance/consolidate_csv.py" ]; then \
		$(PYTHON) scripts/maintenance/consolidate_csv.py; \
	fi

backup:
	@echo "💾 Creating full backup..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' -czf backups/cruciblemark_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz benchmark_scores/ outputs/ benchmark_modules/
	@echo "✅ Backup created."
	@$(MAKE) clean-runs FORCE=1
	@$(MAKE) consolidate-csv
	@echo "✨ Backup chain complete."
