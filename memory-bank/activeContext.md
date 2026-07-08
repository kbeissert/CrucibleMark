## SESSION START INSTRUCTIONS

On every new session, read these files in this order:
1. `memory-bank/activeContext.md`  — current focus and open questions
2. `memory-bank/progress.md`       — what is done, what is blocked
3. `memory-bank/systemPatterns.md` — architecture, stack, patterns

Do NOT auto-read reference files. Only load a reference file when the current
task explicitly requires it. Check `memory-bank/reference/_index.md`
to know what reference files exist.

---

# Active Context
## Aktueller Status (2026-07-08, v4.10.15, vLLM-Experiment abgeschlossen)

- **vLLM-Experiment beendet:** Alle lokalen Modelle sind auf llama.cpp/GGUF sowohl schneller als auch in den Ergebnissen besser. vLLM wird für lokale Single-User-Modelle nicht weiter verfolgt. vLLM-Code bleibt im Repo (potenzieller Artikel über Ornith-Cross-Backend-Vergleich, evtl. Modelle ohne GGUF in Zukunft).
- **Kritischer Befund (Session 51):** llama.cpp `--reasoning off` unterdrückt Thinking NICHT — das Modell generiert weiterhin Reasoning als Klartext ("Here's a thinking process:..."), das vom Server als `reasoning_content` zurückgegeben wird. 22/50 Ornith-Tasks (44%) haben think_content trotz `enable_thinking: false`. vLLM mit `enable_thinking: false` (Chat-Template-Variable) unterdrückt Thinking korrekt (0/49 Tasks). Der Score-Unterschied (llama.cpp 76.3% vs vLLM 73.85%) ist vollständig durch leaked Thinking erklärt, NICHT durch Quantisierungsqualität — ohne Thinking sind beide nahezu identisch (75.39% vs 75.55%).
- **Ornith vLLM-Ergebnis (73.85%) bleibt im Leaderboard** — als Thinking-OFF-Referenz und potenzieller Artikel-Inhalt. Keine Weiterverfolgung, keine Optimierung.
- **Entscheidung:** Benchmark soll reale Nutzer-Erlebnisse abbilden, nicht künstliche Fairness. llama.cpp's leaked Thinking IST die Realität für Single-User — nicht "reparieren".
- **Nächster Schritt:** Working Tree committen (Session-50 + Session-51 Code, v4.10.15-Bump). Thematische Aufteilung, nur auf explizite Anfrage.
- **Offen/Risiko:** Working Tree uncommitted (Session-50-Code + v4.10.15-Bump + pre-existing qwopus-Deletions/Gemma-Card-Edits). vLLM-TOML-Änderung auf GX10 (nicht im Git).
