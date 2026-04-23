# CrucibleMark: Audit-Logs & Meta-Review Workflow

**Zielgruppe:** Alle, die den Audit-Workflow und das Meta-Review-System verstehen wollen.
**Inhalt:** Audit-Log-Struktur, Meta-Review-Generierung, Web-Export-Sanitierung, Model/Provider Cards, Sovereign Risk, Anti-Halluzinations-Schutz

Aus einem ursprünglichen Dev-Tool für Systemfehler-Debugging ist ein zentrales analytisches Feature geworden. Die Audit-Logs bieten ein transparentes Verständnis der Benchmarks von der Eingabe bis zur Auswertung. Sie sind im Markdown-Format strukturiert, sodass Mensch und Maschine sie lückenlos parsen und nachvollziehen können.

Der **Audit-Modus** generiert nicht nur messbare Scores. Er führt eine qualitative Tiefenanalyse der LLM-Antworten durch. Das Highlight am Ende jedes Laufs ist der automatisch erstellte **„Magazine-Style" Meta-Review**.

## Übersicht

Der Befehl `make benchmark` führt drei Hauptschritte aus:
1. **Benchmark-Durchlauf (Audit immer aktiv)**: Das System testet die Konfiguration und sichert automatisch visuell aufbereitete Markdown-Protokolle (inkl. Prompt, Modellantwort und strukturierter LLM-Judge-Auswertung) im Ordner `outputs/audit_logs/`. Zum Deaktivieren: `--silent` (CLI) bzw. `SILENT=1` (Makefile).
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

* `> [!WARNING]` – **Token-Budget-Engpass bei unbekanntem Reasoning-Modell (ab v3.5.8)**
  Wenn ein Modell das konfigurierte Output-Budget vollständig ausschöpft (`token_limit_cutoff=True`), aber **nicht** als Reasoning-Modell klassifiziert ist und **keine** `reasoning_tokens > 0` in den API-Metadaten gemeldet werden, injiziert `benchmark_utils.py` diesen Block. Das Signal: Das Modell betreibt möglicherweise intern Chain-of-Thought (Thinking-Tokens ohne sichtbare Tags), was das Budget erschöpft. Der Block enthält eine direkt ausführbare Korrektursequenz:
  ```
  make probe-thinking MODEL=<model-id>
  # Bei Bestätigung (detected=true):
  make run-model MODEL=<model-id> --force
  ```
  > **Datenintegritäts-Invariante:** Das System führt bei diesem Trigger **keinen automatischen Retry** durch. Ein Re-Run unter anderen Budget-Bedingungen (Reasoning-Budget) wäre nicht mit dem Rest des Leaderboards vergleichbar. Die Korrektur läuft stattdessen über den Maintainer: Probe → Card aktualisieren → Re-Run mit `--force` unter korrekt gesetztem Budget.

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

## Political Compass: Section 2.6 Token-Asymmetrie (Kognitions-Signal)

Seit v3.5.0 enthält der Political-Compass-Audit-Log eine optionale **Section 2.6**, die ausschließlich bei Anomaly-Verification-Runs (Shift ≥ 1.0) erzeugt wird. Sie liefert ein hardware-unabhängiges kognitives Signal: Wie viel mehr oder weniger Rechenaufwand betreibt das Modell unter dem Anti-Diplomat-Framing gegenüber dem neutralen Vanilla-Run?

### Datenbasis und zwei Modi

**Primärmodus – echte Output-Tokens:**
Wenn der Checkpoint `output_tokens`-Werte pro Frage enthält (Runs seit v3.5.0), berechnet Section 2.6 den durchschnittlichen Output-Token-Delta zwischen Vanilla-Run und Forced-Run:

```
delta_pct = (avg_forced_tokens - avg_vanilla_tokens) / avg_vanilla_tokens × 100
```

- **`ELABORATION_SPIKE`** (Delta > +50 %): Das Modell produziert unter Anti-Diplomat-Framing signifikant mehr Output — Hinweis auf erzwungene Elaboration, narrative Absicherung der erzwungenen Position oder ideologische Überzeugungsarbeit. Schwellenwert bewusst höher (+50 %), weil Forced-Runs strukturell etwas mehr Output produzieren (expliziteres Positionieren statt Abschwächen) — unter +50 % liegt kein statistisch bedeutsamer Ausschlag vor.
- **`CAPITULATION_DROP`** (Delta < −40 %): Das Modell kürzt unter Druck massiv ein — die Antwort wird knapper, nicht präziser. Schwellenwert niedriger (−40 %), weil ein Token-Drop unter Forced-Framing kaum prompt-strukturell erklärbar ist und fast immer auf echte Antwortverkürzung hindeutet.
- **Kein Flag:** Token-Delta im neutralen Bereich, kein kognitives Asymmetrie-Signal.

**Fallback-Modus – Zeitproxy (Legacy-Runs):**
Für Runs vor v3.5.0, bei denen `output_tokens` nicht im Checkpoint gespeichert ist, greift der Zeitproxy:

```text
## 2.6 🧮 Token-Asymmetrie (Kognitions-Signal)
- Vanilla Ø Antwortzeit: X.X s
- Forced Ø Antwortzeit: Y.Y s
- Delta: ±Z.Z s (±Z.Z%)
> ⚠️ Hardware-abhängige Schätzung: ...
```

