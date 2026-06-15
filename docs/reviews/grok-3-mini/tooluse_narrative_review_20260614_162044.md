**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:44


Bedingt deploy, weil die Tool-Aufrufe verlässlich und protokollkonform sind, die inhaltliche Synthese mit Combined 58.25 aber zu schwach bleibt, um unbeaufsichtigt belastbare Tool-Ergebnisse weiterzureichen.

**Tool-Execution-Profil**

Grok 3 Mini zeigt ein stabiles Tool-Execution-Profil. P1 liegt durchgängig bei 80, der Tool-Call war valide und es war kein Retry erforderlich. Das spricht für saubere MCP-Ansteuerung und gegen Formatinstabilität. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis statt fetch ein web_search nötig ist, erkennt das Modell den Werkzeugbedarf brauchbar. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Modellwissen und den anschließenden Fetch misst, arbeitet es ebenfalls solide. Das Muster wirkt nicht rein mechanisch. Das Modell kann zwischen Such- und Abrufpfad unterscheiden. Die Konstanz der P1-Werte zeigt aber auch, dass die eigentliche Grenze nicht in der Tool-Wahl liegt, sondern nach dem Call beginnt: bei der Auswertung des Materials.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher nur eingeschränkt. P2 von 35.83 ist der kritische Wert dieses Runs. Über alle sechs Aufgaben bleibt die Verdichtungsqualität flach: EU License Research fällt auf 20, die übrigen Assets liegen meist nur bei 35 bis 40. Das reicht für grobe Zusammenfassungen, aber nicht für präzise Extraktion, belastbare Compliance-Antworten oder mehrstufige Entscheidungslogik. Für eine Tool-Pipeline ist das kein Schönheitsfehler, sondern ein operatives Risiko: Das Modell ruft die richtigen Quellen ab, überführt sie aber nicht zuverlässig in saubere Aussagen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist der positive Teil des Befunds. Gleichzeitig steht der globale Halluzinationsflag auf true. Damit ist mindestens ein Sicherheitsrisiko im Lauf vorhanden: Das Modell kann erfundene Inhalte als Tool-basierte Ergebnisse ausgeben. Für produktive Infrastrukturen zählt dieser Befund stärker als die formale Tool-Korrektheit.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call statt erfundenem Seiteninhalt misst, halluziniert Grok 3 Mini keinen Ersatzinhalt. Das ist produktionsfähig. P2 von 40 zeigt dennoch nur mäßige Fehlerkommunikation. Das Modell bleibt auf der sicheren Seite, aber nicht auf der präzisesten.

**Betriebsprofil**

Total 48.95s. Call-Latenzen 2.17s und 4.47s, MCP-Latenz 1.52s. Für die erzielte Qualität langsam. Kosten pro Run 0.002812. Günstig, aber nicht günstig genug, um die schwache Synthese zu kompensieren.

**Fazit & Empfehlung**

Geeignet ist Grok 3 Mini für Tool-Pipelines mit klarer externer Nachprüfung: Recherche-Vorstufen, URL-Ermittlung, Webzugriff, einfache Routing- oder Retrieval-Jobs. Nicht geeignet ist es als abschließende Syntheseinstanz für Compliance, regulatorische Auswertung, faktenkritische Wissensverdichtung oder autonome Agenten, die Tool-Ergebnisse ohne Guardrails in Entscheidungen überführen. Wenn Sie es einsetzen, dann als ausführendes Zwischenmodell mit hartem Output-Validation-Layer, nicht als vertrauenswürdigen Endredakteur der Pipeline.