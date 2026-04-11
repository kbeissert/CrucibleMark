# CrucibleMark: Audit-Logs & Meta-Review Workflow

Aus einem ursprünglichen Dev-Tool für Systemfehler-Debugging ist ein zentrales analytisches Feature geworden. Die Audit-Logs bieten ein transparentes Verständnis der Benchmarks von der Eingabe bis zur Auswertung. Sie sind im Markdown-Format strukturiert, sodass Mensch und Maschine sie lückenlos parsen und nachvollziehen können.

Der **Audit-Modus** generiert nicht nur messbare Scores. Er führt eine qualitative Tiefenanalyse der LLM-Antworten durch. Das Highlight am Ende jedes Laufs ist der automatisch erstellte **„Magazine-Style" Meta-Review**.

## Übersicht

Der Befehl `make benchmark-audit` führt drei Hauptschritte aus:
1. **Benchmark-Durchlauf (`--audit`)**: Das System testet die Konfiguration wie gewohnt und sichert zusätzlich visuell aufbereitete Markdown-Protokolle (inkl. Prompt, Modellantwort und strukturierter LLM-Judge-Auswertung) im Ordner `outputs/audit_logs/`.
2. **Leaderboard-Generierung**: Die aggregierten Scores landen wie üblich als CSV.
3. **Meta-Review (`generate_review.py`)**: Ein wählbares Reviewer-LLM liest die CSV sowie die detaillierten Judge-Logdateien (*REASONING*-Blöcke) ein und schreibt einen umfassenden redaktionellen Artikel über Stärken und Schwächen der getesteten Modelle.

## Konfiguration & Prompts

Das Modell, das den abschließenden Artikel verfasst, lässt sich unabhängig vom Judge in der Konfiguration definieren (`benchmark_config.yaml`). Modelle mit großen Kontextfenstern eignen sich hier besonders gut, weil sie viele Audit-Logs gleichzeitig verarbeiten müssen.

```yaml
llm_review:
  enabled: true
  provider:
    name: google            # Welcher Provider für das Redaktions-Modell?
    model: gemini-2.5-pro   # Welches konkrete Modell verfasst den Text?
    max_tokens: 8192
```

**Anpassung des Review-Verhaltens:**
Tonfall, Strukturvorgaben und redaktionelle Richtlinien des Reviews lassen sich zentral über **`config/meta_reviewer_prompt.yaml`** steuern. Änderungen dort wirken sofort auf alle künftigen `generate_review.py`-Durchläufe – ohne Python-Code anzufassen.

## Ordnerstruktur & Outputs

Das Skript `generate_review.py` iteriert nach dem Audit-Run über alle getesteten Modelle und legt systematisch Berichte an:

```text
outputs/
└── audit_logs/
    ├── mistral-medium-latest/
    │   ├── code_quality_001.md
    │   └── ...
    └── claude-sonnet-4-6/
        └── ...

docs/
└── reviews/
    ├── mistral-medium-latest/
    │   └── review_20260313_140000.md     <-- fertiger Magazin-Artikel
    └── claude-sonnet-4-6/
        └── review_20260313_140500.md
```

> **Hinweis:** `outputs/audit_logs/` ist in `.gitignore` ausgenommen und bleibt lokal. `docs/reviews/` wird im Repository versioniert und ist öffentlich einsehbar.

## Verwendung

### 1. Kompletten Audit-Lauf durchführen

```bash
make benchmark-audit MODEL="mistral-medium-latest"
```

Dieser Befehl stoppt nicht bei der Score-Ermittlung, sondern schließt den Prozess automatisch mit dem generierten Redaktionsartikel in `docs/reviews/` ab.

### 2. Manueller Review-Trigger (rückwirkend)

Wenn bereits Audit-Logs im Ordner `/outputs/audit_logs/` vorliegen und nur der redaktionelle Review-Prozess nachträglich laufen soll:

```bash
.venv/bin/python scripts/analysis/generate_review.py
```

Das Skript wählt automatisch den neuesten Lauf (nach Änderungsdatum sortiert) in `outputs/audit_logs/`.

### 3. Web-Export

Die Audit-Logs und Reviews lassen sich für das öffentliche Frontend aufbereiten:

```bash
make web-export
```

Beim Export werden alle Audit-Logs **sanitiert**: Die Judge-Auswertung (Section 3) wird entfernt. Öffentlich zugänglich sind damit nur:

