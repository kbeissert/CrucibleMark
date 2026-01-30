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
	@echo "=== Benchmarking (Neue modulare Struktur) ==="
	@echo "  make benchmark            Interaktiver Benchmark (Wizard)"
	@echo "  make list-models          List available Local & Commercial models (with Connectivity Check)"
	@echo "  make benchmark-auto       🤖 Auto-Fill Mode: Ergänzt fehlende Benchmarks"
	@echo "  make benchmark-single     Einzelnes Modell (MODEL=name [MODULE=name])"
	@echo "  make leaderboard          Generiere Leaderboard-CSV aus Ergebnissen"
	@echo "  make clean-sessions       🗑️  Lösche temporäre Checkpoints (Political Compass)"
	@echo ""
	@echo "=== Golden Standards ==="
	@echo "  make generate-golden      Generate golden standard (ASSET=path)"
	@echo ""
	@echo "=== Validation & Testing ==="
	@echo "  make validate             Validate all test assets"
	@echo "  make validate-single      Validate single asset (ASSET=path)"
	@echo "  make validate-structure   Check module directory structure compliance (Clean Architecture)"
	@echo "  make test                 Run validation & unit tests"
	@echo "  make analyze-costs        Calculate estimated token costs for all assets"
	@echo "  make diff-results         Compare two benchmark JSONs (Regression Testing)"
	@echo ""
	@echo "=== Utilities ==="
	@echo "  make clean                Clean caches and temporary outputs"
	@echo "  make clean-csv            Delete all benchmark CSV files"
	@echo "  make clean-all            Delete EVERYTHING (caches + CSVs)"
	@echo "  make list-models          List models (Local & Commercial Status)"
	@echo "  make list-modules         List available benchmark modules"
	@echo "  make create-module        🚀 Scaffold a new benchmark module (Interactive)"
	@echo "  make backup               Backup benchmark scores to backups/"
	@echo ""

install:
	@echo "📦 Installing dependencies (Smart Setup)..."
	$(PYTHON) scripts/setup_env.py

install-dev: install
	@echo "🛠️ Installing development dependencies..."
	$(PYTHON) -m pip install -r requirements-dev.txt

# === NEUE MODULARE BENCHMARK-COMMANDS ===

benchmark:
	@echo "🚀 Starte interaktiven Benchmark..."
	$(PYTHON) run_benchmark.py

benchmark-single:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Error: MODEL variable not set"; \
		echo "Usage: make benchmark-single MODEL=qwen2.5:14b [MODULE=code_quality]"; \
		exit 1; \
	fi
	@echo "🤖 Starte automatisierten Benchmark mit Modell: $(MODEL)..."
	$(PYTHON) run_benchmark.py --model $(MODEL) $(if $(MODULE),--module $(MODULE))

benchmark-auto:
	@echo "🌙 Starte Full Auto Benchmark (Overnight Mode)..."
	@echo "   Führt ALLE Module auf ALLEN Modellen aus."
	$(PYTHON) scripts/benchmark_auto.py

leaderboard:
	@echo "📊 Generiere Leaderboard..."
	$(PYTHON) scripts/generate_leaderboard.py

# === VALIDATION ===

validate:
	@echo "🔍 Validiere alle Module aus benchmark_config.yaml..."
	$(PYTHON) scripts/validate_assets.py --all

validate-single:
	@if [ -z "$(ASSET)" ]; then \
		echo "Error: ASSET variable not set"; \
		echo "Usage: make validate-single ASSET=benchmark_modules/code_quality/assets/asset_001_wcag_audit.yaml"; \
		exit 1; \
	fi
	$(PYTHON) scripts/validate_assets.py $(ASSET)

generate-golden:
	@echo "🏆 Generiere Golden Standard für alle Module (nur fehlende)..."
	$(PYTHON) scripts/run_commercial_benchmark.py --mode golden_standard --auto

generate-golden-new:
	@echo "🏆 Generiere Golden Standard für alle Module (FORCE UPDATE)..."
	$(PYTHON) scripts/run_commercial_benchmark.py --mode golden_standard --auto --force

run-benchmark:
	$(PYTHON) run_benchmark.py

# === UTILITIES ===

clean:
	@echo "🧹 Cleaning caches and temporary files..."
	rm -rf outputs/runs/*
	rm -rf outputs/comparisons/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-sessions:
	@echo "🧹 Cleaning temporary benchmark sessions (Checkpoints)..."
	@rm -rf outputs/temp/session_*.json
	@echo "Done."

clean-csv:
	@echo "🗑️  Deleting ALL benchmark CSV files..."
	rm -f benchmark_scores/*.csv

clean-all: clean clean-csv
	@echo "✨ All clean! (Caches and CSVs deleted)"

clean-runs:
	@if [ -f "scripts/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/cleanup_runs.py --keep 1; \
	else \
		echo "⚠️  cleanup_runs.py nicht gefunden"; \
	fi

clean-runs-force:
	@if [ -f "scripts/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/cleanup_runs.py --keep 1 --force; \
	else \
		echo "⚠️  cleanup_runs.py nicht gefunden"; \
	fi

list-modules:
	@echo "📋 Available Modules (Ordered by Config):"
	@if [ -f "scripts/list_modules.py" ]; then \
		$(PYTHON) scripts/list_modules.py; \
	else \
		$(PYTHON) -c "import yaml; config=yaml.safe_load(open('benchmark_config.yaml')); [print(f'  {i+1}. {k}: {v[\"name\"]}') for i, (k,v) in enumerate(config.get('modules', {}).items()) if v.get('enabled', True)]"; \
	fi

test: validate
	@echo "🧪 Running Unit Tests..."
	$(PYTHON) -m pytest benchmark_modules/

list-models:
	@$(PYTHON) scripts/list_models.py

# === UTILITIES & VALIDATION ===

validate-structure:
	@echo "🏗️ Checking Module Structure..."
	$(PYTHON) scripts/validate_structure.py

# === DEVELOPMENT ===

create-module:
	@$(PYTHON) scripts/scaffold_module.py

analyze-costs:
	@echo "💰 Analyzing Prompt Token Costs..."
	$(PYTHON) scripts/analyze_prompts.py

diff-results:
	@echo "⚖️ Comparing Benchmark Results..."
	@echo "Usage: $(PYTHON) scripts/compare_baselines.py --ref REF.json --test TEST.json"
	@$(PYTHON) scripts/compare_baselines.py --help

# === BACKUP ===

consolidate-csv:
	@if [ -f "scripts/consolidate_csv.py" ]; then \
		$(PYTHON) scripts/consolidate_csv.py; \
	else \
		echo "⚠️  scripts/consolidate_csv.py nicht gefunden"; \
	fi

backup:
	@echo "💾 Creating full backup (scores, outputs, modules, standards)..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' -czf backups/cruciblemark_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		benchmark_scores/ \
		outputs/ \
		benchmark_modules/ \
		golden_standards/
	@echo "✅ Backup created in backups/"
	@echo "🧹 Post-Backup Cleanup Phase 1: Cleaning old JSON logs..."
	@$(MAKE) clean-runs-force
	@echo "🧹 Post-Backup Cleanup Phase 2: Consolidating CSV scores (Keep Latest)..."
	@$(MAKE) consolidate-csv
	@echo "✨ Backup chain complete (Archived + Cleaned + Consolidated)."
