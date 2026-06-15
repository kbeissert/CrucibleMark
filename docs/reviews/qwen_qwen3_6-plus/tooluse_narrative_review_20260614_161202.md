**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:02


Bedingt deploy, weil die Halluzinationslage unkritisch ist, aber die Tool-Calls nicht durchgehend valide sind und das Gesamtbild mit 59.38 nur für überwachte Tool-Pipelines trägt.

**Tool-Execution-Profil**

Qwen 3.6 Plus zeigt brauchbare Ausführung, aber keine verlässliche Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis erkennt, dass statt fetch erst web_search nötig ist, fällt es mit P1 35 klar ab. Beim URL-Construction-Test, der die Ableitung einer korrekten Ziel-URL und anschließendes Fetch prüft, arbeitet es mit P1 80 deutlich besser. Das spricht gegen flexible Tool-Wahl und eher für ein Muster: Wenn die Zielstruktur schon klar ist, liefert es solide. Wenn erst entschieden werden muss, welches Werkzeug den Informationsraum richtig öffnet, wird es unsicher. Dass ein Retry erforderlich war und der Tool-Call nicht valide war, wirkt hier eher wie ein Protokoll- und Orchestrierungsproblem als ein reines Wissensdefizit. Für MCP heißt das: nicht blind an autonome Tool-Ketten hängen, sondern Call-Validierung und Retries serverseitig erzwingen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 50 zeigt, dass Qwen 3.6 Plus gefundene Inhalte nicht konsistent in belastbare, knappe Arbeitsantworten überführt. Das sieht man auch an EU License Research mit P2 20 und an mehreren Assets, die trotz ordentlicher P1-Werte nur auf P2 60 kommen. Die Recherche gelingt also öfter als die anschließende Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal besser als die Punktzahl vermuten lässt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen stammen, wurde keine Halluzination erkannt. Der Content-Verification-State B1 und die schwache P2 zeigen aber: Es erfindet nichts, bleibt jedoch nicht präzise genug an den verifizierten Quellen.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, halluziniert Qwen 3.6 Plus keinen Ersatzinhalt. P2 60 ist kein starker Wert, aber der entscheidende Punkt stimmt: Es bricht Vertrauen nicht durch erfundenen Seiteninhalt. Das reicht für Pipelines mit klarer Fehlerbehandlung.

**Betriebsprofil**

6.58s erster Call. 25.42s zweiter Call. 194.67s total. Langsam für die erzielte Leistung. 0.005278 USD pro Run. Günstig im Preis, aber die Laufzeit frisst einen Teil dieses Vorteils operativ auf.

**Fazit & Empfehlung**

Geeignet für kostenbewusste, überwachte MCP-Pipelines mit harter Tool-Governance, expliziter Tool-Vorwahl und Pflicht-Retries. Nicht geeignet für autonome Rechercheketten, Compliance-nahe Entscheidungsstrecken oder Systeme, in denen das Modell selbstständig zwischen Suche, Fetch und Synthese umschalten muss. Wer Qwen 3.6 Plus einsetzt, sollte es als ausführendes Teilmodell in einer stark eingehegten Orchestrierung behandeln, nicht als vertrauenswürdigen Tool-Dispatcher.