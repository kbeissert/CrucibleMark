**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:55


Nicht deploy für autonome MCP-Pipelines, weil die Tool-Calls nicht valide bleiben, ein Retry nötig ist und der kombinierte Befund mit 51.96 klar unter Produktionsniveau liegt. Für assistierte Workflows ist es nur bedingt nutzbar.

**Tool-Execution-Profil**

GPT-5.4 zeigt keine verlässliche Werkzeugwahl. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen web_search und fetch verlangt, fällt es deutlich ab. Das spricht gegen echte Tool-Intelligenz in offenen Situationen. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, arbeitet es dagegen solide. Das Muster wirkt deshalb nicht wie adaptive Werkzeugwahl, sondern eher wie gutes Abarbeiten, sobald der Pfad schon eng vorgegeben ist.

Der ungültige Tool-Call und das erforderliche Retry deuten primär auf ein Protokoll- oder Formatproblem hin, nicht auf komplettes Aufgabenmissverständnis. Für MCP ist das trotzdem kritisch. In produktiven Tool-Ketten zählt nicht, ob ein zweiter Versuch funktionieren könnte, sondern ob der erste Call zuverlässig maschinenlesbar und ausführbar ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 46.67 zeigt, dass GPT-5.4 extrahierte Informationen nicht konsistent in belastbare Antworten überführt. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo aus vorhandener oder erreichbarer Evidenz keine ausreichend präzise, entscheidungsfeste Zusammenfassung entsteht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil vorsichtig besser als der Rohscore. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Trotzdem ist P2=20 bei Content-Verification-State B2 ein Warnsignal: Das Modell erfindet nichts offen, aber es verankert die Antwort auch nicht sauber genug im beschafften Material. Für Compliance-nahe Recherche ist das zu wenig.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt prüft, reagiert GPT-5.4 akzeptabel. Es halluziniert trotz fehlgeschlagenem Tool nicht und bleibt damit im sicheren Bereich. Das ist produktionsfähig. Es zeigt, dass das Modell bei explizitem Scheitern defensiv reagieren kann, auch wenn die normale Tool-Ausführung selbst nicht stabil genug ist.

**Betriebsprofil**

Total 78.76s. Call 1: 7.97s. Call 2: 4.71s. MCP-Latenz: 0.45s. Für die erreichte Leistung ist das langsam. Kosten pro Run: 0.076749. Für dieses Zuverlässigkeitsniveau ist das teuer.

**Fazit & Empfehlung**

Geeignet höchstens für überwachte Pipelines mit einfacher Fetch-Extraktion, klaren URL-Mustern und hartem Output-Validation-Layer. Nicht geeignet für dynamische Recherchepfade, Tool-Routing, mehrsprachige Web-Recherche oder Compliance-relevante Synthese, bei denen das Modell selbst entscheiden muss, welches Tool wann aufzurufen ist und wie Ergebnisse belastbar zusammengeführt werden. Wenn MCP autonom laufen soll, ist GPT-5.4 in diesem Zustand keine tragfähige Übergabe.