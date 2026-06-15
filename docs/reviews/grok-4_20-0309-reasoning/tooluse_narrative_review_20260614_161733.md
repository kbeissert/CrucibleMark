**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:17:33


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination im Lauf erkannt wurde, die Synthesequalität mit 73.17 Gesamtwert aber zu oft unter Produktionsniveau verdichtet.

**Tool-Execution-Profil**

Grok 4 Reasoning kann einer MCP-Toolkette grundsätzlich übergeben werden. Die Calls waren valide, protokollkonform und ohne erfundene Tool-Ergebnisse. Besonders stark ist die Werkzeugwahl: Beim Web-Search-and-Tool-Selection-Test erkennt das Modell ohne expliziten Hinweis sauber, dass erst gesucht und nicht direkt gefetcht werden muss. Das spricht für echte Tool-Intelligenz statt starres Musterverhalten. Beim URL-Construction-and-Fetch-Test ist es schwächer. Es kann Ziel-URLs oft brauchbar herleiten, aber nicht konsistent präzise genug für deterministische Pipelines. Das Retry-Signal wirkt daher eher wie ein Ausführungs- oder Formatproblem im letzten Schritt, nicht wie ein Verständnisfehler der Aufgabe. Für agentische Abläufe mit Guardrails ist das akzeptabel. Für One-Shot-Automation ohne Nachkontrolle ist es zu knapp.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. P2 von 56.67 ist der klare Engpass dieses Modells. In mehreren Assets zieht es korrekte Tool-Befunde nicht präzise genug zusammen, besonders bei EU License Research und Tool Failure Handling (404), wo die Verdichtung deutlich hinter der Tool-Nutzung zurückbleibt. Für Product- und Architekturentscheidungen heißt das: Das Modell findet Informationen eher, als dass es sie belastbar zusammenfasst.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, bleibt das Modell im sicheren Bereich. Content-Verification-State A bei ausbleibender Halluzination ist ein gutes Vertrauenssignal. Das Modell erfindet hier nichts, auch wenn es die Befunde nicht stark genug verdichtet.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, halluziniert Grok 4 Reasoning keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die schwache P2 zeigt jedoch, dass die Fehlerlage nicht immer klar und knapp kommuniziert wird. Für Produktion ist das akzeptabel, solange der Orchestrator Fehlerstatus und Retry-Logik selbst strikt führt.

**Betriebsprofil**

Total 90.93s pro Run. Modell-Calls je rund 7.1s, MCP-Latenz 0.89s. Langsam. Kosten 0.014590 pro Run. Für Frontier-Niveau günstig bis moderat, gemessen an der nur guten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Toolwahl, Web-Recherche und mehrstufiges Reasoning wichtiger sind als präzise Endverdichtung. Gut einsetzbar als Recherche- und Planungsmodell mit nachgelagerter Validierungs- oder Redaktionsstufe. Nicht die erste Wahl für Compliance-Summaries, Executive Briefs oder andere Pfade, in denen die Antwort direkt aus Tool-Befunden belastbar formuliert werden muss. Deploy nur mit strukturierter Ausgabeprüfung, Retry-Handling und einem zweiten Schritt für die finale Synthese.