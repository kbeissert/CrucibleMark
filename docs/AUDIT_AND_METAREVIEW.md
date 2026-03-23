# CrucibleMark: Audit-Logs & Meta-Review Workflow

Aus einem ursprünglichen Dev-Tool, das Protokolle primär generierte, um Systemfehler zu suchen, ist ein zentrales visuelles und analytisches Feature geworden. Die Audit-Logs bieten nun ein eindeutiges, transparentes Verständnis der Benchmarks von der Eingabe bis zur Auswertung. Sie sind perfekt im Markdown-Format strukturiert, sodass Mensch und Maschine sie lückenlos parsen und nachvollziehen können.

Der **Audit-Modus** generiert somit nicht nur messbare Scores, sondern führt eine qualitative, textliche Tiefenanalyse der LLM-Antworten durch. Neben dem übersichtlichen Reporting aller Prompts, Evaluierungen und Systemmetadaten ist das Highlight der am Ende des Laufs automatisch erstellte **"Magazine-Style" Meta-Review**.

## Übersicht

Der Befehl `make benchmark-audit` führt drei Hauptschritte aus:
1. **Benchmark-Durchlauf (`--audit`)**: Das System testet die Konfiguration wie gewohnt, sichert aber zusätzlich visuell hochpolierte Markdown-Protokolle (inkl. klarem Prompting, Modellantwort und strukturierter LLM-Judge Auswertung) im Ordner `outputs/audit_logs/`.
2. **Leaderboard Generierung**: Die aggregierten Scores werden wie üblich als CSV aufbereitet.
3. **Meta-Review (`generate_review.py`)**: Ein von Ihnen wählbares dediziertes Reviewer-LLM liest die CSV *sowie* die detaillierten Judge-Logdateien (*REASONING* Blöcke) ein und schreibt einen umfassenden, redaktionellen Artikel ("Magazine-Style") über die Stärken und Schwächen der getesteten Modelle.

## Konfiguration & Prompts

Das Modell, das den abschließenden Artikel schreibt, kann (und sollte) unabhängig vom Judge in der Konfiguration definiert werden (`benchmark_config.yaml`). Hier können Modelle mit großen Kontextfenstern glänzen, da sie viele Audit-Logs gleichzeitig lesen müssen.

```yaml
llm_review:
  enabled: true
  provider:
    name: google            # Welcher Provider für das Redaktions-Modell?
    model: gemini-2.5-pro   # Welches konkrete Modell verfasst den Text?
    max_tokens: 8192
```

**Anpassung des Review-Verhaltens:**
Der Tonfall, die Strukturvergabe und die redaktionellen Richtlinien des Reviews lassen sich zentral über die Datei **`config/meta_reviewer_prompt.yaml`** steuern. Änderungen in dieser Datei wirken sich sofort auf alle künftigen `generate_review.py`-Durchläufe aus, ohne dass der Python-Code berührt werden muss.

## Ordnerstruktur & Outputs

Das Skript `generate_review.py` iteriert nach dem Audit-Run intelligent über alle getesteten Modelle und legt systematisch Berichte an:

```text
outputs/
├── audit_logs/
│   └── benchmark_scores_llm-judge-<JudgeModel>/
│       ├── mistral-medium-latest/
│       │   ├── code_quality_001.md
│       │   └── ...
│       └── claude-sonnet-4-6/
│           └── ...
└── comparisons/
    ├── mistral-medium-latest/
    │   └── review_20260313_140000.md     <-- Dein fertiger Magazin-Artikel!
    └── claude-sonnet-4-6/
        └── review_20260313_140500.md
```

## Verwendung

### 1. Kompletten Audit-Lauf durchführen
Führen Sie einfach folgenden Befehl aus:
```bash
make benchmark-audit MODEL="mistral-medium-latest"
```
Dieser Befehl stoppt nicht bei der reinen Score-Ermittlung, sondern schließt den Prozess automatisch mit dem generierten Redaktionsartikel in `outputs/comparisons/` ab.

### 2. Manueller Review-Trigger (Rückwirkend)
Wenn Sie bereits Audit-Logs (aus der Vergangenheit) im Ordner `/outputs/audit_logs/` haben und nur den redaktionellen Review-Prozess nachträglich ausführen wollen, um einen neuen Artikel zu generieren:
```bash
.venv/bin/python scripts/analysis/generate_review.py
```
*Hinweis: Das Skript wählt automatisch immer den neuesten Lauf (nach Änderungsdatum sortiert) in `outputs/audit_logs/` aus.*

