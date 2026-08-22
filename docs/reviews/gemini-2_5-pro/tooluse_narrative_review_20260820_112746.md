**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 11:27:46


Bedingt deploy, weil die Tool-Nutzung stark ist, aber die Synthesetreue für produktive Tool-Pipelines noch zu inkonsistent ausfällt. Das Gesamtbild ist brauchbar, doch der invalide Tool-Call und die schwache Verdichtung begrenzen das Vertrauensniveau.

**Tool-Execution-Profil**

Gemini 2.5 Pro zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung zuverlässig. Das spricht für brauchbare Orchestrierungsfähigkeit in dynamischen MCP-Pipelines. Auch Multilingual Search & Synthesis und EU License Research liegen bei der Ausführung stark, was die operative Tool-Nutzung stützt.

Die Schwäche liegt weniger in der Wahl des Werkzeugs als in der Protokollsauberkeit der Ausführung. Der Tool-Call war nicht durchgehend valide, obwohl kein Retry nötig war. Das deutet eher auf Format- oder Call-Strenge als auf Verständnisprobleme. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet das Modell funktional, aber nicht deterministisch genug für fragile Automationsketten. Für robuste MCP-Setups mit Validierungsschicht ist das akzeptabel. Für direkt durchgereichte Calls ohne Guardrails ist es zu riskant.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung von 60 zeigt, dass Gemini 2.5 Pro extrahierte Informationen oft brauchbar zusammenführt, aber nicht konstant präzise genug verdichtet. Das sieht man deutlich an EU License Research mit schwacher Verdichtung trotz korrekter Tool-Nutzung. Dagegen gelingen HTTP Fetch & Extract und Multilingual Search & Synthesis wesentlich stabiler.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, halluziniert das Modell nicht. Das ist das entscheidende Vertrauenssignal. Der niedrige Wert ist hier also kein Sicherheitsbruch, sondern ein Problem der Zusammenfassung und Belegtreue.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsfähig. Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt stellt, erfindet Gemini 2.5 Pro keinen Seiteninhalt. Das ist der richtige Modus für produktive Systeme. Die Ausführung selbst bleibt mit P1 40 fehleranfällig, aber die Antwortseite bleibt ehrlich. Das kann man mit Retries und Fehlerbehandlung auffangen.

**Betriebsprofil**

Total 111.64s. Einzelaufrufe 7.63s und 10.05s. MCP-Latenz 0.92s. Langsam im Gesamtlauf. Preis: $1.25/1M Input, $10.0/1M Output. Für Frontier-Niveau nicht günstig, gemessen an der nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Such-, Fetch- und Orchestrierungsanteil, wenn eine Validierungsschicht Tool-Calls prüft und die Endausgabe notfalls nachbearbeitet. Nicht geeignet für Compliance-, Policy- oder andere textkritische Workflows, in denen die Verdichtung der Tool-Ergebnisse selbst bereits final belastbar sein muss. Wer ein Modell für Tool-Entscheidung und breite Recherche sucht, kann es einsetzen. Wer ein Modell braucht, das Tool-Ergebnisse präzise und unverändert in belastbare Antworten überführt, sollte striktere Guardrails vorsehen oder ein treueres Synthesemodell nachschalten.