**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:21:02


Bedingt deploy, weil die Tool-Ausführung stark ist, aber erkannte Halluzinationen bei ungültigem Tool-Verhalten und ein Combined-Score von 68.62 das Modell für unbeaufsichtigte MCP-Pipelines derzeit unsicher machen.

**Tool-Execution-Profil**

Upstage Solar Pro4 zeigt echte Werkzeugintelligenz, nicht nur starres Ablaufverhalten. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es das richtige Tool zuverlässig. Das spricht für brauchbare Planungslogik in dynamischen Pipelines. Auch beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist die Leistung solide, aber nicht deterministisch genug für jede Produktionskette. Der P1-Wert von 90 stützt dieses Bild: hohe operative Fähigkeit, aber keine durchgehend protokollsaubere Ausführung. Kritisch ist, dass der Tool-Call insgesamt nicht valide war. Das ist kein bloßer Schönheitsfehler, sondern ein MCP-Risiko, weil ein Orchestrator sich auf formale Korrektheit verlassen muss. Positiv ist nur, dass kein Retry nötig war; das Problem lag also eher in der Ausführung als in einer instabilen Formatierungsschleife.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Der P2-Wert von 66.67 wirkt auf den ersten Blick brauchbar, aber die Asset-Streuung ist hoch. Web Search & Tool Selection gelingt auch in der Verdichtung sehr gut, während Multilingual Search & Synthesis bei der deutschsprachigen Zusammenführung sprachübergreifender Recherche deutlich einbricht. Für Pipelines, die aus Tool-Outputs belastbare Zusammenfassungen erzeugen sollen, ist das zu inkonsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, bleibt es innerhalb der Beschaffungskette und halluziniert nicht. Das ist das stärkste Vertrauenssignal im Review. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Infrastruktur ihren Verifikationswert.

**Fehlerresilienz**

Hier fällt das Modell klar durch. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf prüft, erfindet Solar Pro4 Seiteninhalt statt den Fehler sauber offenzulegen. Das ist produktionskritisch ohne Ausnahme. Eine Pipeline kann mit expliziten Fehlern arbeiten. Sie kann nicht sicher mit plausibel klingendem Ersatzinhalt arbeiten.

**Betriebsprofil**

Total 176.50s pro Run. Call 1: 2.40s. MCP-Latenz: 1.31s. Call 2: 25.71s. Langsam für diese Ergebnisqualität. Kosten/Run: local. Preis laut Modellprofil sehr günstig, aber die Laufzeit drückt die praktische Effizienz.

**Fazit & Empfehlung**

Geeignet für beaufsichtigte Agenten-Pipelines mit starker Guardrail-Schicht, expliziter Tool-Output-Validierung und harter Fehlerbehandlung vor jeder Synthese. Nicht geeignet für autonome MCP-Workflows, Compliance-Strecken oder Retrieval-Ketten, in denen ein Tool-Fehler transparent propagiert werden muss. Wenn Sie es einsetzen, dann als planungsstarken Orchestrator mit nachgelagerter Verifikation, nicht als vertrauenswürdige letzte Instanz.