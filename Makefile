.PHONY: help install validate generate-golden run-benchmark clean test

# Python-Interpreter aus .venv verwenden
PYTHON := .venv/bin/python

help:
	@echo "CrucibleMark - Makefile Commands"
	@echo ""
	@echo "=== Installation ==="
	@echo "  make install              Install Python dependencies"
	@echo ""
	@echo "=== Benchmarking (Neue modulare Struktur) ==="
	@echo "  make benchmark            Interaktiver Benchmark (Modul + Provider wählen)"
	@echo "  make benchmark-local      Lokale Modelle (Ollama)"
	@echo "  make benchmark-commercial Kommerzielle Modelle (Mistral/Claude/GPT)"
	@echo "  make benchmark-module     Spezifisches Modul (MODULE=code_quality)"
	@echo ""
	@echo "=== Golden Standards ==="
	@echo "  make generate-golden      Generate golden standard (ASSET=path)"
	@echo ""
	@echo "=== Validation ==="
	@echo "  make validate             Validate all test assets"
	@echo "  make validate-single      Validate single asset (ASSET=path)"
	@echo ""
	@echo "=== Utilities ==="
	@echo "  make clean                Clean output directories"
	@echo "  make list-models          List available Ollama models"
	@echo "  make test                 Run validation tests"
	@echo ""

install:
	$(PYTHON) -m pip install -r requirements.txt

# === NEUE MODULARE BENCHMARK-COMMANDS ===

benchmark:
	@echo "🚀 Starte interaktiven Benchmark..."
	$(PYTHON) run_benchmark.py

benchmark-local:
	@echo "🖥️  Starte lokalen Benchmark (Ollama)..."
	$(PYTHON) run_benchmark.py --provider local

benchmark-commercial:
	@echo "🌐 Starte kommerziellen Benchmark..."
	$(PYTHON) run_benchmark.py --provider commercial

benchmark-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Error: MODULE variable not set"; \
		echo "Usage: make benchmark-module MODULE=code_quality"; \
		exit 1; \
	fi
	@echo "📦 Starte Benchmark für Modul: $(MODULE)..."
	$(PYTHON) run_benchmark.py --module $(MODULE)

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
	$(PYTHON) scripts/validate_assets.py test_modules/test_assets/

validate-single:
	@if [ -z "$(ASSET)" ]; then \
		echo "Error: ASSET variable not set"; \
		echo "Usage: make validate-single ASSET=test_modules/test_assets/code_quality/asset_001_wcag_audit.yaml"; \
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
	$(PYTHON) scripts/run_benchmark.py \
		--models qwen2.5:14b \
		--assets test_modules/test_assets/code_quality/asset_001_wcag_audit.yaml

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
	@echo "Available Ollama models:"
	@ollama list

test: validate
	@echo "✓ All tests passed"
