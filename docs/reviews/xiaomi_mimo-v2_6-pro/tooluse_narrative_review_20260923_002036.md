**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:20:36


Bedingt deploy, weil die Tool-Nutzung stark ist, das Modell aber bei Tool-Fehlern halluziniert und damit das Vertrauen in eine MCP-Pipeline beschädigt. Der Gesamteindruck ist gut, aber der Sicherheitsbefund wiegt schwerer als der Combined-Score von 75.04.

**Tool-Execution-Profil**

Xiaomi MiMo V2.6 Pro zeigt echte Werkzeugintelligenz statt eines starren Fetch-Musters. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf an web_search sauber und erreicht P1 100. Das spricht für brauchbare Planungslogik in dynamischen Pipelines. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Abruf misst, arbeitet es solide, aber nicht deterministisch genug für hochstrikte Flows. P1 80 ist gut, aber nicht hart belastbar. Kritisch ist das Protokollsignal: Tool-Call valide ist false. Das heißt nicht, dass es Tools grundsätzlich verfehlt, aber die MCP-Ausgabe war mindestens in einem relevanten Fall nicht sauber genug für reibungslosen Produktionsbetrieb. Positiv ist, dass kein Retry erforderlich war. Das wirkt eher wie ein Validitäts- oder Formatmangel im Call als wie ein tieferes Verständnisproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 59.17 zeigt, dass MiMo Ergebnisse oft korrekt einsammelt, sie aber beim Verdichten nicht präzise genug hält. Das sieht man an EU License Research mit P2 40 und Tool Failure Handling (404) mit P2 35. Besser ist es bei Multilingual Search & Synthesis mit P2 80 und bei URL Construction & Fetch mit P2 80.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es formal auf dem Tool-Pfad und halluziniert dort nicht. Das ist wichtig für Compliance-nahe Recherchen. Trotzdem steht global Halluzination erkannt auf true. Damit liegt kein bloßer Qualitätsmangel vor, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Aussagen als Tool-Ergebnis ausgibt, wird die gesamte Infrastruktur unzuverlässig.

**Fehlerresilienz**

Hier fällt das Modell klar durch. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt abgrenzt, halluziniert MiMo trotz fehlgeschlagenem Tool-Call Seiteninhalt. Das ist produktionskritisch ohne Ausnahme. Ein Agent darf nach einem 404 nur den Fehlerzustand melden oder eine neue Suche vorschlagen. Er darf keinen Inhalt rekonstruieren.

**Betriebsprofil**

Total 285.77s. Call 1 5.81s, MCP-Latenz 0.93s, Call 2 40.89s. Für die gezeigte Leistung langsam. Kosten/Run: local. Preis laut Modellkarte günstig bis moderat für Frontier-Klasse, aber die Laufzeit frisst den Vorteil in interaktiven Pipelines auf.

**Fazit & Empfehlung**

Geeignet für überwachte Research- und Orchestrierungs-Pipelines, in denen ein Controller Tool-Antworten validiert, Fehlerzustände abfängt und finale Aussagen prüft. Nicht geeignet für autonome Retrieval-, Compliance- oder Incident-Workflows, in denen Tool-Fehler robust und wahrheitsgemäß behandelt werden müssen. Wenn Sie MiMo einsetzen, dann nur mit strikter Response-Validierung, Hard-Gates bei 4xx/5xx und einer Policy, die unbelegte Synthese konsequent verwirft.