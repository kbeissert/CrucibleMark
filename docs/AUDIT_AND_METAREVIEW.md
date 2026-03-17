# CrucibleMark: Audit & Meta-Review Workflow

CrucibleMark bietet neben dem Standard-Benchmark einen erweiterten **Audit-Modus**. Dieser Modus generiert nicht nur messbare Scores, sondern führt eine qualitative, textliche Tiefenanalyse der LLM-Antworten durch. Das Highlight ist der am Ende des Laufs automatisch erstellte **"Magazine-Style" Meta-Review**.

## Übersicht

Der Befehl `make benchmark-audit` führt drei Hauptschritte aus:
1. **Benchmark-Durchlauf (`--audit`)**: Das System testet die Konfiguration wie gewohnt, sichert aber zusätzlich hochdetaillierte Markdown-Protokolle (mit Prompt, Antwort und LLM-Judge Reasoning) im Ordner `outputs/audit_logs/`.
2. **Leaderboard Generierung**: Die aggregierten Scores werden wie üblich als CSV aufbereitet.
3. **Meta-Review (`generate_review.py`)**: Ein von Ihnen wählbares dediziertes Reviewer-LLM liest die CSV *sowie* die detaillierten Judge-Logdateien (*REASONING* Blöcke) ein und schreibt einen umfassenden, redaktionellen Artikel ("Magazine-Style") über die Stärken und Schwächen der getesteten Modelle.

## Konfiguration (benchmark_config.yaml)

Das Modell, das den abschließenden Artikel schreibt, kann (und sollte) unabhängig vom Judge in der Konfiguration definiert werden. Hier können Modelle mit großen Kontextfenstern glänzen, da sie viele Audit-Logs gleichzeitig lesen müssen.

```yaml
llm_review:
  enabled: true
  provider:
    name: google            # Welcher Provider für das Redaktions-Modell?
    model: gemini-2.5-pro   # Welches konkrete Modell verfasst den Text?
    max_tokens: 8192
```

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

## System Info & Warnungen in Audit-Logs

Während eines Benchmark-Laufs kann das Framework spezielle Systemmeldungen in die Markdown-Protokolle einfügen. Diese Warnungen helfen dem LLM-Judge (bei der Bewertung) und dem Meta-Reviewer (bei der Erstellung des Magazin-Artikels), das technische Verhalten des Modells korrekt einzuschätzen:

* `> [!WARNING]`
  `> Das Modell (bzw. die API) hat das initial angeforderte Token-Limit abgelehnt...`
  **Bedeutung:** Das Modell unterstützt die per Konfiguration geforderte Kontextgröße nicht (oder die API hat sie abgelehnt) und das Framework musste auf einen kleineren Fallback-Wert (z. B. 4096 Tokens) zurückschalten. Das weist auf ein beschränktes Kontextfenster des Modells hin.

* `> [!CAUTION]`
  `> Das Modell hat das maximale Token-Limit erreicht und die Antwort abgebrochen...`
  **Bedeutung:** Das Modell war für die gestellte Aufgabe extrem gesprächig (verbose) und hat das Ausgabelimit gerissen. Die generierte Antwort wurde mittendrin abgeschnitten. Dies führt in der Regel zu Punktabzügen beim Judge, da das Modell Anweisungen zur Prägnanz missachtet hat.

* `> [!CAUTION]`
  `> Das Framework hat eine Endlosschleife des Modells erkannt (extreme Zeichen-Wiederholung) und den defekten Textblock an dieser Stelle gekürzt.`
  **Bedeutung:** Das Modell erlitt eine typische LLM-Halluzination und geriet in eine Endlosschleife (z. B. 80.000 Leerzeichen am Stück, um eine Tabelle zu formatieren). Das Framework blockiert diesen Fehler serverseitig (um Token-Kosten und Abstürze zu verhindern). Der Meta-Reviewer registriert so automatisiert, dass das Modell zu Instabilitäten und Endlosschleifen neigt.
