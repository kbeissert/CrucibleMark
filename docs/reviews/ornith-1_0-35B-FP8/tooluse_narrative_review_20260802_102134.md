**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:21:34


Bedingt deploy, weil das Modell zwar keine Halluzinationen im Test zeigte, aber keine verlässliche Tool-Call-Validität erreichte und mit einem Combined-Score von 51.96 klar unter Produktionsniveau für autonome MCP-Pipelines bleibt.

**Tool-Execution-Profil**

Ornith 1.0 35B zeigt brauchbare Ausführung, aber schwache Werkzeugwahl. Das zentrale Muster: Wenn der Pfad klar ist, arbeitet es solide. Beim HTTP Fetch & Extract, das präzise Fakten aus abgerufenem Content ziehen soll, erreicht es 80 in P1. Beim URL-Construction-Test, der korrekte URL-Ableitung plus anschließenden Fetch prüft, liegt es ebenfalls bei 80. Das spricht für ordentliche mechanische Ausführung.

Sobald es aber selbst erkennen muss, welches Tool überhaupt benötigt wird, bricht die Leistung sichtbar ein. Beim Web Search & Tool Selection, das ohne expliziten Hinweis zwischen web_search und fetch unterscheiden soll, fällt P1 auf 35. Das wirkt nicht wie robuste Tool-Intelligenz, sondern wie ein Muster: bekannte oder direkt ableitbare Fetch-Aufgaben gelingen, offene Recherchepfade nicht. Für MCP-Orchestrierung ist das ein echtes Risiko, weil falsche Tool-Wahl früh die ganze Kette verfehlt. Dass der Tool-Call insgesamt nicht valide war, bestätigt diesen Befund. Immerhin: Es brauchte keinen Retry, also liegt das Problem eher im Verständnis der Werkzeugentscheidung als im Ausgabeformat.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 62.50 ist für produktive Verdichtung zu unsauber, vor allem weil die Schwächen genau in den Rechercheaufgaben liegen. EU License Research kommt nur auf 20 in P2. Multilingual Search & Synthesis, also sprachübergreifende Recherche mit deutscher Zusammenfassung, endet bei 40. Das Modell kann Inhalte zusammenziehen, aber nicht konsistent in eine belastbare, entscheidungsfähige Synthese überführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Vorwissen kommen, ist Halluzination zwar nicht erkannt worden. Der sehr schwache P2-Wert von 20 zeigt aber trotzdem: Das Modell bleibt nicht überzeugend am tatsächlich beschafften Evidenzraum. Für Compliance-nahe Pipelines ist das zu wenig Vertrauen.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich Ornith brauchbar. Im 404-Test, der transparenten Umgang mit fehlschlagenden Calls statt erfundenem Ersatzinhalt misst, erreicht es 80 in P2 und halluziniert keinen Seiteninhalt. Das ist produktionsrelevant positiv. Ein Modell darf scheitern. Es darf nur nicht so tun, als hätte das Tool geliefert.

**Souveränitätsprofil**

Lokal gut betreibbar, aber nicht fleet-kompetitiv. Als Open-Weight-Modell mit MIT-Lizenz passt es sauber in souveräne Deployments. Leistungsseitig bleibt es jedoch  -1.22 Punkte unter dem Fleet-Ø von 66.87.

**Fazit & Empfehlung**

Geeignet ist Ornith 1.0 35B für lokal betriebene, streng geführte Pipelines, in denen das aufrufende System Tool-Wahl, URL-Bildung und Fehlerpfade weitgehend vorgibt. Nicht geeignet ist es als autonomer Recherche-Agent in offenen MCP-Umgebungen, besonders nicht für Compliance-, Lizenz- oder multilingual ausgreifende Suchketten. Wenn Sie es einsetzen, dann als ausführendes Subsystem mit enger Tool-Governance, nicht als eigenständig planende Instanz.