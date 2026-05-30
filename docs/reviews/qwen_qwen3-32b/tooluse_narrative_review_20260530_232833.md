**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:33


Bedingt deploy: Qwen 3 32B erzeugt valide Tool-Calls und arbeitet MCP-konform, ist aber wegen erkannter Halluzinationen bei Combined 64.88 kein vertrauenswürdiger Endpunkt für faktenkritische Tool-Pipelines.

**Tool-Execution-Profil**

In der Werkzeugausführung ist das Modell solide. P1 86.67 zeigt, dass es Tools grundsätzlich korrekt ansteuert und keine Retry-Schleife brauchte. Besonders wichtig: Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis statt fetch ein web_search nötig ist, erkennt es die richtige Werkzeugklasse sicher und erreicht P1 100. Das spricht gegen rein schematisches Abarbeiten und für echte Werkzeugwahl unter Kontext.

Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für enge Produktionspfade; P1 80 ist funktional, nicht präzise. Das Muster ist klar: Qwen 3 32B versteht, welches Tool es braucht, verliert aber an Zuverlässigkeit, sobald die Ausführung von selbst erzeugten Zwischenannahmen abhängt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 43.33 ist der eigentliche Schwachpunkt dieses Laufs. In Web Search & Tool Selection und URL Construction & Fetch kann es Ergebnisse noch ordentlich zusammenziehen, aber bei EU License Research und Multilingual Search & Synthesis bricht die Verdichtungsqualität deutlich ein. Für Pipelines, in denen extrahierte Fakten knapp und präzise in eine Folgeentscheidung eingehen, ist das zu instabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Beim Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, halluziniert das Modell trotz Content-Verification-State A. Das ist kein bloßer Qualitätsfehler, sondern ein Sicherheitsrisiko: Ein Modell, das erfundene oder vorab gelernte Inhalte als Tool-Ergebnis ausgibt, unterläuft die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Hier fällt das Modell für produktive Nutzung klar ab. Im Test Tool Failure Handling (404), der misst ob ein fehlgeschlagener Tool-Call transparent gemeldet oder mit erfundenem Inhalt überspielt wird, erzeugt Qwen 3 32B trotz 404 weiter Halluzinationen. Transparente Fehlerkommunikation wäre akzeptabel. Halluzinierter Seiteninhalt trotz Fehler ist produktionskritisch ohne Ausnahme.

**Souveränitätsprofil**

Lokal betreibbar und sehr günstig bei 0.002685 pro Run. Gesamtzeit 31.49s ist für den Output eher langsam. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Damit ist das Modell souveränitätsfreundlich, aber nicht fleet-kompetitiv genug, um seinen Vertrauensnachteil zu kompensieren.

**Fazit & Empfehlung**

Geeignet für interne Recherche- und Vorstrukturierungs-Pipelines, in denen Tool-Aufrufe validiert werden und ein nachgelagerter Prüfschritt jede Aussage gegen den Roh-Output der Tools hält. Nicht geeignet für Compliance, regulatorische Recherche, Incident-Workflows oder autonome Agentenpfade mit Nutzerkontakt. Wenn Sie Qwen 3 32B einsetzen, dann nur als vorgeschalteten Tool-Bediener, nicht als letzte Instanz für faktengebundene Synthese.