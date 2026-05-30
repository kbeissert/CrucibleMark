**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:38


Bedingt deploy, weil die Tool-Calls formal valide sind, aber die Gesamtleistung mit 42.33 und vor allem die schwache Synthesetreue für vertrauenskritische MCP-Pipelines nicht ausreicht.

**Tool-Execution-Profil**

Das Modell spricht das MCP-Protokoll sauber an. Tool-Call valide: true, Retry war nicht nötig. Das ist die Mindestvoraussetzung für Integration und sie ist erfüllt. Die eigentliche Schwäche liegt nicht im Format, sondern in der Werkzeugwahl.

Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden soll, bleibt es mit P1=40 deutlich zu unsicher. Beim URL-Construction-Test, der korrekte Ziel-URLs aus eigenem Wissen ableiten und dann fetch ausführen soll, landet es ebenfalls bei P1=40. Das Muster spricht nicht für robuste Tool-Intelligenz, sondern für begrenzte Planungspräzision. Positiv ist nur HTTP Fetch & Extract mit P1=80: Wenn die richtige Ressource bereits vorliegt, kann es den Abruf zuverlässig ausführen. Für dynamische Pipelines, in denen das Modell den nächsten Tool-Schritt selbst bestimmen muss, ist das zu wenig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2=31.67 zeigt, dass die eigentliche Verdichtung der abgerufenen Inhalte der Engpass ist. Besonders auffällig sind EU License Research mit P2=20, HTTP Fetch & Extract mit P2=15 und URL Construction & Fetch mit P2=15. Das Modell holt also teils verwertbare Daten, transformiert sie aber nicht stabil in belastbare Antworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt P2 bei 20 bei Content-Verification-State B2. Dort wurde zwar keine Halluzination markiert, aber die Bindung an das Tool-Ergebnis bleibt schwach. Zusätzlich ist der globale Halluzinationsflag true. Das ist kein Qualitätsdetail, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnisse ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Hier verhält sich das Modell produktionsfähig. Im 404-Test, der transparente Kommunikation bei fehlschlagendem Abruf statt erfundenem Seiteninhalt misst, erreicht es P2=80. Es halluziniert trotz Fehler nicht. Das ist für reale Pipelines wichtig, weil Tool-Ausfälle regelmäßig auftreten und sauber propagiert werden müssen.

**Souveränitätsprofil**

Lokal betreibbar und kostenseitig attraktiv, aber nicht fleet-kompetitiv genug. Das Modell läuft in der Gruppe local_sovereign und liegt mit -5.32 Punkten unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet für souveräne, kostensensitive Pipelines mit enger Tool-Führung: feste Tool-Reihenfolgen, bekannte Endpunkte, klare Validierung nach dem Modellschritt. Nicht geeignet für Compliance-, Recherche- oder Agentic-Orchestrierungs-Pipelines, in denen das Modell selbst Tools wählen, aktuelle Web-Inhalte belastbar verdichten und als einzige Syntheseinstanz vertrauenswürdig bleiben muss. Für Produktion nur hinter Guardrails, Source-Gating und nachgelagerter Ergebnisprüfung einsetzen.