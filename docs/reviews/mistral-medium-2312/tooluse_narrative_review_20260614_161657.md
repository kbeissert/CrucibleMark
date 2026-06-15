**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:16:57


Nicht deploy für autonome MCP-Pipelines, weil das Modell trotz nur schwachem Gesamtergebnis vor allem an zwei produktionskritischen Stellen scheitert: ungültige Tool-Calls und erkannte Halluzination bei zugleich erforderlichem Retry.

**Tool-Execution-Profil**

Mistral Medium 1.0 führt einfache, klar vorgezeichnete Tool-Pfade brauchbar aus, zeigt aber keine verlässliche Werkzeugintelligenz. Das sieht man direkt an der Schere zwischen **Web Search & Tool Selection**, das prüft, ob ohne Hinweis search statt fetch gewählt wird, mit P1 35, und **URL Construction & Fetch**, das die Ableitung einer Ziel-URL und den anschließenden Fetch misst, mit P1 75. Das Modell kann also bekannte oder naheliegende Abrufmuster bedienen, erkennt aber dynamische Recherchebedarfe nicht stabil. Für MCP-Orchestrierung ist das ein Kernproblem, weil nicht der einzelne Call zählt, sondern die richtige Entscheidung vor dem Call. Dass ein Retry nötig war, spricht hier eher für ein Protokoll- oder Formatproblem als für reines Fachverständnis. Für Produktion ist das dennoch relevant: Ein Modell, das erst nach Korrekturschleife gültige Calls liefert, erhöht Komplexität und Fehlerrisiko im Controller.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 42.5 zeigt, dass die Verdichtung häufig zu grob oder unpräzise bleibt. Positiv ist **HTTP Fetch & Extract**, das strukturierte Fakten aus echtem Seiteninhalt prüft, mit P2 60. Negativ sind **EU License Research** mit P2 20 und **Web Search & Tool Selection** mit P2 20. Besonders bei mehrsprachiger Recherche bleibt die Zusammenführung unstetig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot **EU License Research**, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, liegt der Content-Verification-State nur bei B2 und die Synthese ist schwach. Auch wenn dort keine Halluzination markiert wurde, ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, verliert die gesamte Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Hier verhält sich das Modell akzeptabel. Im Test **Tool Failure Handling (404)**, der transparentes Verhalten bei fehlschlagendem Abruf prüft, erreicht es P2 80 und halluziniert keinen Ersatzinhalt. Das ist produktionsreif. Ein fehlgeschlagenes Tool wird als Fehler behandelt, nicht als Einladung zum Erfinden.

**Betriebsprofil**

Call 1: 5.21s. MCP-Latenz: 0.21s. Call 2: 4.50s. Total: 59.59s.  
Kosten/Run: local.  
Für die gezeigte Leistung ist das Gesamtprofil langsam.

**Fazit & Empfehlung**

Geeignet höchstens für assistierte Pipelines mit hartem Guardrailing, strikt validierten Tool-Schemas und externer Ergebnisprüfung nach jedem Schritt. Nicht geeignet für autonome Rechercheketten, Compliance-nahe Workflows oder Routing-Aufgaben, in denen das Modell selbst zwischen Suche, Abruf und Synthese wählen muss. Wenn Sie dem Modell nur klar definierte Fetch-Aufgaben geben und Fehler strikt abfangen, ist ein begrenzter Einsatz denkbar. Als eigenständige MCP-Schaltinstanz trägt es zu wenig Vertrauen.