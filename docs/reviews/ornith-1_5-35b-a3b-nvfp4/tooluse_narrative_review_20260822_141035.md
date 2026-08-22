**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:10:35


Bedingt deploy, weil das Modell trotz gutem Gesamtergebnis von 76.04 keinen durchgehend validen Tool-Call-Pfad zeigt und die Synthesequalität für produktive Tool-Pipelines zu ungleich bleibt.

**Tool-Execution-Profil**

Ornith 1.5 35B-A3B zeigt echte Werkzeugwahl statt starrem Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 95 und erkennt den Bedarf für web_search sehr zuverlässig. Das spricht für brauchbare Planungslogik in offenen MCP-Abläufen.

Weniger sauber ist die Ausführungsschicht. Beim Test URL Construction & Fetch, der die eigenständige Herleitung der Ziel-URL und den anschließenden Abruf misst, landet es bei P1 80. Das ist operativ brauchbar, aber nicht präzise genug für deterministische Pipelines mit harter Schema- und Zielbindung. Dazu passt das globale Signal tool_call_valid=False: Die Modellintelligenz bei der Werkzeugwahl ist da, die Protokolltreue im konkreten Call-Pfad ist nicht stabil genug. Retry war nicht nötig, daher liegt das Problem eher in der Erstvalidität des Aufrufs als in einem wiederkehrenden Formatkollaps.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 60 zeigt ein klares Gefälle zwischen Beschaffung und Verdichtung. Stark ist es bei HTTP Fetch & Extract sowie URL Construction & Fetch mit jeweils P2 80. Schwach ist es dort, wo knappe, belastbare Zusammenführung wichtiger ist als das reine Finden, etwa bei EU License Research und Tool Failure Handling (404) mit jeweils P2 40. Für produktive Pipelines heißt das: Die Rohdaten kommen oft an, die letzte Meile zur belastbaren Entscheidung bleibt wacklig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht. Das ist das wichtigere Vertrauenssignal. Der niedrige P2-Wert zeigt also kein Sicherheitsversagen, sondern zu schwache Verdichtung unter Compliance-ähnlichem Druck.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt verlangt, halluziniert das Modell nicht. Das ist für Produktion akzeptabel. Der P2-Wert von 40 zeigt jedoch, dass die Fehlerkommunikation zwar ehrlich, aber nicht sauber genug weiterverarbeitet wird. Als Agent bricht es die Vertrauenskette nicht, als Berichterstatter bleibt es zu unpräzise.

**Betriebsprofil**

Total 153.47s. Call 1 3.28s. MCP-Latenz 1.10s. Call 2 21.19s. Langsam für die gelieferte Qualität. Kosten/Run: local. Günstig im Betrieb, aber zeitlich teuer.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Orchestrationspipelines, in denen Tool-Auswahl wichtiger ist als perfekte Endverdichtung und ein nachgelagerter Validator die Ausgabe prüft. Nicht geeignet für Compliance-, Lizenz-, Freigabe- oder andere entscheidungsnahe Pipelines, in denen das Modell Tool-Ergebnisse selbst belastbar zusammenfassen muss. Als MCP-Agent mit Guardrails ist es brauchbar. Als autonomer Abschlussknoten noch nicht.