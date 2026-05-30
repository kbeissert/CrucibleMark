**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:58


Nicht deploy für MCP-gestützte Tool-Pipelines, weil weder valide Tool-Calls noch belastbare Ausführungsscores vorliegen und der Combined Score mit 0.00 nur einen Ausfallzustand abbildet, nicht produktionsfähige Kompetenz.

**Tool-Execution-Profil**

Das Kernproblem ist nicht eine schwache Teilkompetenz, sondern fehlende Nachweisbarkeit der Tool-Ausführung. P1 ist durchgängig n/a, zugleich ist der Tool-Call als nicht valide markiert. Damit gibt es keinen belastbaren Beleg, dass qwen3.6-plus MCP-konform arbeitet, das richtige Tool auswählt oder Requests formal korrekt bildet.

Besonders kritisch ist, dass sowohl beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden soll, als auch beim Test URL Construction & Fetch, der präzise URL-Ableitung und anschließendes Fetching prüft, keinerlei verwertbare Ergebnisse vorliegen. Das spricht nicht für ein knapp verfehltes Leistungsniveau, sondern für eine fehlende operative Spur. Ein Retry war nicht erforderlich. Das entlastet das Modell nicht, sondern deutet darauf hin, dass das Problem nicht nur ein Formatfehler im ersten Versuch war.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine belastbare Aussage. P2 ist in allen Assets n/a. Für Produktionsentscheidungen ist das ein harter Mangel, weil gerade die Verdichtung von Tool-Outputs in verwertbare Antworten die eigentliche Wertschöpfung einer Tool-Pipeline ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal begrenzt, aber positiv. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist ein Vertrauensindikator, aber kein Freifahrtschein. Ohne valide Tool-Nutzung bleibt offen, ob das Modell sauber am Werkzeug hängt oder nur keinen prüfbaren Output geliefert hat.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf prüft, wurde keine Halluzination trotz Fehler erkannt. Das ist für Produktion grundsätzlich akzeptabel. Positiv ist also: Es erfindet im dokumentierten Fehlerszenario keinen Ersatzinhalt. Negativ bleibt: Auch diese Beobachtung kompensiert nicht die fehlende Evidenz für reguläre Tool-Ausführung.

**Betriebsprofil**

Keine verwertbaren Laufzeitdaten. Kosten pro Run: local. Leistungsbewertung im Verhältnis zu Latenz und Kosten ist daher nicht möglich.

**Fazit & Empfehlung**

qwen3.6-plus ist in diesem Lauf kein Kandidat für produktive MCP-Pipelines mit eigenständiger Tool-Entscheidung, Fetching oder Web-Recherche. Vertretbar wäre allenfalls ein eng eingezäunter Einsatz ohne echte Tool-Verantwortung, etwa als nachgelagerter Textumformer auf bereits validierten Inputs. Für Architekturen, in denen das Modell selbst Toolwahl, Aufrufbildung und Ergebnisintegration zuverlässig tragen muss, fehlt jede belastbare Freigabebasis.