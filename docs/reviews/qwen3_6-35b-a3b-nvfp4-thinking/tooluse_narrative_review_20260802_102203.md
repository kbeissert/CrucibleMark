**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:03


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und die schwache Synthesetreue das Vertrauen in produktive Tool-Pipelines begrenzen. Der Gesamteindruck ist gut, aber nicht robust genug für unbeaufsichtigte High-Trust-Flows.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis web_search statt fetch gewählt wird, reagiert es korrekt und erreicht volle Ausführungssicherheit. Das ist ein gutes Signal für dynamische MCP-Pipelines. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließendes Fetch prüft, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 heißt: meist richtig, aber nicht präzise genug für Flows, in denen eine falsch gebildete URL sofort Folgefehler erzeugt.

Kritisch ist der globale Befund „Tool-Call valide: false“. Das spricht weniger gegen die grundsätzliche Toolwahl als gegen Protokolldisziplin im einzelnen Aufruf. Da kein Retry nötig war, wirkt das nicht wie ein anhaltendes Formatversagen, sondern wie eine punktuelle Inkonsistenz. Für MCP-Orchestrierung ist das trotzdem relevant, weil ein einzelner invalider Call die Pipeline unterbrechen kann.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 56.67 der klare Schwachpunkt dieses Laufs. Besonders EU License Research und HTTP Fetch & Extract zeigen, dass das Modell abgerufene Inhalte nicht stabil in belastbare, präzise Endantworten überführt. Für Retrieval allein reicht das, für entscheidungsreife Zusammenfassungen nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, liegt P2 bei nur 20. Zwar wurde dort keine Halluzination markiert, aber der Gesamtlauf trägt Halluzinationsbefund. Das ist ein Sicherheitsrisiko, kein bloßer Qualitätsfehler. Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als Ergebnis ausgibt, wird die gesamte Infrastruktur fragwürdig.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Call misst, reagiert das Modell akzeptabel. P2 80 und kein halluzinierter Seiteninhalt zeigen, dass es Fehler eher offenlegt als mit erfundenem Ersatzmaterial zu verdecken. Das ist produktionsfähig und wichtiger als hohe Eloquenz.

**Betriebsprofil**

Call 1: 7.92s. MCP-Latenz: 1.06s. Call 2: 27.59s. Total: 219.40s.  
Kosten/Run: local.  
Direkte Einordnung: günstig im Betrieb, aber langsam im Gesamtdurchlauf relativ zur erzielten Synthesequalität.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines mit menschlichem Review, vor allem für Recherche, Tool-Routing und mehrsprachige Vorarbeit. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die Endantwort ohne Nachkontrolle belastbar sein muss. Wenn Sie es einsetzen, dann als Tool-Operator vor einem strengeren Verifier oder als Zwischenagent, nicht als letzte Instanz.