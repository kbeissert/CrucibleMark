# Active Context

## Was wurde heute fertiggestellt?
- Ein robuster Audit-Log-Modus (`make benchmark-audit`) wurde implementiert, der alle Interaktionen (inklusive dem final evaluierten Prompt und der vollständigen LLM-Judge Reasoning-Historie) als Markdown in `outputs/audit_logs/` speichert.
- Die Daten-Übergabe (`BenchmarkResult`) aus den Evaluatoren in die Core-Treiberschicht wurde überarbeitet, um die präzisen Prompts und Regex-Subkategorien für den Audit-Log durchzuschleifen.
- Umfassende Dokumentation zum Audit-Mode in `USER_GUIDE.md` und `README.md` integriert.

## Was ist der nächste logische Schritt?
- Volldurchlauf aller lokalen Modelle starten, um das finale Leaderboard mit den kompletten Judge-Daten und Regex-Kategorien zu befüllen und die Stabilität in einem Langzeit-Lauf (Overnight) abzusichern.
- Umsetzung des **Batch-Mode** (Phase 3.5), da das per-task Loading (~40s Overhead pro Task bei 9GB Judge-Modellen) nach wie vor extrem teuer ist.

## Welche offenen Fragen oder Risiken gibt es?
- **LLM Judge Latency:** Jeder Task-Wechsel, der den LLM-Judge anstößt, triggert auf lokalen Systemen das In-Memory-Loading, was den Test-Lauf künstlich in die Länge zieht, bis Model-Batching implementiert ist.
- Risiko von Datenverlust bei OOM-Kills durch Ollama bei zu kleinen RAM-Limits, das durch das neue `PendingJudgeResult`-Safety-Net abgefangen werden sollte, aber im Dauerbetrieb noch validiert werden muss.
