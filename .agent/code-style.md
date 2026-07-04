# Code Style

Python-Konventionen für CrucibleMark (Python 3.12).

## Sprach-Stack

- **Python 3.12**, venv (nie global).
- Type hints in ALLEN neuen Funktionen (mypy-kompatibel).

## Verbote

- **Kein `print()` für Debugging** → `logging.debug()`.
- **Kein bare `except:`** — Exception-Typ immer angeben.
- **Keine Provider-Namen hardcoden** → aus `benchmark_config.yaml` lesen.

## Konventionen

- Bestehende Pytest-Fixtures wiederverwenden, keine Duplikate.
- Keine neuen Dependencies ohne Rückfrage — `requirements.txt` ist bewusst schlank.
- Modulnamen konsistent mit bestehender Verzeichnisstruktur.

## Plugin-Laden

- **Namespace-Kollision:** Bei `importlib` mit gleichnamigen Plugin-Dateien `{parent.name}_{stem}` verwenden.
