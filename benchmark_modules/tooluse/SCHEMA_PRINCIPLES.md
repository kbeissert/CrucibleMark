# Tool Use Benchmark — Schema Architecture Principles

**Version:** 3.10.0 (Final)  
**Status:** Binding für zukünftige Asset-Erweiterungen

---

## Core Rule: Separation of Concerns

### In Asset YAML (Judge braucht das):
- `golden_answer` — Referenzantwort
- `must_include` / `must_not_include` — Harte Kriterien
- `red_flags` / `acceptable_patterns` — Beobachtbare Marker
- `acceptable` / `unacceptable` — Verhaltensmuster
- `output_format` — Strukturelle Anforderungen

### NICHT in Asset YAML (gehört in Dokumentation):
- Scoring-Guides (0–3 Punkte-Erklärungen)
- Beispiele oder Case-Studies
- Ausführliche Begründungen
- Interpretationshilfen für Grenzfälle
- Historische oder kontextuelle Hinweise

### Gewichte:
- **ZENTRAL** unter `evaluation.phase2_rubric.weights:`
- **NICHT** pro Dimension wiederholt
- **NICHT** in Scoring-Guides oder Dokumentation erneut definiert

---

## Warum Diese Trennung Critical Ist

1. **SSoT-Integrität:** Asset YAML ist Single Source of Truth für Judge. Alles andere ist Referenz.
2. **Judge-Konsistenz:** Der Judge liest nur die YAML. Keine Umleitungen auf externe Erklärtexte.
3. **Wartbarkeit:** Wenn Scoring-Guides in Asset-YAML zurückwandern, entsteht Redundanz und Drift-Risiko.
4. **tooluse003-Spezial:** Halluzinations-Test braucht **maximale Klarheit ohne Interpretation**. Scoring-Guides würden hier Softness reintroduzieren.

---

## Checkliste für Neue Assets

Bevor ein neues Tool Use Asset hinzugefügt wird:

- [ ] `golden_answer` ist 4–6 Sätze, neutral, konsistent mit Auditor-Standard
- [ ] `weights:` vorhanden mit factuality/hallucination_risk/uncertainty_handling
- [ ] `must_include` / `must_not_include` sind beobachtbar, nicht interpretativ
- [ ] `red_flags` sind konkret (keine "schlechte Qualität" o.ä.)
- [ ] `acceptable_patterns` sind positive Beispiele, nicht Erklärungen
- [ ] `output_format` ist eine Hard Constraint, kein Scoring-Faktor
- [ ] Keine Scoring-Guides, keine Punkt-Erklärungen in der YAML
- [ ] Keine Wiederholung der Gewichte pro Dimension

---

## Versioning

| Version | Date | Change |
|---------|------|--------|
| 3.10.0 | 2026-05-23 | Schema finalized; separation of concerns locked in |

---

## References

- Asset Standard: `benchmark_modules/tooluse/assets/tooluse00{1,2,3}.yaml`
- Judge Documentation: `JUDGE_CHECKLIST.md` (Reference only, not authoritative)
- Scoring Reference: `SCORING_RUBRIC.md` (Reference only, not authoritative)
