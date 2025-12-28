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
	@echo "  make clean                Clean output directories"
	@echo "  make list-models          List models (Local & Commercial Status)"
	@echo ""

install:
	@echo "📦 Installing runtime dependencies..."
	$(PYTHON) -m pip install -r requirements.txt

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
	$(PYTHON) run_benchmark.py --model $(MODEL) $(if $(MODULE),--module $(MODULE),--all)

test-stability:
	@if [ -z "$(MODELS)" ] || [ -z "$(CATEGORY)" ]; then \
		echo "Usage: make test-stability MODELS='ministral-3:8b qwen2.5:14b' CATEGORY=code_quality"; \
		exit 1; \
	fi
	$(PYTHON) scripts/test_stability.py \
		--models $(MODELS) \
		--category $(CATEGORY) \
		--runs 5

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
	$(PYTHON) scripts/interactive_benchmark.py

quick-test:
	$(PYTHON) run_benchmark.py \
		--models qwen2.5:14b \
		--assets benchmark_modules/code_quality/assets/asset_001_wcag_audit.yaml

test-stability:
	@if [ -z "$(MODELS)" ] || [ -z "$(CATEGORY)" ]; then \
		echo "Usage: make test-stability MODELS='ministral-3:8b qwen2.5:14b' CATEGORY=code_quality"; \
		exit 1; \
	fi
	$(PYTHON) scripts/test_stability.py \
		--models $(MODELS) \
		--category $(CATEGORY) \
		--runs 5

# === UTILITIES ===

clean:
	rm -rf benchmark_results/*
	rm -rf outputs/runs/*
	rm -rf outputs/comparisons/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

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