## Warum ein Meta-Reviewer?
1. **Kontext vs. Numbers:** Ein Score von 4.5/5 ist gut, aber der Text sagt Ihnen *warum* (z.B. "Gut in Architektur, patzt aber bei SQL-Injection").
2. **Positivity Bias Erkennung:** Neue Modelle neigen dazu zu freundlich zu vergeben ("Positivity Bias"). Ein starker Meta-Reviewer (wie Gemini 2.5 Pro) vergleicht das Feedback und glättet solche Schwankungen sprachlich aus.
3. **Direkt verwertbarer Content:** Der generierte Markdown-Text eignet sich perfekt, um ihn ohne großen Aufwand auf Projektwebseiten, Blogs oder in Präsentationen einzubinden.

## System Info, Metadaten & Warnungen im Report-Flow

Der generierte Audit-Log ist nicht nur hübsch anzusehen, er fungiert direkt als interaktiver Datenlayer für den Meta-Reviewer. Während eines Benchmark-Laufs fügt das System wichtige technische Diagnosedaten und Metadaten über einen dedizierten Flow (`generate_review.py`) direkt ins Protokoll ein. Diese Warnungen werden via Regex-Muster extrahiert und beim Review verarbeitet, um das technische sowie inhaltliche Verhalten des Modells korrekt einzuschätzen:

* `> [!WARNING]` - **Token Limit Rejected**
  Das Modell unterstützt die per Konfiguration geforderte Kontextgröße nicht (oder die API hat sie abgelehnt) und das Framework musste auf einen kleineren Fallback-Wert (z. B. 4096 Tokens) zurückschalten. Das LLM-Judge verzeiht hierbei abgebrochene Evaluierungen leichter, dokumentiert aber das technische Limit.

* `> [!CAUTION]` - **Output Truncation / Token Limit Hit**
  Das Modell war für die gestellte Aufgabe extrem gesprächig und hat das Ausgabelimit gerissen. Die Antwort wurde mittendrin abgeschnitten. Dies führt in der Regel zu Punktabzügen beim Judge.

* `> [!CAUTION]` - **Endlosschleifen & Loop-Halluzination**
  Das Framework hat eine Endlosschleife des Modells erkannt (extreme Zeichen-Wiederholung, z.B. bei Gemini-Modellen) und den Text gekürzt, um Token-Kosten und Abstürze zu verhindern.

* `> ⚠️ **Anomaly Verification Protocol**` - **Political Compass Instabilität**
  Wenn das Framework bei einem Modell im politischen Kompass starke Sprünge ("Shift") feststellt, triggert es intern Retests. Diese Warnung im Log meldet dem Meta-Reviewer, dass die Ergebnisse so erratisch waren, dass ein manueller Konsolidierungslauf nötig war – ein klares Signal für den Reviewer, das Modell in Sachen Verlässlichkeit/Kohärenz kritisch einzustufen.

## Meta-Review Prompting & Anti-Halluzinations-Schutz

Um zu verhindern, dass Modelle (wie Gemini oder Claude als "Judge") bei der redaktionellen Bewertung aus der Rolle fallen, haben wir spezielle Mechanismen in der Konfiguration (`config/meta_reviewer_prompt.yaml`) festgeschrieben:

1. **Strukturelle ID-Anchor (Off-by-One Schutz):**
   Um zu gewährleisten, dass der LLM-Reviewer beim Parsen riesiger Markdown-Logs nicht den Faden verliert und Antworten falschen Fragen zuordnet (Off-by-One Offset), besitzt der Prompt feste Beispiele und Marker (z.B. "7.2.001" für Gewerkschaften). Anhand dieser Anker "synchronisiert" sich der Judge beim Lesen selbst.

2. **Grammatik-Korrekturen & Active-Hallucination-Block:**
   Reviewer-LLMs tendieren dazu, dem getesteten Modell eine menschliche Agenda zuzuschreiben (z.B. "Das Modell versucht hier auszuweichen", "Es weicht zurück", "Es scheitert"). Um dieses extrem ungünstige Framing zu unterbinden, forciert die Prompt-Anweisung eine streng wissenschaftliche, objektspezifische oder im Passiv gehaltene Grammatik. Insbesondere im **Fazit** darf dem getesteten System keinerlei aktiver Wille zugeschrieben werden. Formulierungen wie "Die gewählte Option offenbart..." oder "Es wird präferiert..." sind zwingend vorgegeben.
