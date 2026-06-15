**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:14:02


Nicht deploy für autonome MCP-Pipelines, weil der Tool-Call nicht durchgängig valide war, ein Retry nötig wurde und die Gesamtleistung mit 50.96 klar zu schwach für verlässliche Produktionsübergabe ausfällt.

**Tool-Execution-Profil**

MiniMax M2.7 kann einfache, stark eingegrenzte Tool-Pfade ausführen, zeigt aber keine belastbare Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt es mit P1 35 deutlich ab. Beim Test URL Construction & Fetch, der die korrekte URL-Ableitung und anschließendes Fetch misst, erreicht es dagegen P1 80. Das spricht gegen flexible Tool-Wahl und eher für ein festes Muster: Wenn die Zielstruktur schon klar ist, arbeitet es brauchbar. Wenn es zuerst den richtigen Werkzeugtyp erkennen muss, bricht die Zuverlässigkeit ein.

Dass der Tool-Call am Ende als nicht valide markiert wurde und ein Retry erforderlich war, wirkt hier eher wie ein Protokoll- und Orchestrierungsproblem als wie reines Wissensdefizit. Für eine MCP-Pipeline ist das trotzdem kritisch. Ein Modell darf nicht nur inhaltlich richtig liegen, sondern muss Calls auch beim ersten Versuch formal korrekt erzeugen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung von 43.33 zeigt, dass MiniMax M2.7 extrahierte Inhalte nicht stabil in präzise, belastbare Antworten überführt. Das sieht man besonders bei EU License Research mit P2 20 und bei Multilingual Search & Synthesis mit P2 20. Dagegen funktioniert reine Extraktion aus bereits geholtem Content besser, etwa bei HTTP Fetch & Extract mit P2 80.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal gemischt, aber nicht katastrophal. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist positiv. Der schwache B1-Verifikationszustand und P2 20 zeigen aber, dass es den Tool-Befund nicht sauber absichert oder verdichtet. Es erfindet nicht, aber es verankert auch nicht zuverlässig.

**Fehlerresilienz**

Beim 404-Test, der transparente Kommunikation bei Tool-Fehlern statt erfundenem Ersatzinhalt misst, bleibt MiniMax M2.7 auf der akzeptablen Seite. P2 60 ist kein starkes Ergebnis, aber entscheidend ist: Es halluziniert trotz Fehler keinen Seiteninhalt. Für Produktion ist das der Mindeststandard, und den erfüllt es hier.

**Betriebsprofil**

Call 1: 3.92s. Call 2: 6.71s. MCP-Latenz: 0.20s. Total: 65.05s.  
Kosten pro Run: $0.0048.  
Direkte Einordnung: günstig, aber für die gezeigte Leistung und den Retry-Bedarf zu langsam im End-to-End-Verhalten.

**Fazit & Empfehlung**

Geeignet höchstens für beaufsichtigte Pipelines mit einfachen Fetch- und Extraktionsschritten, klar vorgegebenen URLs und nachgelagerter Validierung durch ein zweites System. Nicht geeignet für dynamische Tool-Auswahl, Recherche-Workflows, mehrsprachige Synthese oder Compliance-nahe Aufgaben, in denen das Modell selbst entscheiden muss, welches Tool wann einzusetzen ist. Wer eine Tool-Infrastruktur übergeben will, braucht hier zu viele Leitplanken.