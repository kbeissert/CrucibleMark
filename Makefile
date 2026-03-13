.PHONY: help install validate generate-golden run-benchmark clean test backup

# Python-Interpreter aus .venv verwenden
PYTHON := .venv/bin/python

help:
	@echo "CrucibleMark - Makefile Commands"
	@echo ""
	@echo "=== Installation ==="
	@echo "  make install              Install runtime dependencies (User)"
	@echo "  make install-dev          Install dev dependencies (Developer)"
	@echo ""
	@echo "=== Benchmarking ==="
	@echo "  make benchmark            Interactive OR Single Model (MODEL=name [MODULE=name])"
	@echo "  make benchmark-audit      🕵️ Interactive Audit Mode (Log Prompts & Judges)"
	@echo "  make benchmark-auto       🤖 Auto-Fill Mode: Supplement missing benchmarks"
	@echo "  make benchmark-cross-model Single Module vs ALL LLMs (MODULE=name)"
	@echo "  make benchmark-human      👤 Human Baseline Test (Political Compass)"
	@echo ""
	@echo "=== Reporting & Standards ==="
	@echo "  make leaderboard          Generate Leaderboard CSV"
	@echo "  make bias-report          📊 Update Bias Sensitivity Report"
	@echo "  make generate-golden      Generate golden standard (ASSET=path)"
	@echo ""
	@echo "=== Validation & QA ==="
	@echo "  make validate             Validate all test assets"
	@echo "  make validate-single      Validate single asset (ASSET=path)"
	@echo "  make validate-structure   Check module directory structure"
	@echo "  make test                 Run validation & unit tests"
	@echo "  make diff-results         Compare two benchmark JSONs"
	@echo "  make analyze-costs        Calculate token costs"
	@echo ""
	@echo "=== Tools & Maintenance ==="
	@echo "  make list-models          List available Models"
	@echo "  make judge-health         Check LLM Judge provider status [PROVIDER=name]"
	@echo "  make list-modules         List available Modules"
	@echo "  make create-module        🚀 Scaffold a new module"
	@echo "  make update-prices        💱 Force-update LiteLLM token price cache"
	@echo "  make clean                Clean caches/temp files"
	@echo "  make clean-all            Deep Clean (Caches + CSVs)"
	@echo "  make backup               Create full backup"
	@echo ""

# === INSTALLATION ===

install:
	@echo "📦 Installing dependencies..."
	$(PYTHON) scripts/dev/setup_env.py

install-dev: install
	@echo "🛠️ Installing development dependencies..."
	$(PYTHON) -m pip install -r requirements-dev.txt

# === BENCHMARKING ===

benchmark:
	@echo "🚀 Starting Benchmark..."
	$(PYTHON) run_benchmark.py $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(filter true,$(FORCE)),--force)
	@$(MAKE) leaderboard

benchmark-audit:
	@echo "🕵️  Starting Benchmark (Audit Mode)..."
	$(PYTHON) run_benchmark.py --audit $(if $(MODEL),--model "$(MODEL)") $(if $(MODULE),--module "$(MODULE)") $(if $(filter true,$(FORCE)),--force)
	@$(MAKE) leaderboard

benchmark-dev:
	@echo "🚀 Starting Interactive Benchmark (Dev Mode - Fast Iteration)..."
	$(PYTHON) run_benchmark.py --dev
	@$(MAKE) leaderboard

benchmark-cross-model:
	@echo "🚀 Starting Cross-Model Benchmark..."
	@$(PYTHON) scripts/core/run_cross_model_benchmark.py $(if $(MODULE),--module $(MODULE))

benchmark-auto:
	@echo "🤖 Starting Full Auto Benchmark (Smart Autofill)..."
	$(PYTHON) scripts/core/benchmark_auto.py

benchmark-human:
	@echo "👤 Starting Human Baseline Test..."
	$(PYTHON) scripts/tools/run_human_compass.py

run-benchmark:
	$(PYTHON) run_benchmark.py

# === REPORTING & STANDARDS ===

review-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Fehler: Gib ein Modell an. Beispiel: make review-model MODEL=claude-haiku-4-5-20251001"; \
		exit 1; \
	fi
	@echo "📰 Generating Review for $(MODEL)..."
	$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)"

review-all:
	@echo "📰 Generating Reviews for ALL models..."
	$(PYTHON) scripts/analysis/generate_review.py --all

leaderboard:
	@echo "📊 Generating Leaderboard..."
	$(PYTHON) scripts/core/generate_leaderboard.py

bias-report:
	@echo "📊 Updating Bias Sensitivity Report..."
	$(PYTHON) scripts/analysis/update_bias_report.py

generate-golden:
	@echo "🏆 Generating Golden Standards (missing only)..."
	$(PYTHON) scripts/core/run_commercial_benchmark.py --mode golden_standard --auto

generate-golden-new:
	@echo "🏆 Generating Golden Standards (FORCE UPDATE)..."
	$(PYTHON) scripts/core/run_commercial_benchmark.py --mode golden_standard --auto --force

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
	@$(PYTHON) scripts/analysis/compare_baselines.py --help

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

clean:
	@echo "🧹 Cleaning caches and temporary files..."
	rm -rf outputs/runs/*
	rm -rf outputs/comparisons/*
	rm -rf outputs/audit_logs/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-sessions:
	@echo "🧹 Cleaning temporary benchmark sessions..."
	@rm -rf outputs/temp/session_*.json

clean-csv:
	@echo "🗑️  Deleting ALL benchmark CSV files..."
	rm -f benchmark_scores/*.csv

clean-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Use: make clean-model MODEL=name"; \
		exit 1; \
	fi
	@echo "🧹 Deleting results for model: $(MODEL)"
	$(PYTHON) scripts/maintenance/clean_results.py --model "$(MODEL)"

clean-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Use: make clean-module MODULE=key"; \
		exit 1; \
	fi
	@echo "🧹 Deleting results for module: $(MODULE)"
	$(PYTHON) scripts/maintenance/clean_results.py --module "$(MODULE)"

clean-all: clean clean-csv
	@echo "✨ All clean!"

clean-runs:
	@if [ -f "scripts/maintenance/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/maintenance/cleanup_runs.py --keep 1; \
	fi

clean-runs-force:
	@if [ -f "scripts/maintenance/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/maintenance/cleanup_runs.py --keep 1 --force; \
	fi

consolidate-csv:
	@if [ -f "scripts/maintenance/consolidate_csv.py" ]; then \
		$(PYTHON) scripts/maintenance/consolidate_csv.py; \
	fi

backup:
	@echo "💾 Creating full backup..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' -czf backups/cruciblemark_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz benchmark_scores/ outputs/ benchmark_modules/ golden_standards/
	@echo "✅ Backup created."
	@$(MAKE) clean-runs-force
	@$(MAKE) consolidate-csv
	@echo "✨ Backup chain complete."
