**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:46:47


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, aber die Synthesequalität für produktive Wissensverdichtung zu oft unscharf bleibt. Mit validen Tool-Calls, ohne Halluzinationsbefund und einem Combined Score von 74.17 ist es für kontrollierte Tool-Pipelines grundsätzlich tragfähig.

**Tool-Execution-Profil**

Gemini 3.1 Pro Preview zeigt ein starkes Tool-Profil. Es wählt Werkzeuge nicht nur schematisch, sondern erkennt im Test Web Search & Tool Selection ohne expliziten Hinweis korrekt, dass erst Websuche statt direktem Fetch nötig ist. Das spricht für echte Werkzeugwahl unter unvollständiger Aufgabenformulierung. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann fetch ausführen lässt, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines mit hart codierten Erwartungswerten. Die Calls selbst sind valide, MCP-konform und ohne Retry ausführbar. Das ist für Produktion wichtiger als formale Eleganz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. Der P2-Wert von 60 zeigt, dass das Modell gefundene Inhalte oft korrekt zusammenzieht, aber nicht konsistent präzise genug formuliert. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Recherche gelingt, die Verdichtung aber an Genauigkeit und Trennschärfe verliert. Für reine Retrieval- und Routing-Aufgaben reicht das. Für Compliance, Policy oder mehrsprachige Executive Summaries ist es zu unruhig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell vertrauenswürdig. P2 ist dort mit 40 schwach, aber Content-Verification-State A und kein Halluzinationsbefund bedeuten: Es erfindet keine Quelle und ersetzt Tool-Ergebnisse nicht durch Trainingswissen. Das ist ein Vertrauenssignal, auch wenn die Endverdichtung schwach bleibt.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei Tool-Fehlern gegen erfundenen Ersatzinhalt prüft, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Fehlschlag akzeptabel. Genau dieses Verhalten hält eine Tool-Pipeline überprüfbar.

**Betriebsprofil**

Total 108.34s. Einzelcalls 4.09s und 13.26s, MCP-Latenz 0.71s. Für den Output langsam. Kosten pro Run 0.034276 USD. Preislich akzeptabel, aber nicht günstig im Verhältnis zur nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Führung, Web-Recherche, Routing, Vorvalidierung und transparentem Fehlerpfad. Nicht die erste Wahl für Pipelines, in denen die eigentliche Wertschöpfung aus präziser Verdichtung entsteht, etwa Compliance-Zusammenfassungen, regulatorische Briefings oder mehrsprachige Entscheidungsunterlagen. Deployen, wenn Tool-Treue wichtiger ist als redaktionelle Präzision. Nicht deployen als letzte Syntheseschicht ohne nachgelagerte Kontrolle.