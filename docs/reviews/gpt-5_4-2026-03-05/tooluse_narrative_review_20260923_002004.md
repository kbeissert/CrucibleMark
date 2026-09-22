**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:20:04


Bedingt deploy, weil das Modell zwar nicht halluziniert, aber mit ungültigen Tool-Calls und einem schwachen Gesamtergebnis von 43.12 kein verlässlicher Standardkandidat für MCP-gestützte Pipelines ist.

**Tool-Execution-Profil**

Das Kernproblem ist nicht rohe Sprachqualität, sondern Werkzeugdisziplin. Der Tool-Call war nicht valide, und P1 liegt insgesamt nur bei 61.67. Besonders aufschlussreich ist die Differenz zwischen Web Search & Tool Selection und URL Construction & Fetch: Beim Test, ob es ohne Hinweis erkennt, dass statt fetch eine Suche nötig ist, fällt es mit P1 35 deutlich ab. Beim Test, ob es eine Ziel-URL aus eigenem Wissen ableiten und dann fetch ausführen kann, erreicht es dagegen P1 75. Das spricht nicht für flexible Werkzeugwahl, sondern für ein Muster: Wenn die Ressource direkt herleitbar wirkt, arbeitet es brauchbar; wenn erst entschieden werden muss, welches Tool epistemisch nötig ist, greift es zu oft zum falschen Pfad. Für dynamische Tool-Pipelines ist das ein strukturelles Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 55.00, und die schwachen Werte in EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass es extrahierte Inhalte nicht stabil in präzise, belastbare Antworten überführt. Gerade bei strukturierter Faktenextraktion aus Fetch-Inhalten bleiben Verdichtung und Priorisierung zu unscharf.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis kommen, wurde keine Halluzination erkannt. Das ist der wichtigste Vertrauensanker dieses Laufs. Der P2-Wert von 20 bleibt jedoch schwach. Das Modell erfindet hier nichts, aber es beweist auch keine saubere, quellennahe Synthese.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt misst, reagiert das Modell akzeptabel. P2 60 ist nicht stark, aber entscheidend ist: Es hat trotz Tool-Fehler keinen Seiteninhalt erfunden. Für Produktion ist das die Mindestanforderung, und die erfüllt es.

**Betriebsprofil**

Call 1: 1.96s. MCP-Latenz: 0.19s. Call 2: 2.23s. Total: 26.29s.  
Preis: $2.5/1M Input, $15.0/1M Output.  
Für die gezeigte Leistung langsam und teuer.

**Fazit & Empfehlung**

Geeignet ist GPT-5.4 nur für überwachte Pipelines mit engem Tool-Routing, klaren Allowed-Paths und nachgelagerter Validierung der Tool-Aufrufe. Für agentische Workflows, offene Recherchepfade, Compliance-nahe Web-Abfragen und mehrsprachige Rechercheketten würde ich es nicht als primären Orchestrator einsetzen. Wenn Sie es verwenden, dann als Antwortschicht hinter einer streng kontrollierten Tool-Auswahl, nicht als Instanz, der Sie die Werkzeugentscheidung selbst überlassen.