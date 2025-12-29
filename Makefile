.PHONY: help install validate generate-golden run-benchmark clean test

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
	@echo "  make benchmark-auto       Automatisierter Run (MODEL=name [MODULE=name])"
	@echo "  make leaderboard          Generiere Leaderboard-CSV aus Ergebnissen"
	@echo ""
	@echo "=== Golden Standards ==="
	@echo "  make generate-golden      Generate golden standard (ASSET=path)"
	@echo ""
	@echo "=== Validation & Testing ==="
	@echo "  make validate             Validate all test assets"
	@echo "  make validate-single      Validate single asset (ASSET=path)"
	@echo "  make test                 Run validation & unit tests"
	@echo ""
	@echo "=== Utilities ==="
	@echo "  make clean                Clean caches and temporary outputs"
	@echo "  make clean-csv            Delete all benchmark CSV files"
	@echo "  make clean-all            Delete EVERYTHING (caches + CSVs)"
	@echo "  make list-models          List models (Local & Commercial Status)"
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

benchmark-auto:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Error: MODEL variable not set"; \
		echo "Usage: make benchmark-auto MODEL=qwen2.5:14b [MODULE=code_quality]"; \
		exit 1; \
	fi
	@echo "🤖 Starte automatisierten Benchmark mit Modell: $(MODEL)..."
	$(PYTHON) run_benchmark.py --model $(MODEL) $(if $(MODULE),--module $(MODULE))

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

clean-csv:
	@echo "🗑️  Deleting benchmark CSV files..."
	rm -f benchmark_scores/commercial_models_benchmark.csv
	rm -f benchmark_scores/local_models_benchmark.csv
	rm -f benchmark_scores/golden_standard_benchmark.csv
	rm -f benchmark_scores/benchmark_leaderboard.csv

clean-all: clean clean-csv
	@echo "✨ All clean! (Caches and CSVs deleted)"

clean-runs:
	@if [ -f "scripts/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/cleanup_runs.py --keep 5; \
	else \
		echo "⚠️  cleanup_runs.py nicht gefunden"; \
	fi

clean-runs-force:
	@if [ -f "scripts/cleanup_runs.py" ]; then \
		$(PYTHON) scripts/cleanup_runs.py --keep 5 --force; \
	else \
		echo "⚠️  cleanup_runs.py nicht gefunden"; \
	fi

list-models:
	$(PYTHON) scripts/list_models.py

test: validate
	@echo "🧪 Running Unit Tests..."
	$(PYTHON) -m pytest benchmark_modules/
