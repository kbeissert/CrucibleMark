**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:32


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgehend valide formatiert wurden und die Synthesetreue mit 60 klar hinter der Ausführungsqualität zurückbleibt. Der Combined-Score von 74.25 reicht für produktive Nutzung nur dort, wo Ergebnisse nachgelagert kontrolliert werden.

**Tool-Execution-Profil**

Gemma 4 26B-A4B Instruct zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell den Bedarf für web_search sauber und erreicht P1 100. Das ist ein starkes Signal für dynamische MCP-Pipelines.

Weniger sauber ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen ableitet und dann korrekt abruft. P1 80 heißt: brauchbar, aber nicht deterministisch genug für Pipelines, die exakte Endpunkte ohne Korrekturschicht erwarten. Kritisch bleibt, dass der Tool-Call insgesamt als nicht valide markiert wurde, obwohl kein Retry nötig war. Das spricht eher für Protokoll- oder Formatschwächen an Einzelstellen als für ein grundsätzliches Verständnisproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung von 60 zeigt, dass das Modell gefundene Inhalte meist brauchbar zusammenführt, aber bei Präzision, Gewichtung und Verdichtung nicht stabil genug für hochwertige Ergebnisübergaben ist. Das sieht man auch an EU License Research mit P2 40 sowie an mehreren Aufgaben mit solider Ausführung, aber nur durchschnittlicher Enddarstellung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Das Modell driftet also nicht offen in erfundene Aktualität ab, auch wenn es die recherchierten Inhalte anschließend nicht stark genug verdichtet.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, halluziniert das Modell keinen Ersatzinhalt. Das ist produktionsreif. P2 60 heißt hier: Die Kommunikation über den Fehler ist akzeptabel, aber nicht besonders präzise oder handlungsleitend. Für Produktionsbetrieb ist das tragbar, weil die Sicherheitsgrenze eingehalten wird: kein erfundener Seiteninhalt trotz Fehler.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit für souveräne Deployments attraktiv. Mit einem Sovereignty Gap von -1.22 Punkten unter dem Fleet-Ø von 66.87 bleibt es praktisch fleet-kompetitiv. Für Organisationen mit Lokalpflicht ist das ein belastbarer Vorteil.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Such-, Abruf- und Routing-Anteilen, bei denen Tool-Wahl wichtiger ist als perfekte Ergebnisverdichtung. Gut passend für interne Research-Agents, Retrieval-gestützte Assistenten und souveräne On-Prem-Setups mit Review-Schicht. Nicht die richtige Wahl für Compliance-, Rechts- oder Executive-Briefing-Pipelines, in denen die Endsynthese selbst revisionsnah sein muss. Wer dieses Modell einsetzt, sollte Tool-Call-Validierung und eine strikte Post-Processing-Schicht verbindlich davor setzen.