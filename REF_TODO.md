# Refactoring & Cleanup Plan (v0.9 -> v1.0 Prep)

## 1. Leaderboard-Skript Robustheit (Completed)
- [x] **Hardcoding entfernen:** Leaderboard verlässt sich jetzt zu 100% auf die `benchmark_config.yaml`.
- [x] **Dynamische Scores:** `Routine Score` und `Reasoning Score` werden anhand von `score_group` in der Config berechnet.
- [x] **Optionalität:** Political Compass läuft als `score_group: info` und blockiert den "Pending" Status nicht.
- [x] **Ausstehend-Logik:** Fehlende PC-Daten werden sauber als "Ausstehend" angezeigt.

## 2. Modul-Architektur (Konzept v1.0)
- [ ] **Interface-Definition:** Runner-Logik umkehren ("Inversion of Control").
    - `get_tasks()`: Modul liefert Aufgaben-Liste an Runner.
    - `execute_task()`: Runner führt einzelne Aufgabe aus (Granulares Resume möglich).
    - `finalize()`: Modul aggregiert Ergebnisse am Ende.
- [ ] **Political Compass Refactoring:** Aufbrechen des monolithischen Loops in Einzel-Tasks, die vom Framework gesteuert werden.
- [x] **Scaffolding Tool:** `scripts/scaffold_module.py` erstellt und in Makefile integriert.

## 3. Module Enhancement
- [ ] **Code Quality "Expertise" aktivieren:** Die Bewertungs-Logik (Evaluator) unterstützen bereits die Kategorie "Expertise", aber die Assets (YAML) nutzen sie noch nicht.
    - Assets (`code_quality/assets/*.yaml`) müssen um `scoring.expertise` Sektionen erweitert werden.
    - Ziel: Bewertung der Erklärungstiefe (Root Cause Analysis) und Didaktik, nicht nur der Lösung.

## 4. Cleanup
- [ ] **Legacy "Tier" entfernen:** Die Spalte `tier` in `local_models_benchmark.csv` (und im `BaseRunner`) ist veraltet, da nun `score_group` genutzt wird. Muss vollständig entfernt werden, sobald keine Legacy-Parser mehr darauf zugreifen.
- [ ] Veraltete Skripte/Logs entfernen.
- [ ] Dieses TODO-File löschen bei Abschluss aller Punkte.
