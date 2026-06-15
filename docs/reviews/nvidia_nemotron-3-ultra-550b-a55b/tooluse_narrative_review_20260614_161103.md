**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:03


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, die Syntheseleistung aber für produktive Wissens- und Compliance-Pipelines nicht stabil genug ausfällt. Der Gesamtbefund ist trotz validem Tool-Call und ohne Halluzinationssignal nur moderat belastbar.

**Tool-Execution-Profil**

Auf der MCP-Ebene arbeitet das Modell sauber. Die Tool-Calls sind valide, ein Retry war nicht nötig, und die Ausführung zeigt kein Protokollversagen. Das ist die wichtigste Grundvoraussetzung für eine Tool-Pipeline.

Bei **Web Search & Tool Selection**, also dem Test, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, erkennt das Modell den richtigen Werkzeugtyp sehr sicher. Das spricht gegen ein starres Call-Muster und für echte Werkzeugwahl. Auch bei **EU License Research** und **Multilingual Search & Synthesis** greift es zuverlässig auf externe Quellen zu, statt reflexhaft aus dem Modellwissen zu antworten.

Schwächer ist die Präzision bei **URL Construction & Fetch**. Im Test, ob das Modell eine Ziel-URL selbst korrekt ableiten und dann abrufen kann, ist die Ausführung brauchbar, aber nicht deterministisch genug für fragile Integrationen. Für offene Web-Flows ist das akzeptabel. Für Systeme mit strikter URL- oder Endpoint-Logik sollte die URL-Bildung außerhalb des Modells liegen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die klare Schwäche. P2 von 40 zeigt, dass die Modellantworten die abgerufenen Inhalte oft nicht in belastbare, entscheidungsfähige Endausgaben überführen. Das sieht man besonders bei **EU License Research**, **Web Search & Tool Selection** und **Multilingual Search & Synthesis**: Die Recherche gelingt, aber die Verdichtung in eine saubere Antwort bricht weg.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot-Befund ist besser als der P2-Wert vermuten lässt. Bei **EU License Research**, also dem Test auf aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen, bleibt es im Tool-Pfad. P2 ist zwar 0, aber ohne Halluzination und mit Content-Verification-State A. Das ist kein Vertrauensbruch, sondern ein Auswertungsproblem.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, also dem Test auf transparenten Umgang mit einem gescheiterten Abruf, reagiert das Modell produktionsgerecht. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlerzustand sauber. Genau dieses Verhalten ist für robuste Pipelines akzeptabel.

**Betriebsprofil**

Total 51.01s pro Run: langsam.  
Modell-Calls 2.90s und 4.74s, MCP-Latenz 0.86s: die Gesamtdauer entsteht nicht durch Tool-Transport allein.  
Kosten/Run: local. Günstig im Tokenpreis, aber der reale Betriebsaufwand bleibt wegen Frontier-MoE-Infrastruktur hoch.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen das Modell Tools auswählen, Aufrufe korrekt absetzen und Fehler transparent behandeln soll. Nicht geeignet als letzte Instanz für Compliance-Ausgaben, Research-Briefings oder mehrsprachige Entscheidungsvorlagen, wenn die Antwort selbst präzise aus Tool-Ergebnissen destilliert werden muss. Empfehlenswert als Orchestrator vor einer strengeren Verifikations- oder Synthese-Schicht, nicht als alleinige Antwortmaschine.