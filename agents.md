# AGENTS.md

## Stack
- Python 3.12, venv (nie global)
- pytest mit `-v --tb=short`
- Typen immer annotieren (mypy-kompatibel)

## Verbotenes
- Keine `print()` für Debugging → `logging.debug()`
- Keine bare `except:` → immer spezifischer Exception-Typ

## Bekannte Fallstricke
<!-- KI trägt hier ein, was schief gelaufen ist -->
- Code-Modelle (z.B. Hermes) neigen bei Tabellen zu Loops → `repeat_penalty` erhöhen (1.15).
- Doppelte Argumente in `kwargs`: Parameter explizit mit `.pop()` entfernen, bevor sie an den Client weitergereicht werden.

## Patterns (gelernt)
<!-- KI trägt hier erfolgreiche Lösungsmuster ein -->
- Konfig-Hierarchie: Global (`benchmark_config`) → Modul (`config.yaml`) → Runtime. Modul-Config überschreibt Global.
