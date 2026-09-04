**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:21:48


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein ungültiger Tool-Call und erkannte Halluzination das Vertrauen in produktive Tool-Pipelines begrenzen. Der Gesamteindruck ist brauchbar, aber nicht freigabefähig ohne enge Leitplanken.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber und erreicht volle Ausführungstreue. Das spricht für brauchbare Tool-Intelligenz in offenen Pipelines.

Schwächer ist die Präzision beim URL-Construction-Test, der das eigenständige Ableiten einer Ziel-URL und den anschließenden fetch misst. Hier ist die Richtung korrekt, aber nicht deterministisch genug für Infrastrukturen, die auf exakte Adressbildung angewiesen sind. Der ungültige Tool-Call bestätigt dieses Bild: Das Modell versteht grundsätzlich, welches Werkzeug gebraucht wird, produziert aber nicht durchgängig MCP-saubere Aufrufe. Da kein Retry erforderlich war, liegt das Problem eher in der Erstpräzision als in einem bloßen Formatversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 65.83 der klare Schwachpunkt. In HTTP Fetch & Extract verdichtet es solide, aber bei EU License Research und besonders bei URL Construction & Fetch verliert es Präzision und schneidet Begründungen zu grob. Für Pipelines, die aus Tool-Output direkt belastbare Kurzantworten erzeugen sollen, ist das zu instabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen kommen, bleibt es ausreichend diszipliniert. Dort wurde keine Halluzination erkannt. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko: Sobald ein Modell in einer Tool-Kette erfundene Fakten als abgerufene Fakten ausgibt, ist nicht nur die Antwortqualität betroffen, sondern die Vertrauensbasis der gesamten Infrastruktur.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit gescheiterten Tool-Aufrufen prüft, kommuniziert das Modell den Fehler offen und erfindet keinen Seiteninhalt. Genau dieses Verhalten ist für robuste Pipelines erforderlich.

**Betriebsprofil**

Call 1: 4.16s. MCP-Latenz: 0.97s. Call 2: 31.88s. Total: 222.05s. Lokal und damit direkte Inferenzkosten niedrig. Für die erreichte Qualität jedoch langsam, vor allem bei mehrstufigen Läufen.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Routing-Pipelines, in denen Tool-Wahl wichtiger ist als perfekte Endverdichtung und in denen ein nachgelagerter Validator Antworten prüft. Nicht geeignet für Compliance-, Vertrags-, Lizenz- oder andere High-Trust-Pipelines, in denen jeder Tool-Call protokollkonform und jede Synthese streng quellengebunden sein muss. Wenn Sie es einsetzen, dann nur mit Tool-Call-Schema-Validation, Antwort-Postchecks und klarer Begrenzung auf assistierende statt entscheidende Rollen.