**Deployment-Urteil**

> **Erstellt am:** 12.07.2026, 12:41:21


Bedingt deploy, weil Grok 4.20 im Tool-Zugriff stark ist, aber mit ungültigem Tool-Call und nur mäßiger Synthesetreue kein Modell für unbeaufsichtigte MCP-Pipelines ist. Der Combined-Score von 74.75 zeigt brauchbare Substanz, die Produktionsfreigabe scheitert hier aber nicht an Halluzination, sondern an Verlässlichkeit in der Auswertung.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Call-Muster. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch erkannt wird, arbeitet es treffsicher und erreicht P1 100. Das spricht für situatives Routing. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen mit anschließendem Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug; P1 80 ist für produktive Fetch-Ketten nur solide. Insgesamt ist die Ausführung stark, P1 89.17 bestätigt das. Kritisch bleibt, dass der Tool-Call nicht durchgehend valide war. Das ist ein Integrationsrisiko auf Protokollebene, auch ohne Retry-Bedarf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 60.00 ist der klare Schwachpunkt dieses Laufs. Positiv sticht HTTP Fetch & Extract hervor, wo strukturierte Fakten aus echtem Seiteninhalt präzise zusammengeführt werden und P2 100 erreicht wird. Schwach sind dagegen EU License Research und Multilingual Search & Synthesis mit jeweils P2 40. Genau dort, wo mehrere Quellen oder Sprachgrenzen verdichtet werden müssen, sinkt die Ausgabedisziplin.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell nicht. Das ist das zentrale Vertrauenssignal. Der P2-Wert von 40 zeigt aber, dass es die abgerufenen Inhalte nicht sicher genug in belastbare Antwortform überführt. Für Compliance-nahe Recherchen ist das zu wenig.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call gegen erfundenen Ersatzinhalt prüft, bleibt Grok 4.20 auf der sicheren Seite. Es halluziniert trotz Fehler keinen Seiteninhalt. Das ist für Produktion akzeptabel. Die Kehrseite: Die Fehlerkommunikation ist nicht stark genug verdichtet, P2 40 zeigt also formale Transparenz ohne gute operative Aufbereitung.

**Betriebsprofil**

Total 103.45s. Langsam.  
Call 1: 6.62s, MCP-Latenz: 0.84s, Call 2: 9.78s.  
Preis: $1.25/1M Input, $2.5/1M Output. Günstig bis moderat für Frontier, gemessen an der gezeigten Syntheseleistung nicht überragend effizient.

**Fazit & Empfehlung**

Geeignet für recherchestarke Pipelines mit menschlicher Freigabe, insbesondere wenn Tool-Auswahl und Web-Zugriff wichtiger sind als präzise Endverdichtung. Nicht geeignet für vollautomatische Compliance-, Policy- oder mehrsprachige Decision-Pipelines, in denen Tool-Ergebnisse sauber, knapp und belastbar zusammengeführt werden müssen. Wenn Sie es einsetzen, dann mit strikter Output-Validierung, Schema-Prüfung und einer zweiten Instanz für Ergebnisabgleich.