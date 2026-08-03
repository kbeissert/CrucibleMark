---
name: Tool Use Schema — Finalisiert v3.11.0, Separation of Concerns
description: Schema-Architektur ist finalisiert und kalibriert. YAML ist SSoT, Scoring-Guides gehören nicht in Assets. Kalibrierungsergebnisse bestätigen Stabilität.
type: feedback
originSessionId: b9258989-bd9b-4649-9011-4094a5265c62
---
## Das Schema ist finalisiert. Gilt jetzt als strukturelles Dogma für die Projekttöne.

**Why:** Separation of Concerns ist critical, weil:
1. Judge liest nur Asset YAML — Alles andere ist Rauschen
2. Scoring-Guides in Assets reintroduzieren Interpretationsspielraum
3. tooluse003 (Halluzinations-Test) braucht maximale Klarheit, keine Weichheit
4. SSoT-Integrität sichert langfristige Wartbarkeit

**How to apply:** 
- Asset YAMLs enthalten NUR: golden_answer, must_include/must_not_include, red_flags, acceptable/unacceptable, output_format
- Gewichte sind zentral unter `weights:`, nicht pro Dimension
- Scoring-Guides, Case-Studies, Beispiele → JUDGE_CHECKLIST.md oder SCORING_RUBRIC.md, nicht in Assets
- Bei neuen Tool Use Assets: SCHEMA_PRINCIPLES.md Checkliste durchlaufen vor dem Commit

**Non-negotiable für tooluse003:** Null-Toleranz für Halluzinationen ist im Schema hart codiert. Keine weichen Scoring-Guides die das untergraben.
