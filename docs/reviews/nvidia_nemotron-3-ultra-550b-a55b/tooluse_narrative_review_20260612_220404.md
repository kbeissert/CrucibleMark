**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:04:04


Bedingt deploy, weil das Modell Tools sicher und protokollkonform einsetzt, aber die Syntheseleistung mit Combined 64.17 und besonders P2 40.00 zu oft unter Produktionsniveau bleibt.

**Tool-Execution-Profil**

Im Tool-Layer arbeitet NVIDIA Nemotron 3 Ultra 550B A55B verlässlich. Die Tool-Calls waren valide, ein Retry war nicht nötig, und es gab keinen Hinweis auf MCP-Protokollbruch. Das ist die zentrale Eintrittsbedingung für jede Tool-Pipeline, und die erfüllt das Modell.

Bei der Werkzeugwahl zeigt es echte Selektionsintelligenz statt bloßem Standardmuster. Im Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erreicht es P1 100. Es erkennt also, wann zuerst gesucht statt direkt abgerufen werden muss. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, liegt es bei P1 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen präzise Endpunkte konstruieren lassen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Schwäche. HTTP Fetch & Extract, Tool Failure Handling (404) und URL Construction & Fetch sind mit P2 80 solide. Sobald aber Recherche, Mehrquellenlage oder mehrsprachige Verdichtung ins Spiel kommen, bricht die Qualität ein. EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis fallen jeweils auf P2 0. Das Modell holt die Daten, aber es überführt sie nicht zuverlässig in belastbare Ausgaben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das Vertrauenssignal ist daher besser als der P2-Wert vermuten lässt: Es erfindet nichts, aber es liefert aus den abgerufenen Quellen nicht die nötige verifizierte Verdichtung.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert das Modell produktionsgerecht. P2 80, keine halluzinierten Seiteninhalte trotz Fehler. Das ist akzeptabel für reale MCP-Pipelines, weil ein Ausfall als Ausfall behandelt wird und nicht mit erfundenem Ersatzinhalt kaschiert wird.

**Betriebsprofil**

Total 51.01s pro Run. Call 1: 2.90s. MCP-Latenz: 0.86s. Call 2: 4.74s. Langsam im Gesamtdurchlauf. Kosten: lokal. Im Verhältnis zur Leistung nur dann vertretbar, wenn lokaler Betrieb oder Open-Weights-Zwang wichtiger ist als Durchsatz.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen das Modell Tools auswählen, Calls korrekt formulieren und Fehler transparent eskalieren soll. Nicht geeignet als letzte Syntheseinstanz für Compliance, Lizenzprüfung, mehrsprachige Recherche oder jede Pipeline, in der aus mehreren Tool-Ergebnissen eine belastbare Endaussage entstehen muss. Setzen Sie es als Orchestrator oder Zwischenschritt ein, nicht als finales Urteilssystem.