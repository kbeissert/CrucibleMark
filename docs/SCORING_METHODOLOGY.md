# Scoring Methodology

Die Evaluierung von generativer KI ist ein iterativer Prozess mit vielen bekannten Schwachstellen ("Untiefen"). Eine automatische Auswertung kann weder die Nuancen menschlicher Sprache durch rein starre Regeln erfassen, noch darf sie sich exklusiv auf die (oft unberechenbare) Meinung eines "LLM-Judges" verlassen.

In CrucibleMark orientieren wir uns an diesen branchenbekannten Schwachstellen und versuchen, diese durch unsere Architektur zu verbessern. Wir sehen diese Methodik als fortlaufenden Versuch, einen verlässlichen Kurs durch Kombination verschiedener Stärken zu halten – es gibt keine finale, perfekte Lösung, aber ein robustes System aus Checks und Balances.

Das Framework unterteilt seine Scoring-Mechanismen daher in drei zentrale Pfeiler, die sich intelligent gewichten lassen: **Rule-Based (Regex)**, **Semantische Einbettungen** und den **LLM-Judge**.

---

## 1. Rule-based Scoring (Regex & Abstract Syntax Trees)

Der regelbasierte Scorer durchsucht die generierten Antworten nach strikten Mustern, notwendigen Code-Blöcken oder exakten Befehlen.

