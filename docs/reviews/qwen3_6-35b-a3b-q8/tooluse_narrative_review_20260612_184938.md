**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:49:38


Bedingt deploy, weil die Tool-Ausführung insgesamt brauchbar ist, das Modell aber keinen durchgehend validen Tool-Call liefert und bei der Synthese ein Vertrauensrisiko für produktive Tool-Pipelines sichtbar wird.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Standardmuster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr zuverlässig. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, bleibt es brauchbar, aber weniger präzise. Das spricht für situatives Tool-Verständnis, nicht für starres Schema, aber auch für begrenzte Deterministik in der letzten Meile.

Kritisch ist der Befund, dass der Tool-Call nicht durchgehend valide war und ein Retry nötig wurde. Das wirkt hier eher wie ein Protokoll- oder Formatproblem als wie ein reines Planungsversagen. Die hohen P1-Werte in den Such-, Fetch- und multilingualen Aufgaben zeigen, dass das Modell die Struktur der Aufgabe meist versteht. Für MCP-Pipelines heißt das: Wrapper mit Call-Validation, Schema-Repair und kontrolliertem Retry sind Pflicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Die P2-Leistung ist mit 65.83 der klar schwächere Teil des Profils. Das Modell extrahiert aus Fetch-Inhalten teils sehr sauber, etwa bei HTTP Fetch & Extract und URL Construction & Fetch, fällt aber bei Syntheseaufgaben mit Auswahl- und Priorisierungsbedarf sichtbar ab. Besonders bei Web Search & Tool Selection war die Werkzeugwahl stark, die anschließende Verdichtung aber deutlich schwächer.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das eigentliche Produktionsrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, erreicht das Modell nur P2=20 bei Content-Verification-State B2. Auch ohne explizite Halluzination in genau diesem Test ist der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene oder unzureichend verifizierte Fakten als Tool-Ergebnis formuliert, wird die gesamte Tool-Infrastruktur fragwürdig.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, meldet es den Fehlschlag statt Seiteninhalt zu erfinden. Das ist produktionsfähig. Ein System kann auf dieser Basis sauber eskalieren oder erneut planen.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist ein kleiner Rückstand, kein Ausreißer. Das Provenienz-Risiko der offenen Gewichte aus China bleibt für regulierte Umgebungen dennoch ein separater Governance-Punkt.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit Such-, Fetch- und Extraktionsschritten, wenn ein Orchestrator Tool-Calls strikt validiert und jede Synthese gegen Rohquellen rückprüft. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen die Antwort selbst als verlässliche Verdichtung des Tool-Outputs gelten muss. Als Tool-Operator brauchbar. Als letzte Wahrheitsinstanz nicht.