- **Header** (Modell, Provider, Laufzeit, Tokens, Kosten)
- **Section 1 – Prompt / Fragestellung:** die exakte Anfrage, die das Benchmark-System an das getestete Modell gesendet hat
- **Section 2 – Model Response:** die vollständige Antwort des getesteten Modells (inkl. technischer Warn-Blöcke wie `[!CAUTION]`)
- **Modul-Metriken** (P95-Antwortzeit, Timeout-Rate)

Die Judge-Bewertung (Scores, Golden-Standard-Referenzen, Rubriken) fließt nicht in den öffentlichen Audit-Log ein, sondern ausschließlich in den **Meta-Review** (`docs/reviews/`), wo sie redaktionell verdichtet und kontextualisiert wird.

## Warum ein Meta-Reviewer?

1. **Kontext vs. Zahlen:** Ein Score von 4,5/5 ist gut, aber der Text erklärt *warum* (z. B. „Gut in Architektur, patzt aber bei SQL-Injection").
2. **Positivity Bias-Erkennung:** Neuere Modelle tendieren zu freundlichem Feedback. Ein starker Meta-Reviewer (wie Gemini 2.5 Pro) vergleicht das Feedback und glättet solche Schwankungen sprachlich aus.
3. **Direkt verwertbarer Content:** Der generierte Markdown-Text lässt sich ohne großen Aufwand auf Projektwebseiten, Blogs oder in Präsentationen einbinden.

## System Info, Metadaten & Warnungen im Report-Flow

Der Audit-Log fungiert direkt als interaktiver Datenlayer für den Meta-Reviewer. Während eines Benchmark-Laufs injiziert das System technische Diagnosedaten und Metadaten via dediziertem Flow direkt ins Protokoll. Diese Warnungen extrahiert `generate_review.py` per Regex und verarbeitet sie beim Review:

* `> [!WARNING]` – **Token Limit Rejected**
  Das Modell unterstützt die per Konfiguration geforderte Kontextgröße nicht (oder die API lehnte sie ab). Das Framework schaltete auf einen kleineren Fallback (z. B. 4096 Tokens) zurück. Der LLM-Judge verzeiht abgebrochene Evaluierungen leichter, dokumentiert aber das technische Limit.

* `> [!NOTE]` – **Token-Effizienz-Anomalie (Budget ausgeschöpft)**
  Das Modell hat das per Config gesetzte `max_tokens`-Output-Budget vollständig ausgeschöpft (`token_limit_cutoff=True`). Dieser Block erscheint nur, wenn tatsächlich ein Budget in `benchmark_config.yaml → token_budgets` definiert ist — nicht bei ungebegrenzten Modulen. Er markiert, dass die Antwort möglicherweise abgeschnitten wurde *oder* dass das Modell strukturell mehr Tokens produziert als der Modul-Median. Reasoning-Module sind von diesem Flag explizit ausgenommen.

* `> [!CAUTION]` – **Output Truncation / Token Limit Hit**
  Das Modell war für die gestellte Aufgabe extrem gesprächig und riss das Ausgabelimit. Die Antwort wurde mittendrin abgeschnitten. Das führt in der Regel zu Punktabzügen beim Judge.

* `> [!CAUTION]` – **Endlosschleifen & Loop-Halluzination**
  Das Framework erkannte eine Endlosschleife des Modells (extreme Zeichen-Wiederholung, z. B. bei Gemini-Modellen) und kürzte den Text, um Token-Kosten und Abstürze zu vermeiden.

* `> [!WARNING]` – **Hard Constraint Violation (Wortanzahl)**
  Das Modell hat die im Asset definierte Wortanzahl-Obergrenze überschritten. Die Stufe des Verstoßes wird im Label ausgewiesen: `Mild Overshoot` (>120%), `Clear Violation` (>200%) oder `Constraint Ignored` (>300%). Ein automatischer Scoreabzug von 20–60% wird angewendet; der Abzug erscheint inklusive absoluter Punktzahl im Log, damit der Meta-Reviewer den Einfluss korrekt einordnen kann.
  ```
  > **[HARD CONSTRAINT VIOLATION – Constraint Ignored (>300%)]** ...
  ```

* `> [!WARNING]` – **Language Mismatch**
  Das Modell hat eine Aufgabe, die explizit in Deutsch (`metadata.language: de`) gestellt war, auf Englisch beantwortet. Die Erkennung basiert auf einer heuristischen DE/EN-Marker-Frequenzanalyse. Es wird **kein Score-Abzug** angewendet; der Befund wird als separater `status=language_mismatch`-Flag und als WARNING-Block ins Log geschrieben, damit der Meta-Reviewer Instruction-Following und inhaltliche Qualität getrennt bewerten kann.
  ```
  > **[LANGUAGE MISMATCH]** The model responded in English, but the task requires
  > German (`expected_language: de`). Language marker counts: DE=21, EN=66.
  ```

* `> ⚠️ **Anomaly Verification Protocol**` – **Political Compass Instabilität**
  Wenn das Framework bei einem Modell starke Sprünge im politischen Kompass feststellt, triggert es intern Retests. Diese Warnung meldet dem Meta-Reviewer, dass die Ergebnisse so erratisch waren, dass ein manueller Konsolidierungslauf nötig war – ein klares Signal für kritische Einordnung in Sachen Verlässlichkeit.

## Model Cards & Provider Cards als Reviewer-Kontext

Vor der eigentlichen Textgenerierung reichert `generate_review.py` den Prompt mit strukturierten Steckbriefen an:

- **Model Card** (`benchmark_scores/model_cards/<model_id>.json`): Entwickler, Herkunftsland, primärer Fokus, bekannte Stärken/Schwächen, Judge Context Hint (z. B. präferierter Antwort-Stil) und ein Datenschutz-Profil (Weights-Provenance-Risk).
- **Provider Card** (`benchmark_scores/provider_cards/<provider_id>.json`): Unternehmensdaten, Deployment-Typ, GDPR-DPA-Status, Datenspeicherort, Retentionsdauer und Sovereign Risk der API-Nutzung.

Beide Cards fließen als `### Model Card`-Block in das Prompt-Template ein und steuern die **Sovereign-Risk-Berechnung** (`compute_sovereign_risk()`): Kombiniert aus Weights-Herkunft (Model Card) und Cloud-Act-Exposition des Providers (Provider Card) ergibt sich eine dreistufige Einschätzung (`low` / `medium` / `high`), die der Meta-Reviewer im Datenschutz-Abschnitt des Review-Artikels ausweist.

Cards werden separat generiert und aktualisiert:

```bash
make model-cards          # alle fehlenden Model Cards generieren
make model-cards FORCE=1  # alle neu generieren
make provider-cards       # alle fehlenden Provider Cards generieren
```

## Token-Effizienz-Kontext im Meta-Review

Ab v3.4.0 injiziert `generate_review.py` vor den eigentlichen `{log_data}`-Block eine neue Template-Variable `{token_efficiency_context}`. Diese enthält:

- Den **modulspezifischen Ø-Token-Verbrauch** des zu reviewenden Modells
- Den **Fleet-Median** (Durchschnitt über alle Modelle für dasselbe Modul)
- Die **berechnete Ratio** (Modell / Median)

Der Meta-Reviewer-Prompt enthält einen dedizierten Diagnostik-Block **"Token-Effizienz (Verbosity)"**: Wenn die Ratio > 1.5× Median liegt, ist der Reviewer verpflichtet, einen gesonderten Absatz zu schreiben. Reasoning-Module und Metacog-Assets sind von dieser Pflicht ausgenommen, da dort Verbosity strukturell erwartet wird.

## Meta-Review Prompting & Anti-Halluzinations-Schutz

Um zu verhindern, dass Modelle (wie Gemini oder Claude als „Judge") bei der redaktionellen Bewertung aus der Rolle fallen, gibt es spezielle Mechanismen in `config/meta_reviewer_prompt.yaml`:

1. **Strukturelle ID-Anker (Off-by-One-Schutz):**
   Um sicherzustellen, dass der LLM-Reviewer beim Parsen großer Markdown-Logs nicht den Faden verliert und Antworten falschen Fragen zuordnet, enthält der Prompt feste Beispiele und Marker (z. B. "7.2.001" für Gewerkschaften). Anhand dieser Anker synchronisiert sich der Judge beim Lesen selbst.

2. **Grammatikrestriktionen & Active-Hallucination-Block:**
   Reviewer-LLMs tendieren dazu, dem getesteten Modell eine menschliche Agenda zuzuschreiben (z. B. „Das Modell versucht hier auszuweichen"). Um dieses Framing zu unterbinden, erzwingt die Prompt-Anweisung eine streng wissenschaftliche, objektspezifische oder im Passiv gehaltene Grammatik. Im **Fazit** darf dem getesteten System keinerlei aktiver Wille zugeschrieben werden. Formulierungen wie „Die gewählte Option offenbart..." oder „Es wird präferiert..." sind zwingend vorgegeben.
