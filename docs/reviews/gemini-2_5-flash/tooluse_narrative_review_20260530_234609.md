**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:46:09


Bedingt deploy, weil Gemini 2.5 Flash valide Tool-Calls produziert und im Gesamtbild brauchbar orchestriert, aber die Synthesetreue mit Combined 71.08 und erkanntem Halluzinationssignal nicht stabil genug für vertrauenskritische Pipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. P1 bei 90 zeigt, dass es MCP-konform arbeitet, valide Calls erzeugt und keinen Retry brauchte. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es korrekt, dass erst web_search nötig ist. Das spricht gegen bloßes Schema-Folgen und für situative Werkzeugwahl. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL prüft, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Fetch-Pipelines. Das Muster ist damit klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei selbst konstruierten Endpunkten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 bei 52.50 ist der eigentliche Bremsfaktor dieses Modells. Es findet Informationen, fasst sie aber nicht konstant präzise zusammen. Das sieht man an HTTP Fetch & Extract, das strukturierte Fakten aus realem Seiteninhalt ziehen soll und mit P2 35 deutlich zu viel Präzision verliert. Für Pipelines, in denen das Tool-Ergebnis fast unverändert in ein Downstream-System geht, ist das kritisch.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb es trotz schwacher Verdichtung im Tool-Pfad. Content-Verification-State A und keine Halluzination in diesem Test sind ein gutes Vertrauenssignal. Der globale Halluzinationsbefund bleibt dennoch ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der den Umgang mit scheiternden Tool-Aufrufen misst, hat Gemini 2.5 Flash keinen Ersatzinhalt erfunden. Es kommuniziert Fehler transparent, statt nicht vorhandenen Seiteninhalt zu behaupten. Genau dieses Verhalten braucht eine produktive Tool-Pipeline.

**Betriebsprofil**

Call 1: 1.26s. MCP-Latenz: 0.77s. Call 2: 4.22s. Total: 37.51s.  
Kosten pro Run: $0.005286.  
Direkte Einordnung: günstig, aber nicht schnell. Das Preisniveau ist attraktiv. Die Gesamtlaufzeit ist für interaktive Orchestrierung eher lang im Verhältnis zur nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines, in denen das Modell primär Tools auswählt, Aufrufe korrekt ausführt und Fehler sauber meldet. Nicht geeignet für Compliance-, Reporting- oder Extraktionsketten, in denen die sprachliche Verdichtung selbst als verlässlicher Output weiterverarbeitet wird. Setzen Sie es als Tool-Orchestrator mit nachgelagerter Validierung ein, nicht als letzte semantische Instanz.