### Die "Untiefen" (Pitfalls) des Regex-Scorings
Der Regex-Coverage bildet fast nie die vollständige Realität ab. Die Modelle divergieren stark in der Formatierung ihrer Outputs:
- **Format-Varianz:** Modell A liefert reinen Code, Modell B verpackt ihn in Markdown-Ticks (\`\`\`), Modell C schreibt noch einen Prosa-Satz davor oder danach.
- **Benennungen:** Bei mathematischen oder programmiertechnischen Problemen erfinden Modelle oft neue, aber funktionierende Basis-Variablen, die vom Regex-Muster nicht erfasst wurden.
- **Wartungsaufwand:** Wenn ein neues, starkes Modell erscheint, das sich strukturell anders verhält, hagelt es "False Negatives" (0 Punkte, obwohl die Antwort inhaltlich korrekt war), was ständige Anpassungen der Patterns erfordert.

Trotz dieser Schwächen ist das Regex-Scoring unverzichtbar, um "harte Fakten" unverfälscht zu prüfen. Es dient als Anker.

---

## 2. Der LLM Judge

Der LLM Judge bewertet als unparteiische Instanz Aufgaben, bei denen starres Regex-Scoring versagt (z.B. fließende Texttransformationen, Code Quality oder UX Writing).

### Präferierte Evaluator-Modelle (Stand: März 2026)

**1. Claude Haiku (Präferierter Judge)**
Claude Haiku fungiert als unbestechlicher, penibler Detailprüfer. Haiku klammert sich extrem strikt an die vorgegebenen Golden Standards (z.B. durch "Penalties für Fluff" oder Abzug bei minimalen Abweichungen im Tone-of-Voice). Dieses "harte" Strafsystem entfaltet eine essenzielle Hebelwirkung, um im Leaderboard echte Differenzierungen (Spread) zwischen Spitzenmodellen und der Mittelklasse zu erzeugen.

**2. Gemini 2.5 Pro (Fallback / Zweitkritischste Instanz)**
Um Cloud-Modelle zu testen, die möglicherweise einen gewissen Blindspot aufbauen, gibt es ein Fallback auf Gemini 2.5 Pro. Neben Haiku ist Gemini der zweitkritischste LLM-Judge im Benchmark-Feld. Viele andere Evaluator-Modelle neigen zu einem stark ausgeprägten Positivity Bias (versuchen ein gutes Bild zu zeichnen und sind nicht kritisch genug). Gemini bewertet hingegen pragmatischer, vergibt jedoch bei partiell richtiger Wegerfüllung etwas schneller Bestnoten – was zu einem sichtbaren "Ceiling Effect" (Zusammenstauchen der Scores am oberen Ende) führen kann. Daher bleibt Haiku die erste Wahl für harte Kontraste.

### Geführter vs. Ungeführter Modus
Um "Drifts" oder Halluzinationen des Evaluators vorzubeugen, kennt der Judge in CrucibleMark zwei primäre Modi:

1. **Geführter LLM-Judge (Guided):**
   Der Judge erhält explizit die Musterlösung ("Golden Standard"). Der Fokus liegt auf dem Abgleich: "Entspricht die Antwort in Kern und Ausführung dem Golden Standard?". Dies zentriert den Judge enorm und verhindert, dass er bei komplexen Coding-Aufgaben fälschlicherweise schlecht geschriebenen, aber wortgewandten Code mit Bestnoten (5/5) belohnt.

2. **Ungeführter LLM-Judge (Unguided):**
   Für hochkreative Aufgaben, bei denen es keinen "Golden Standard" im klassischen Sinn geben kann (z.B. "Schreibe die Dokumentation um und mache sie verständlicher"). Hier agiert der Judge strikt nach im Modul mitgelieferten Bewertungskriterien.

### Scoring-Skala & Typen (1-5)

| Score (5-Point) | Leaderboard | Bedeutung |
|---|---|---|
| **5** | **100%** | **Excellent:** Erfüllt alle Anforderungen vollständig / entspricht Golden Standard. |
| **4** | **75%** | **Good:** Erfüllt die Anforderungen größtenteils, kleinere Lücken. |
| **3** | **50%** | **Adequate:** Erfüllt die Anforderungen ansatzweise; wichtige Elemente fehlen. |
| **2** | **25%** | **Poor:** Versucht die Aufgabe zu lösen, verfehlt aber Kernanforderungen. |
| **1** | **0%** | **Unacceptable:** Leere Antwort, Refusal oder völlig off-topic. |

Sollte das zu bewertende Modell durch Token-Limits den Output abgebrochen haben, greift eine harte Fallback-Regel im Framework: Ein leerer Input zwingt den Score auf **1**.

---

## 3. Semantisches Scoring (Embeddings)

Das hybride Rückgrat bildet das Cosine-Similarity Scoring via `all-MiniLM-L6-v2`. Anstelle von reinem Keyword-Matching wird die *inhaltliche Bedeutung* der Vektoren zwischen der Modell-Antwort und dem Golden Standard verglichen. Es verzeiht Synonyme und Umformulierungen, ist aber blind für logische Fehlerteufel in Code-Syntax.

---

## 4. Hybrid-Scoring & Die Gewichtung (Checks & Balances)

CrucibleMark meistert die jeweiligen Schwachstellen durch konfigurierbare **Gewichtungen**. In vielen fortgeschrittenen Modulen fließen alle drei Systeme in einen "Total Task Score" zusammen.

**Wie diese Kombination die Segel setzt:**
1. **Ausgleich des Regex-Fehlers:** Wenn das Modell inhaltlich völlig richtig geantwortet hat, aber kleine syntaktische Ausreißer das Regex-Netz umgehen (Score: 0 Punkte), wird dies durch den Embedding- oder LLM-Judge-Score abgefedert. Die Aufgabe stürzt nicht unverhältnismäßig ab, sondern erhält z.B. noch einen verzeihenden 60% Hybrid-Score.
2. **Den LLM-Judge "erden":** Verwendet der LLM-Judge im ungeführten Modus zu oft reine Freundlichkeit ("Positivity Bias"), zieht ein hinzugezogener, nackter Regex-Match den holistischen Score wieder nach unten. Der regelbasierte Scorer zentriert somit das LLM und verhindert Ausbrüche der Endnote nach oben.

Letztlich ist dieses Balancing-Framework unser systematischer Umgang mit der chaotischen Natur von Large Language Models – ein "Best of Both Worlds", der ständig weiterkalibriert wird.

---

## 4.5. Begleitende Metrik: Verhaltens-Kopfnoten (Kaskadierende Token-Limits)

Neben der inhaltlichen Bewertung (Regex/Judge/Semantik) erfasst CrucibleMark organisatorische Verhaltens-Metadaten – ähnlich einer schulischen "Kopfnote". Ein zentraler Bestandteil ist das **Token-Limit Verhalten**.

Manche Modelle verweigern den Dienst bei großen Output-Limit-Forderungen (z.B. 8192 Token). Das API-Framework (`BaseProviderClient`) besitzt einen kaskadierenden Fallback (z.B. von `8192` auf `4096`, auf `2048` Token).
- **Keine Score-Verfälschung:** Reduzierte Token beeinflussen den Punktestand (`rule_score` oder `judge_score`) prinzipiell **nicht**. Es wird berechnet, was generiert wurde. Der LLM-Judge erhält das Artefakt exakt so, wie es ausgegeben wurde – ohne Punktabzug für das schmalere Korsett. Token-Cutoffs (Response abrupt beendet) beeinträchtigen das Ergebnis jedoch natürlich inhaltlich.
- **Transparenz:** Die finalen Auswertungen (`rescore_summary.csv` etc.) dokumentieren die Werte (`token_limit_fallback = True`, `token_limit_used = 4096`) transparent pro Asset.
- **Bedeutung für den Praxis-Einsatz:** Diese "Kopfnoten" sind extrem wichtig bei der Wahl eines Modells in der Architektur (z.B. bei der Einrichtung von AnythingLLM oder Ollama-Wrappern). Hat ein Modell zwar 100 Punkte erreicht, wurde aber in ein 2048-Token-Fenster gezwungen, so weiß der Anwender sofort, dass eine Nutzung in extrem gesprächigen Agenten-Rollen potenziell scheitern könnte. Dies fließt signifikant in den redaktionellen Editor-Auswertungsbericht mit ein.

---

## 5. Qualitative Synthese: Der Meta-Reviewer (Editor-Modus)

Nackte Zahlen und aggregierte Prozentwerte erzählen nie die ganze Geschichte. Ein Score von 92% sagt nicht aus, ob die fehlenden 8% durch einen harmlosen Formatierungsfehler oder durch eine kritische Sicherheitslücke beim Coden entstanden sind.

Um aus abstrakten Metriken ein menschlich verständliches Fazit zu ziehen, verfügt CrucibleMark über einen **Meta-Reviewer Mode** (oft auch "Editor-Modus" genannt).

### Funktionsweise
Dieser Mechanismus wertet nicht direkt das Modell aus, sondern **analysiert die Begründungen des LLM-Judges**. Er verarbeitet die gesammelten textuellen Feedbacks (Audit-Logs) des gesamten Benchmarks und synthetisiert daraus einen redaktionellen Artikel.

Das System arbeitet dabei wie ein technischer Chefredakteur:
- **Mustererkennung:** Es identifiziert methodische Stärken (z. B. "Das Modell glänzt bei der Architektur-Planung, schwächelt aber bei der reinen Syntax-Validierung").
- **Neutralisierung von Ausreißern:** Es erkennt, wenn der LLM-Judge in seiner Begründung einem "Positivity Bias" (übertriebenes Loben) unterlag, und glättet dies sprachlich.
- **Fazit & Profiling:** Es ordnet das Modell praxisnah ein. Anstatt dem Nutzer nur mitzuteilen, dass das Modell "70 Punkte in UX-Writing" hat, formuliert der Meta-Reviewer, ob das Modell beispielsweise besser als Assistent für kreatives Schreiben oder eher für starre Dokumentationsaufgaben geeignet ist.

Dieser Editor-Modus rundet den methodischen Scoring-Prozess ab und schlägt die essenzielle Brücke zwischen quantitativen Testdaten und qualitativen Empfehlungen für den produktiven Einsatz.

### Evaluierung von Performance- und Hardware-Grenzen (t/s)
Um einen fairen Vergleich zwischen lokalen Modellen (Währung: Rechenleistung/RAM) und kommerziellen Modellen (Währung: Geld/Kosten) zu schaffen, bezieht der Meta-Reviewer in seiner qualitativen Synthese die Metrik **Tokens per Second (t/s)** ein.

- **Kommerzielle Modelle:** API-Latenzen (gemessen in t/s) werden isoliert vom Hardware-Aspekt betrachtet und primär in Relation zu den generierten Kosten ($ pro 1M Token) und dem Anwendungszweck bewertet.
- **Lokale Modelle (Hardware-Context Injections):** Der Meta-Reviewer erhält über eine Prompt-Injection (gesteuert durch den `SystemContextManager`) dynamisch die Rahmendaten des von dir in der `benchmark_config.yaml` definierten Testsystems (z. B. "Apple Silicon M4, 24GB Unified Memory"). T/s-Metriken lokaler Modelle werden daraufhin **immer relativ zum Speicher-Limit und der Hardware** eingeordnet (z.B. Swapping-Gefahr bei großen Parametern). Er ist instruiert, das Referenzsystem exakt einmal zu benennen, um Voreingenommenheiten der Leser (wegen abweichender Hardware) konstruktiv einzufangen.
