**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:14:15


Nicht deploy für produktive MCP-Tool-Pipelines, weil die Tool-Calls nicht valide waren, ein Retry erforderlich wurde und die Gesamtausführung trotz fehlender Halluzinationen kein belastbares Protokollvertrauen herstellt.

**Tool-Execution-Profil**

Llama 4 Scout 17B zeigt kein verlässliches Tool-Verhalten. P1 bleibt über alle Aufgaben bei 35 und damit auffällig flach. Das spricht nicht für situationsabhängige Werkzeugwahl, sondern für ein starres oder nur teilweise protokollkonformes Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch erzwingt, erkennt das Modell den Bedarf nicht robust genug. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Vorwissen ableiten und anschließend per Fetch abrufen lässt, wirkt die Ausführung ebenfalls nicht deterministisch. Dass retry_required=true gesetzt ist, deutet hier eher auf ein Format- oder Protokollproblem als auf reines Inhaltsverständnis. Für MCP-Betrieb ist genau das kritisch: Ein Modell darf in der Tool-Ausgabe nicht “fast richtig” sein.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. In fünf von sechs Assets liegt P2 bei 40 und damit auf einfachem, brauchbarem Verdichtungsniveau. Sobald die Aufgabe aber eine saubere, quellengebundene Zusammenführung aktueller Web-Inhalte verlangt, bricht die Leistung sichtbar ein. Der Ausschlag kommt aus EU License Research mit P2=0.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist negativ, obwohl keine formale Halluzination markiert wurde. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, verfehlt das Modell die inhaltliche Verifikation vollständig. Content-Verification-State B2 bei P2=0 heißt in der Praxis: Die Antwort bleibt nicht belastbar an die abgerufenen Quellen gebunden. Für Compliance-, Policy- oder Regulated-Research-Pipelines ist das nicht ausreichend.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlschlagenden Abruf prüft, halluziniert es keinen Ersatzinhalt und erreicht P2=40. Das ist produktionsfähig im engen Sinn: Fehler werden eher offengelegt als kaschiert. Diese Stärke kompensiert aber nicht die schwache Tool-Validität.

**Souveränitätsprofil**

Lokal betreibbar, aber nicht fleet-kompetitiv. Der Sovereignty Gap liegt bei -1.37 Punkten unter dem Fleet-Ø von 67.84. Hinzu kommt eine harte Einschränkung: EU-domicilierte Organisationen dürfen Llama 4 laut Meta-Lizenz nicht selbst deployen. Für souveräne EU-Setups fällt das Modell damit praktisch aus.

**Fazit & Empfehlung**

Geeignet allenfalls für interne Assistenz-Workflows mit menschlicher Kontrolle, einfacher Web-Zusammenfassung und tolerierbaren Retries. Nicht geeignet für autonome MCP-Pipelines, Compliance-Recherche, deterministische Tool-Orchestrierung oder jede Kette, in der Tool-Calls formal korrekt und quellengebundene Synthesen zwingend sein müssen. Das Modell ist textuell oft brauchbar, aber als Infrastrukturträger nicht belastbar genug.