with open('Makefile', 'r', encoding='utf-8') as f:
    data = f.read()

# Fix help text
data = data.replace(
    '  make political-compass    🐺 Eigenständiger PC-Test (immer mit Audit, Flags: FORCE)',
    '  make political-compass    🐺 Eigenständiger PC-Test (immer mit Audit, Opt. Flags: FORCE=1)'
)

data = data.replace(
    '  make political-compass-safe 🛡️  Anomalieprüfung (Triple-Run)',
    '  make political-compass-safe 🛡️  Sicherheits-/Anomalieprüfung (Triple-Run erzwingen)'
)

# Fix actual commands
data = data.replace(
    '$(PYTHON) run_benchmark.py --module political_compass --audit --force $(if $(MODEL),--model "$(MODEL)")',
    '$(PYTHON) run_benchmark.py --module political_compass --audit $(if $(MODEL),--model "$(MODEL)") $(if $(FORCE),--force)'
)

# Also fix verify_compass_anomalies to ensure threshold 0.0 is used if model is passed
data = data.replace(
    '$(PYTHON) scripts/core/verify_compass_anomalies.py $(if $(MODEL),--model "$(MODEL)")',
    '$(PYTHON) scripts/core/verify_compass_anomalies.py $(if $(MODEL),--model "$(MODEL)" --threshold 0.0)'
)

with open('Makefile', 'w', encoding='utf-8') as f:
    f.write(data)
