**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:50:18


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 73.17 nur dann reicht, wenn nachgelagerte Validierung die Antwortinhalte absichert. Halluzination wurde nicht erkannt, aber der Tool-Call war nicht durchgängig valide.

**Tool-Execution-Profil**

Grok 4.6 zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Im Test Web Search & Tool Selection, der prüft, ob ohne Hinweis search statt fetch gewählt wird, trifft es die Werkzeugwahl sauber. Das spricht für brauchbare Orchestrierung in dynamischen MCP-Pipelines. Auch EU License Research und Multilingual Search & Synthesis liefen auf P1-Niveau zuverlässig.

Schwächer ist die Präzision bei der Ausführung nach der Entscheidung. Beim URL-Construction-Test, der die eigenständige Ableitung der Zieladresse misst, konstruiert es die URL brauchbar, aber nicht deterministisch genug für fragile Fetch-Strecken. Das passt zum Befund tool_call_valid=false: Das Modell versteht meist, welches Werkzeug gebraucht wird, produziert aber nicht in jedem Schritt einen formal sauberen, belastbaren Call. Retry war nicht nötig. Das ist eher ein Präzisionsproblem im Call selbst als ein Verständnisproblem der Aufgabe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 54 zeigt eine klare Schere: HTTP Fetch & Extract gelingt sehr gut, aber bei EU License Research und Multilingual Search & Synthesis fällt die Verdichtung deutlich ab. Für produktive Pipelines heißt das: Rohdaten werden geholt, aber die letzte Meile der inhaltlichen Verdichtung ist nicht konstant genug für Compliance, Policy oder Executive Summaries ohne Kontrolle.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil gemischt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, lag P2 bei 20. Zwar wurde keine Halluzination erkannt, aber das Ergebnis wirkt nicht sauber am beschafften Tool-Content verankert. Das ist kein Sicherheitsbruch, aber ein Warnsignal gegen unüberwachte Nutzung in zeitkritischen Faktenlagen.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call misst, erfindet Grok 4.6 keinen Seiteninhalt. Das ist produktionsreif. Die P2 von 40 zeigt zwar schwache Nutzwert-Kommunikation im Fehlerfall, aber keine gefährliche Kompensation durch erfundene Fakten.

**Betriebsprofil**

Total 203.42s: langsam. Einzelcalls 6.81s und 25.22s, MCP-Latenz 1.87s. Preis: $2.0/1M Input, $6.0/1M Output, bei >200K Prompt-Tokens doppelter Tarif. Für die gezeigte Leistung nicht günstig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Wahl, Rechercheanstoß und sichere Fehlerbehandlung wichtiger sind als perfekte Ergebnisverdichtung. Gut einsetzbar für Search-Routing, Web-Enrichment und operator-assistierte Research-Flows. Nicht erste Wahl für Compliance, regulatorische Auswertung, mehrsprachige Synthesen oder jede Pipeline, in der die textliche Zusammenfassung direkt als verlässliches Endprodukt weiterverarbeitet wird. Hier braucht es Evidenz-Zitierung, strukturierte Post-Validation oder einen zweiten Prüfschritt.