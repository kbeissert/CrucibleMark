**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:18:34


Bedingt deploy, weil GPT-5 valide Tool-Calls erzeugt und keine Halluzination im Lauf zeigte, aber die Synthesetreue mit Combined 71.42 und P2 56.67 für verlässliche Produktionspipelines zu inkonsistent bleibt.

**Tool-Execution-Profil**

Bei der Tool-Ausführung wirkt GPT-5 grundsätzlich pipeline-tauglich. Die Calls waren valide und MCP-konform. Im Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 80. Das spricht für echte Werkzeugwahl statt starrem Muster. Im Test URL Construction & Fetch, der die Ableitung einer korrekten Ziel-URL aus Eigenwissen misst, liegt es ebenfalls bei P1 80. Das ist solide, aber nicht deterministisch genug für Pipelines, in denen schon kleine URL-Fehler Folgeschritte brechen.

Auffällig ist retry_required=true. Das wirkt hier eher wie ein Ausführungs- oder Formatproblem im Ablauf als wie ein grundlegendes Verständnisproblem. Gegen ein Verständnisdefizit spricht, dass die Tool-Calls am Ende valide waren und die Auswahl des richtigen Werkzeugs über mehrere Aufgabentypen hinweg funktionierte.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. GPT-5 extrahiert in HTTP Fetch & Extract sauberer als im Rest des Feldes und kommt dort auf P2 80. Sobald mehrere Quellen, Ausnahmen oder Fehlerzustände in eine knappe Schlussantwort überführt werden müssen, fällt die Verdichtungsqualität sichtbar ab. EU License Research und Tool Failure Handling (404) landen beide bei P2 40. Das heißt: Die Rohdaten kommen an, aber die letzte Meile der belastbaren Zusammenfassung ist nicht stabil genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, wurde keine Halluzination erkannt. Content-Verification-State A ist für Compliance-nahe Flows ein wichtiges Positivsignal. Das Modell driftet also nicht leichtfertig in auswendig gewusste Antworten ab, auch wenn die Zusammenfassung zu grob bleibt.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich GPT-5 produktionsfähig. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt prüft, halluziniert es keinen Seiteninhalt. P2 40 zeigt zwar schwache Aufbereitung des Fehlers, aber kein Vertrauensbruch. Für Produktion ist das akzeptabel: lieber ein knapp erklärter Fehler als erfundene Daten.

**Betriebsprofil**

Total 188.78s: langsam.  
Call 1 6.88s, Call 2 23.18s, MCP-Latenz 1.40s.  
Kosten/Run 0.077128: für die gezeigte Leistung teuer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Auswahl, Web-Recherche und vorsichtige Fehlerbehandlung wichtiger sind als präzise Endverdichtung. Gut passend für Analysten-Assistenz, explorative Recherche und mehrsprachige Suchflüsse mit menschlicher Abnahme. Nicht die richtige Wahl für Compliance-Summaries, Executive Briefs oder automatisierte Entscheidungen, bei denen die Antwort die Tool-Ergebnisse exakt und vollständig verdichten muss.