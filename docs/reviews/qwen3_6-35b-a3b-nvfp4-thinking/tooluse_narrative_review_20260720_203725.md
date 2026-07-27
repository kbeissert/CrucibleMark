**Deployment-Urteil**

> **Erstellt am:** 20.07.2026, 20:37:25


Bedingt deploy, weil die Tool-Nutzung insgesamt brauchbar ist, aber der kombinierte Befund von 68.00 bei zugleich invalidem Tool-Call und schwacher Synthesetreue zu wenig Vertrauen für autonome MCP-Pipelines gibt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, aber keine durchgehend saubere Ausführung. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den richtigen Pfad sicher und erreicht P1 100. Das spricht gegen ein starres Fetch-zuerst-Muster. Beim URL-Construction-Test, der die eigenständige Herleitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für eng geführte Pipelines. Der globale Befund "Tool-Call valide: false" ist hier der operative Knackpunkt. Das Modell versteht meist, welches Tool gebraucht wird, produziert aber nicht in jedem Fall protokollsaubere Aufrufe. Für MCP-Orchestrierung mit strenger Schema-Prüfung braucht es deshalb eine Guardrail-Schicht, die Calls validiert und gegebenenfalls korrigiert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 56.67 ist für produktive Ergebnisaufbereitung zu niedrig, weil die Schwäche nicht in Randfällen steckt, sondern in der Kernaufgabe der Verdichtung. Sichtbar wird das vor allem bei EU License Research mit P2 20, obwohl andere Aufgaben wie URL Construction & Fetch mit P2 80 deutlich besser laufen. Das Muster ist damit ungleichmäßig: einfache Extraktion gelingt eher, verlässliche Zusammenführung und Priorisierung von Rechercheergebnissen nicht stabil genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot zu EU License Research ist hier das Warnsignal. Es halluziniert zwar nicht offen, aber das sehr schwache Ergebnis deutet darauf hin, dass es aktuelle Web-Befunde nicht sauber in belastbare Aussagen überführt. Für Compliance-, Policy- oder Lizenzpipelines ist genau das zu wenig. Das Vertrauen in den Recherchepfad bleibt begrenzt, auch ohne formalen Halluzinationsfund.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, reagiert das Modell akzeptabel. P2 60 ist keine starke Fehlerkommunikation, aber der wichtige Punkt ist: Es erfindet keinen Seiteninhalt. Halluzination trotz Fehler wurde nicht erkannt. Das macht es produktionstauglich für Umgebungen, in denen Fehler explizit an den aufrufenden Dienst zurückgegeben werden dürfen.

**Betriebsprofil**

Call 1: 8.53s. MCP-Latenz: 1.37s. Call 2: 28.72s. Total: 231.72s. Lokal betrieben, aber für die gezeigte Leistung langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Assistenz- und Recherchepipelines mit Human-in-the-loop, wo Tool-Wahl wichtig ist und Ergebnisse nachgelagert geprüft werden. Nicht geeignet für autonome Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen Tool-Ausgaben präzise verdichtet und MCP-Calls strikt valide sein müssen. Wer es einsetzt, sollte Call-Validation, Output-Checking und klare Failure-Handoffs verpflichtend vorschalten.