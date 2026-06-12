**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:04:13


Bedingt deploy, weil das Modell ohne Halluzinationsbefund arbeitet, aber keine valide Tool-Call-Ausführung zeigt und mit 57.62 Combined nur begrenzte Verlässlichkeit für produktive Tool-Pipelines erreicht.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht in erfundenen Inhalten, sondern in der Werkzeugausführung. P1 von 67.50 signalisiert brauchbare Grundkompetenz, aber der ungültige Tool-Call ist für MCP-gestützte Umgebungen ein harter Produktionsbefund. Ein Modell kann inhaltlich korrekt wirken und trotzdem operativ ausfallen, wenn der Aufruf nicht protokollkonform ist.

Die Daten zu Web Search & Tool Selection und URL Construction & Fetch sind nicht einzeln ausgewiesen. Deshalb lässt sich keine saubere Aussage treffen, ob GPT-5.4 Nano aktiv zwischen Such- und Fetch-Werkzeugen unterscheidet oder nur einem festen Muster folgt. Der Gesamtbefund spricht eher für eingeschränkte Tool-Intelligenz als für robuste Werkzeugwahl. Positiv ist, dass kein Retry erforderlich war. Das deutet eher auf einen einmalig abgeschlossenen, aber nicht validen Call als auf ein bloßes Formatproblem mit späterer Korrektur hin.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 46.67 ist der schwächste Wert im Profil und für Architekten der zentrale Warnhinweis. Das Modell scheint Ergebnisse nicht stabil genug in belastbare, knappe Ausgaben zu überführen. Für Extraktion, Compliance-Zusammenfassungen oder mehrstufige Agentenantworten ist das zu wenig Reserve.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist der wichtigste Vertrauensanker dieses Laufs. Das Modell bricht die Tool-Grenze also nicht offensichtlich auf, auch wenn die Verdichtung schwach bleibt.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt prüft, halluzinierte das Modell keinen Ersatzinhalt. Das ist für Produktion akzeptabel. Ein Modell, das Fehler offen stehen lässt, ist beherrschbar. Ein Modell, das bei 404 Inhalte erfindet, wäre sofort auszuschließen. Diesen Ausschlussbefund gibt es hier nicht.

**Betriebsprofil**

Total 31.02s. Einzelaufrufe 2.20s und 2.56s. MCP-Latenz 0.42s. Lokal bepreist. Für die gezeigte Leistung eher langsam.

**Fazit & Empfehlung**

Geeignet ist GPT-5.4 Nano für kostensensitive Vorstufen: Routing, einfache Klassifikation, grobe Extraktion und kontrollierte Sub-Agent-Aufgaben mit starker externer Validierung. Nicht geeignet ist es als autonomer Operator in MCP-Pipelines, in denen korrekte Tool-Wahl, valide Calls und belastbare Verdichtung direkt produktionsrelevant sind. Wenn Sie es einsetzen, dann nur hinter striktem Schema-Checking, Tool-Call-Validierung und einem zweiten Prüfschritt für die Synthese.