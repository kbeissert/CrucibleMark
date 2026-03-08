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
- Parser-Fallback (`_strip_thinking_tags`): Darf auf keinen Fall an `implicit_separator` (z.B. "**Answer:**") abschneiden, da dies korrekte Modellantworten der Tier 1/2 Reasoning-Tests fälschlicherweise nullt. Nur explizite XML-Tags entfernen.
- **Leaderboard Missing Tests (`*` Bug):** Wenn Tests eines Moduls nicht gezählt werden, fehlt das `prefix: "<name>"` im Feld `metadata` der `config.yaml`. Ohne dies filtert der `score_calculator` die Tests als "Other" heraus.
- **Asset Schema Violation:** Jede YAML-Aufgabe muss zwingend ein `prompt` (oder `prompts`) Feld haben, selbst wenn es vom Modul ignoriert wird, da ansonsten der Basis-`AssetValidator` abbricht.

## Patterns (gelernt)

<!-- KI trägt hier erfolgreiche Lösungsmuster ein -->

- Konfig-Hierarchie: Global (`benchmark_config`) → Modul (`config.yaml`) → Runtime. Modul-Config überschreibt Global.
- **Test-Architektur:** Neue Module (wie das `cli_benchmark`) müssen in Python zwingend von `BaseTest` erben und in `execute()` stets **einzelne** Aufgaben verarbeiten. Modul-interne Batch-Schleifen zerstören das allgemeine Leaderboard-Reporting.
