**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:24


Bedingt deploy, weil GPT-5 im Produktionseinsatz brauchbare Tool-Intelligenz zeigt, aber mit ungültigen Tool-Calls und nur moderater Synthesetreue kein Modell ist, dem man eine MCP-Pipeline ohne enge Leitplanken übergeben sollte.

**Tool-Execution-Profil**

Das Modell erkennt Werkzeugbedarf grundsätzlich gut. Beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, arbeitet es sicher und erreicht volle Ausführungstreue. Auch bei Multilingual Search & Synthesis und EU License Research nutzt es die Recherchepfade zuverlässig. Das spricht gegen ein starres Call-Muster und für echte Tool-Wahl.

Die Schwäche liegt in der operativen Präzision. Tool-Call valide ist insgesamt False, und das passt zum URL-Construction-Test: Wenn das Modell die Ziel-URL aus eigenem Wissen ableiten und dann fetch korrekt ausführen muss, fällt es deutlich ab. Für deterministische Pipelines ist das relevant. GPT-5 versteht also meist, welches Werkzeug gebraucht wird, produziert aber nicht durchgehend belastbare Aufrufe. Retry war nicht erforderlich. Das ist eher ein Präzisionsproblem in der Ausführung als ein reines Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 53.33 zeigt, dass GPT-5 gefundene Inhalte nicht stabil genug in präzise, entscheidbare Antworten überführt. Positiv ist HTTP Fetch & Extract, wo strukturierte Fakten aus realem Content brauchbar zusammengeführt werden. Kritisch sind aber starke Einbrüche bei EU License Research und Multilingual Search & Synthesis. Gerade bei mehrdeutigen oder compliance-nahen Ergebnissen fehlt die letzte Bindung an den Quellinhalt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Signal ist das Warnzeichen. Beim EU License Research-Test, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, liegt P2 nur bei 20. Halluzination wurde zwar nicht erkannt. Trotzdem ist das Vertrauensniveau niedrig, weil die Antwort den Mehrwert des Toolings nicht sauber in belastbare Aussage umsetzt. Für Compliance- oder Policy-Pipelines reicht das nicht.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert GPT-5 akzeptabel. Im 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Abruf statt erfundenem Seiteninhalt misst, kommuniziert das Modell den Fehlschlag überwiegend sauber. Halluzinierter Ersatzinhalt wurde nicht beobachtet. Das ist ein produktionsrelevanter Pluspunkt.

**Betriebsprofil**

Total 191.61s pro Run. Call 1: 6.24s. MCP-Latenz: 0.74s. Call 2: 24.96s. Langsam für die erzielte Qualität. Kosten: nicht extern bepreist, hier local. Im Verhältnis zur Leistung kein Effizienzsignal.

**Fazit & Empfehlung**

Geeignet für assistierte Recherche-Pipelines, in denen ein nachgelagerter Validator Tool-Calls und Zusammenfassungen prüft. Nicht geeignet für autonome MCP-Strecken mit URL-Ableitung, Compliance-Ausgaben oder anderen Aufgaben, bei denen die Antwort strikt an Tool-Belege gebunden sein muss. Wenn Sie GPT-5 einsetzen, dann mit eng geführter Tool-Auswahl, Schema-Validierung und einer harten Quellprüfung vor jeder finalen Ausgabe.