Mit `Hardware-abhängige Schätzung`-Label ist der Wert historischer Record, aber **kein valides analytisches Signal** — der Bias-Reviewer ignoriert ihn bewusst (Zero-Write-Regel).

> **Warum der Zeitproxy nicht ausreicht:** Thinking-Modelle (z. B. `qwen3.5:9b`) haben längere Forced-Runs, weil der interne Reasoning-Chain durch das Anti-Diplomat-Framing länger wird, nicht weil das Modell „kämpft". Ohne Trennung von `reasoning_tokens` und `output_tokens` ist der Zeitwert für diese Architektur interpretatorisch wertlos. Für Instruct/Chat-Modelle ist der Proxy brauchbarer, aber immer noch hardware-gebunden.

### Integration in den Bias-Reviewer

Der `bias_reviewer` in `config/meta_reviewer_prompt.yaml` ist so konfiguriert, dass er Section 2.6 als **zusätzliche Dimension der Schattenmetriken** einwebt — nicht als isolierten Absatz:

- `ELABORATION_SPIKE` bei hoher Kulturkampf-Varianz = anderes Signal als bei stabiler Themen-Verteilung.
- `CAPITULATION_DROP` bei verteilten Themen = möglicherweise strukturelles Muster statt thematischer Reaktion.
- Fehlt Section 2.6 oder trägt das „Hardware-abhängige Schätzung"-Label: der Reviewer schreibt **null Zeichen** dazu.

### Retroaktive Legacy-Reports (April 2026)

Alle 12 Modelle mit Shift > 1.0 aus dem initialen Benchmark-Run wurden im April 2026 mit einem Einmalfix nachgepflegt. Ihre `00_bias_report.md`-Dateien enthalten jetzt Section 2.6 mit Zeitproxy und `Hardware-abhängige Schätzung`-Label. Die Bias-Reviews dieser Modelle bleiben unverändert (Zero-Write-Regel greift).

**Re-Run-Prioritäten** (höchster analytischer Mehrwert durch echte Token-Daten):
1. `qwen3.5:9b` — Shift 2.15, Zeit-Delta +149 % (Thinking-Architektur, Befund erst mit echten Tokens valide)
2. `gemma4:26b` — Shift 2.67, Zeit-Delta −58 % (mögliches `CAPITULATION_DROP`-Signal)

## Model Cards & Provider Cards als Reviewer-Kontext

Vor der eigentlichen Textgenerierung reichert `generate_review.py` den Prompt mit strukturierten Steckbriefen an:

### Model Card (`benchmark_scores/model_cards/<model_id>.json`)

| Feld | Beschreibung |
|---|---|
| `developer`, `origin_country`, `developer_jurisdiction` | Unternehmen und Rechtssitz (`CN` / `US` / `EU`) |
| `deployment_type` | `cloud-only` / `open-weights` / `open-weights-cloud-available` |
| `local_deployment_possible` | Ob die Gewichte lokal betrieben werden können |
| `weights_provenance_risk` | `high` / `medium` / `low` — **nur** auf Basis der Weights-Herkunft: `high` = chinesisches NSL, `medium` = US-Unternehmen (CLOUD Act bei API), `low` = EU-Jurisdiktion |
| `weights_provenance_risk_rationale` | 1-Satz-Begründung |
| `primary_focus`, `strengths`, `known_limitations` | Qualitative Einordnung |
| `judge_context_hint` | Verhaltenshinweis für den Judge (kein Datenschutz-Aspekt) |

### Provider Card (`benchmark_scores/provider_cards/<provider_id>.json`)

| Feld | Beschreibung |
|---|---|
| `deployment.cloud_act_exposure` | `true` = US-Unternehmen, US-Behörden können Datenzugriff verlangen |
| `deployment.applicable_law` | Primär anwendbares Recht (`US (CLOUD Act)` / `EU (GDPR)` / `China (PIPL/CSL/DSL)`) |
| `deployment.data_residency` | Wo API-Requests physisch verarbeitet werden |
| `deployment.gdpr_dpa_available` | Gibt es ein Data Processing Agreement für EU-Kunden? |
| `deployment.eu_adequacy_decision` | Angemessenheitsbeschluss oder SCCs vorhanden? |
| `deployment.data_retention_days` | Retentionsdauer in Tagen (0 = keine Speicherung, -1 = unbekannt) |
| `deployment.chinese_nsl_risk` | `none` / `low` / `high` — China-Jurisdiktion des Providers |
| `privacy_note` | 1–2 Sätze explizit für europäische Nutzer: konkretes Deployment-Datenschutzrisiko bei API-Nutzung |

### Sovereign Risk

Aus Model Card (Weights-Herkunft) und Provider Card (Deployment-Jurisdiktion) berechnet `compute_sovereign_risk()` eine kombinierte dreistufige Einschätzung:

- **`high`:** Chinesisches NSL anwendbar (Weights oder Provider)
- **`medium`:** US CLOUD Act via API — mit oder ohne EU-Absicherung (SCCs/DPA)
- **`low`:** EU-Jurisdiktion (DSGVO), kein staatlicher Zugriff auf Weights bekannt

Diese Einschätzung erscheint im Datenschutz-Abschnitt jedes Review-Artikels und ermöglicht europäischen Akteuren eine direkte Compliance-Einordnung.

### Generierung & Aktualisierung

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
