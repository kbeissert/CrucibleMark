**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:46:24


Bedingt deploy, weil die Tool-Ausführung belastbar ist, aber die Synthesequalität mit P2 55.83 zu oft Präzision verliert und zugleich ein Halluzinationssignal vorliegt. Der Combined-Score von 71.75 reicht für produktive Tool-Pipelines nur dann, wenn nachgelagerte Validierung die Endantwort kontrolliert.

**Tool-Execution-Profil**

Dieses Modell kann man mit einer MCP-Tool-Infrastruktur arbeiten lassen. Die Call-Validität ist gegeben, Retry war nicht nötig, und P1 90 zeigt stabile Protokolltreue. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell den Bedarf an web_search sauber und erreicht P1 100. Das spricht gegen ein bloß starres Fetch-Muster.

Schwächer ist es beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL prüft. Mit P1 80 konstruiert es URLs oft brauchbar, aber nicht präzise genug für strikt deterministische Pipelines. Das Muster ist klar: gute Werkzeugwahl, etwas weniger Präzision bei selbst abgeleiteten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die schwachen Werte in HTTP Fetch & Extract mit P2 15 sowie in Multilingual Search & Synthesis und EU License Research mit jeweils P2 40 zeigen, dass das Modell abgerufene Inhalte nicht konsistent in saubere, belastbare Endantworten überführt. Für Research reicht das, für operative Ausgaben mit Faktenbindung nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, bleibt es formal im verifizierten Inhaltsraum. Content-Verification-State A und keine Halluzination in diesem Test sind ein gutes Vertrauenssignal. Das globale Halluzinationsflag bleibt trotzdem ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, leidet die Vertrauenskette der gesamten Pipeline.

**Fehlerresilienz**

Hier ist das Modell produktionsreif. Im Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlschlagenden Abruf misst, erreicht es P2 100 und halluziniert keinen Seiteninhalt. Es meldet den Fehler, statt Ersatzinhalt zu erfinden. Genau dieses Verhalten ist in produktiven Agent- und Retrieval-Pipelines akzeptabel.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit für souveräne Deployments praktisch attraktiv. Leistungsseitig liegt es mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.62 und bleibt damit fleet-nah. Für eine GGUF-Workstation-Variante ist das ein solides Verhältnis aus Unabhängigkeit und Nutzwert.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines, in denen das Modell Tools auswählen, Aufrufe sauber ausführen und Fehler transparent melden soll. Nicht geeignet als letzte Instanz für faktenkritische Zusammenfassungen, Compliance-Ausgaben oder mehrsprachige Verdichtung ohne zusätzliche Prüfung. Empfehlung: als Tool-Orchestrator und Vorverarbeiter einsetzen, nicht als ungeprüften Synthese-Endpunkt.