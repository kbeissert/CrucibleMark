**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:01:51


Bedingt deploy, weil es keine Halluzination im Test zeigte, aber keine durchgängig validen Tool-Calls lieferte und ein Retry brauchte. Für produktive MCP-Pipelines ist das tragbar, wenn ein Orchestrator Formatfehler abfängt und Wiederholungen steuert.

**Tool-Execution-Profil**

Mistral Large 3 zeigt echte Werkzeugwahl statt starrem Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt es den richtigen Einstieg sehr sicher und erreicht P1 100. Das spricht für brauchbare Tool-Intelligenz in offenen Retrieval-Flows. Schwächer ist es beim URL-Construction-Test, der die korrekte Ziel-URL aus internem Wissen ableitet und dann fetch ausführt: P1 75 ist funktional, aber nicht präzise genug für deterministische Pipelines mit enger Fehlertoleranz.

Der Befund `tool_call_valid: false` bei gleichzeitig hohem P1 deutet eher auf ein Protokoll- oder Formatproblem als auf grundsätzlich falsches Aufgabenverständnis. Dass ein Retry erforderlich war, passt zu diesem Bild. Für MCP-Betrieb heißt das: fachlich oft auf dem richtigen Pfad, aber nicht robust genug für eine Infrastruktur, die strikt valide Call-Strukturen ohne Nachbesserung erwartet.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung von 65 zeigt, dass die Verdichtung brauchbar, aber nicht konstant präzise ist. Besonders auffällig ist der Bruch zwischen starker Werkzeugwahl und schwacher Auswertung im Test Web Search & Tool Selection, wo es zwar korrekt recherchiert, die Ergebnisse aber nur mäßig zusammenführt. Dagegen ist die mehrsprachige Recherche und Verdichtung stark: Multilingual Search & Synthesis erreicht 80 in P2 und wirkt produktionstauglicher.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot-Test EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Parametergedächtnis beantwortet werden, zeigte keine Halluzination. Das ist das wichtigere Vertrauenssignal. Es gibt hier keinen Hinweis, dass das Modell Tool-Ergebnisse durch erfundene Aktualität ersetzt.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, bleibt Mistral Large 3 kontrolliert. P2 80 bei zugleich keiner Halluzination trotz Fehler ist für Produktion akzeptabel. Es kommuniziert den Fehlschlag, statt Seiteninhalt zu erfinden. Genau dieses Verhalten hält eine Tool-Pipeline vertrauensfähig.

**Betriebsprofil**

Call 1: 17.45s. Call 2: 21.83s. MCP-Latenz: 1.25s. Total: 162.17s.  
Langsam für die erzielte Gesamtleistung.  
Kosten pro Run: $0.020402. Günstig bis moderat für ein Frontier-Modell.

**Fazit & Empfehlung**

Geeignet für recherchierende Pipelines mit mehrsprachigem Input, Fehlerabfangung im Orchestrator und tolerierbarer Retry-Logik. Nicht geeignet für strikt deterministische MCP-Strecken, in denen jeder Tool-Call sofort protokollkonform und ohne Nachformatierung sitzen muss. Wenn Ihre Infrastruktur Call-Validierung, Retry und Ergebnisprüfung bereits besitzt, ist das Modell ein brauchbarer Generalist. Wenn das Modell selbst die letzte Instanz für saubere Tool-Ausführung sein soll, ist es nicht die sichere Wahl.