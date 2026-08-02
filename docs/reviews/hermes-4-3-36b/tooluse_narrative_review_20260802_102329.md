**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:29


Bedingt deployen, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Halluzinationsbefund und ungültigem Tool-Call nicht genug Vertrauen für unbeaufsichtigte Produktionspipelines trägt.

**Tool-Execution-Profil**

Hermes 4.3 36B zeigt echte Werkzeugintelligenz, nicht nur starres Call-Muster. Beim Web-Search-&-Tool-Selection-Test erkennt es ohne expliziten Hinweis zuverlässig, dass erst Suche statt direktem Fetch nötig ist. Das spricht für brauchbare Planungslogik in dynamischen MCP-Abläufen. Beim URL-Construction-Test, der korrekte URL-Ableitung und anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 heißt hier: meist funktionsfähig, aber nicht präzise genug für fragile Pipelines mit harter URL-Abhängigkeit. Kritisch bleibt der Gesamtbefund, dass mindestens ein Tool-Call nicht valide war. Da kein Retry erforderlich war, wirkt das weniger wie ein bloßes Formatproblem als wie eine punktuelle Protokoll- oder Ausführungsunsicherheit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 43.33 der klare Schwachpunkt dieses Modells. Besonders bei HTTP Fetch & Extract, Web Search & Tool Selection, URL Construction & Fetch und vor allem Multilingual Search & Synthesis verdichtet es Ergebnisse zu grob, verliert Details oder zieht die falschen Schwerpunkte. Für Architekturen, in denen das Modell Tool-Output in verlässliche Arbeitsantworten übersetzen soll, ist das ein operatives Risiko.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, bleibt das Modell auf der sicheren Seite. Es halluziniert dort nicht und erzielt ein brauchbares Vertrauenssignal. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko: Sobald ein Modell erfundene Inhalte als angebliche Tool-Ergebnisse ausgibt, wird nicht nur eine Antwort schlechter, sondern die Verlässlichkeit der gesamten Tool-Infrastruktur beschädigt.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, reagiert Hermes 4.3 36B produktionsnah. Es kommuniziert den Fehler offen und erfindet keinen Seiteninhalt. Das ist für produktive Systeme akzeptabel und wichtiger als kosmetische Antwortqualität.

**Betriebsprofil**

Total 346.45s pro Run. Call 1 6.11s, MCP-Latenz 1.53s, Call 2 50.10s. Für die gezeigte Qualität klar langsam. Kosten lokal. Wirtschaftlich nur sinnvoll, wenn Open-Weights-Betrieb, Datenkontrolle oder 512K-Kontext wichtiger sind als Durchsatz.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines mit Human-in-the-Loop, transparenter Fehlerbehandlung und klarer Trennung zwischen Tool-Ausführung und finaler Freigabe. Nicht geeignet für autonome Recherche-, Compliance- oder Mehrsprachen-Pipelines, in denen die Antwort selbst als verlässliche Verdichtung des Tool-Outputs dienen muss. Wenn Sie es einsetzen, dann als Orchestrator mit nachgelagerter Verifikation, nicht als letzte Instanz für Faktenzusammenfassung.