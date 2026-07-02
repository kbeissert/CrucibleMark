**Deployment-Urteil**

> **Erstellt am:** 02.07.2026, 12:30:34


Bedingt deploy, weil Claude Opus 4.8 keine Halluzination im Benchmark gezeigt hat, aber keine durchgehend validen Tool-Calls liefert und die Gesamtleistung vor allem an der schwankenden Synthese- und Fehlerbehandlung hängt.

**Tool-Execution-Profil**

Bei der Werkzeugwahl zeigt das Modell klare situative Intelligenz statt bloßem Musterfolgen. Im Test Web Search & Tool Selection, der prüft, ob ohne Hinweis eine Suche statt eines direkten Fetch nötig ist, wählt es das richtige Werkzeug sicher. Das spricht für brauchbare Orchestrierungsfähigkeit in offenen Aufgaben.

Schwächer wird es bei der Ausführungsschärfe. Im Test URL Construction & Fetch, der die eigenständige Ableitung der Ziel-URL prüft, konstruiert es die URL meist brauchbar, aber nicht präzise genug für deterministische Pipelines. Dazu passt das globale Signal tool_call_valid=false. Das Modell versteht also, welches Werkzeug gebraucht wird, produziert aber nicht in jedem Fall protokollsaubere, verlässlich anschlussfähige Calls. Retry war nicht nötig. Das ist kein Formatkollaps, sondern eher ein Präzisionsproblem in der letzten Meile der Tool-Nutzung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung von 60 zeigt, dass Claude Opus 4.8 gefundene Informationen häufig nutzbar zusammenfasst, aber nicht stabil präzise genug für extraktionsnahe Workflows. Besonders sichtbar wird das bei Multilingual Search & Synthesis: Die Recherche über Sprachgrenzen gelingt, die Verdichtung auf Deutsch verliert jedoch an Genauigkeit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, blieb das Modell auf der sicheren Seite. Keine erkannte Halluzination. Das ist das wichtigere Vertrauenssignal: Es erfindet keine aktuellen Compliance-Fakten, auch wenn die Verdichtung nur durchschnittlich ausfällt.

**Fehlerresilienz**

Im 404-Test, der misst, ob ein fehlgeschlagener Tool-Call transparent kommuniziert wird, halluziniert das Modell keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die P2-Leistung von 40 zeigt aber, dass die Fehlerkommunikation nicht sauber genug geführt wird. Für Produktion heißt das: eher defensiv und unvollständig als erfinderisch. Das ist akzeptabel, solange der aufrufende Orchestrator Fehlerzustände selbst streng behandelt.

**Betriebsprofil**

Total 95.11s pro Run. Call-Latenzen 2.22s und 11.09s, MCP-Latenz 2.54s. Langsam für die erzielte Leistung. Preisniveau hoch: $5.0 pro 1M Input und $25.0 pro 1M Output. Für diese Tool-Qualität teuer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit starker externer Kontrolle: Recherche-Orchestrierung, mehrstufige Web-Aufgaben, agentische Vorstrukturierung. Nicht geeignet als unbeaufsichtigte Endinstanz für Compliance, präzise Faktenextraktion oder strikt deterministische Tool-Chains. Deploy nur dann, wenn URL-Validierung, Tool-Call-Schema-Prüfung und harte Fehlerbehandlung außerhalb des Modells abgesichert sind.