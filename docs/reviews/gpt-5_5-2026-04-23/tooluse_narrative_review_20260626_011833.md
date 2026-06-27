**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:33


Bedingt deploy, weil die Tool-Ausführung insgesamt stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen in unbeaufsichtigte MCP-Pipelines begrenzen.

**Tool-Execution-Profil**

GPT-5.5 zeigt klare Werkzeugintelligenz statt bloßem Musterfolgen. Beim Web Search & Tool Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den richtigen Zugriffspfad sicher und erzielt volle Ausführungstreue. Auch beim Multilingual Search & Synthesis-Test arbeitet es tool-seitig sauber. Das spricht für brauchbare Planungsfähigkeit in dynamischen Pipelines.

Weniger stabil ist es bei präzisen, deterministischen Aufrufen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, ist die Leistung brauchbar, aber nicht ausfallsicher. Der globale Befund „Tool-Call valide: False“ ist hier entscheidend. Das Problem liegt nicht an Retry-Bedarf oder Formatdrift, sondern an mindestens einem realen Protokoll- oder Aufruffehler im ersten Durchlauf. Für MCP-Orchestrierung heißt das: gute Tool-Wahl, aber keine garantierte Call-Sauberkeit ohne Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur bedingt zuverlässig. Die P2-Leistung ist der schwächste Teil des Profils. Besonders beim HTTP Fetch & Extract-Test, der strukturierte Fakten aus echtem Seiteninhalt verlangt, bricht die Verdichtungsqualität deutlich ein. GPT-5.5 findet also häufig die Quelle, verliert aber bei Zahlen, Eigennamen oder Detailtreue an Präzision. Für produktive Pipelines ist das kritischer als reine Recherchefehler, weil der Verlust erst in der Antwort sichtbar wird.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell grundsätzlich auf dem Werkzeugpfad und halluziniert nicht. Das ist das wichtigere Vertrauenssignal. Trotzdem bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, unterminiert es die Verlässlichkeit der gesamten Infrastruktur, auch wenn der Honeypot selbst sauber war.

**Fehlerresilienz**

Akzeptabel für Produktion mit Aufsicht. Beim Tool Failure Handling (404)-Test, der die Reaktion auf einen fehlschlagenden Tool-Call misst, kommuniziert GPT-5.5 den Fehler transparent und erfindet keinen Seiteninhalt. Das ist die Mindestanforderung für robuste Tool-Pipelines. Die Ausführungstreue in diesem Asset bleibt aber schwach. Es scheitert also nicht am Ehrlichkeitsverhalten, sondern an der operativen Stabilität im Fehlerpfad.

**Betriebsprofil**

Call 1: 25.37s. Call 2: 15.28s. MCP-Latenz: 1.20s. Total: 251.09s. Langsam.  
Preis: $5.0/1M Input, $30.0/1M Output. Teuer.  
Für die gelieferte Leistung kein effizientes Kosten-Latenz-Profil.

**Fazit & Empfehlung**

Geeignet für recherchestarke, überwachte MCP-Pipelines mit nachgelagerter Validierung, etwa Web-Recherche, mehrsprachige Informationsbeschaffung und Tool-routing mit Human-in-the-loop. Nicht geeignet für vollautomatische Pipelines, in denen Fetch-Ergebnisse präzise extrahiert und ohne Zweitprüfung weiterverarbeitet werden, etwa Compliance-Summarys, strukturierte Datenerfassung oder agentische Ketten mit hartem Verlass auf korrekte Tool-Calls.