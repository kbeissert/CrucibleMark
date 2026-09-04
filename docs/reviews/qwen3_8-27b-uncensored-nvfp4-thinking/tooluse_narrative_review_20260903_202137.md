**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:21:37


Bedingt deploy, weil die Tool-Ausführung stark ist, aber der invalide Tool-Call und die erkannte Halluzination das Vertrauen in produktive Tool-Pipelines begrenzen. Der Gesamteindruck ist gut, aber nicht sicher genug für unkontrollierte Übergabe der Infrastruktur.

**Tool-Execution-Profil**

Qwen 3.8 27B Uncensored zeigt echte Werkzeugintelligenz statt bloßem Schema-Folgen. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es sauber, dass erst web_search nötig ist. Das spricht für brauchbare Planungslogik in offenen Aufgaben.

Schwächer wird es bei der Ausführungsschärfe. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für harte Produktionspfade. Dazu kommt das zentrale Protokollsignal: mindestens ein Tool-Call war nicht valide. Da kein Retry nötig war, wirkt das nicht wie ein bloßes Formatstottern, sondern eher wie ein punktuelles Zuverlässigkeitsproblem in der Call-Bildung. Für MCP-konforme Orchestrierung ist das relevant.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 59.17 der klare Schwachpunkt. Besonders beim HTTP-Fetch-&-Extract-Test, der präzise Fakten aus realem Seiteninhalt ziehen soll, verliert das Modell an Genauigkeit. Es kann Ergebnisse zusammenfassen, aber nicht konstant präzise genug für Compliance-, Policy- oder Extraktionspipelines.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training kommen, halluziniert es nicht. Das ist der wichtigste Entlastungspunkt. Gleichzeitig bleibt das globale Halluzinationssignal ein Sicherheitsrisiko. In einer Tool-Pipeline ist eine erfundene Tatsache nicht nur ein Qualitätsfehler, sondern ein Vertrauensbruch gegen die gesamte Infrastruktur.

**Fehlerresilienz**

Akzeptabel für Produktion mit Aufsicht. Im 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Aufrufen statt erfundenem Ersatzinhalt misst, hat das Modell keinen Seiteninhalt halluziniert. Die Fehlerkommunikation war damit grundsätzlich ehrlich. P2 60 zeigt aber, dass die Erklärung des Fehlers nicht immer sauber genug in Folgeschritte übersetzt wird.

**Betriebsprofil**

Call 1: 6.81s. MCP-Latenz: 1.25s. Call 2: 58.58s. Total: 399.86s.  
Lokal: günstig.  
Für die gelieferte Leistung insgesamt langsam.

**Fazit & Empfehlung**

Geeignet für lokale Research-, Search-Assist- und operatorengeführte Agent-Pipelines, in denen Tool-Wahl wichtiger ist als hochpräzise Verdichtung und jeder Tool-Output nachgelagert geprüft wird. Nicht geeignet für autonome Compliance-, Extraktions- oder Entscheidungsstrecken, die auf strikt valide MCP-Calls und belastbare, quellentreue Synthese angewiesen sind. Wer es einsetzt, sollte Tool-Call-Validierung, Output-Grounding und eine harte Post-Processing-Kontrolle verpflichtend davor setzen.