**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:17


Bedingt deploy, weil das Modell trotz brauchbarer Einzelleistungen bei Tool-Ausführung und Quellentreue kein durchgehend verlässliches MCP-Verhalten zeigt: Halluzination wurde erkannt, Tool-Calls waren nicht durchgehend valide, und ein Retry war erforderlich.

**Tool-Execution-Profil**

Mistral Small 4 ist bei direkter Ausführung brauchbarer als bei Werkzeugwahl. Beim Test URL Construction & Fetch, der prüft ob das Modell eine Ziel-URL selbst ableitet und dann korrekt abruft, arbeitet es solide. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, fällt es deutlich ab. Das spricht nicht für echte Tool-Intelligenz, sondern für ein enges Muster: Wenn der Zielpfad ableitbar ist, liefert es; wenn erst das richtige Werkzeug erkannt werden muss, wird es unsicher.

Dass der Tool-Call nicht valide war und ein Retry nötig wurde, wirkt hier eher wie ein Protokoll- und Formatproblem als ein reines Verständnisproblem. Für MCP-Pipelines ist das trotzdem relevant. Ein Modell, das erst nach Korrekturschleife sauber spricht, erhöht Orchestrierungsaufwand und Fehlerfläche.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 39.17 der klare Schwachpunkt. Besonders bei HTTP Fetch & Extract, also der strukturierten Extraktion konkreter Fakten aus echtem Seiteninhalt, und bei Multilingual Search & Synthesis verliert das Modell Präzision. Es liefert eher eine grobe Zusammenfassung als eine belastbare, quellennah verdichtete Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch testet, bleibt es im akzeptablen Bereich. Es hat aktuelle Lizenzrestriktionen aus Web-Quellen geholt statt aus dem Training zu antworten. Das ist das wichtigste positive Signal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Inhalte als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlgeschlagenen Tool-Call prüft, erfindet das Modell keinen Seiteninhalt. Das ist produktionsseitig akzeptabel. Die schwächere Bewertung entsteht also nicht aus gefährlicher Konfabulation, sondern aus begrenzter Qualität in der Fehlerkommunikation und Weiterführung. Für robuste Systeme ist das nutzbar, solange der Orchestrator Fehlerzustände selbst strikt behandelt.

**Souveränitätsprofil**

Lokal betreibbar, offen lizenziert und damit für souveräne Deployments attraktiv. Leistungseitig liegt es mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.84. Das ist nah genug am Durchschnitt, um als pragmatische lokale Option relevant zu bleiben.

**Fazit & Empfehlung**

Geeignet für kontrollierte MCP-Pipelines mit enger Tool-Vorgabe, festen URL-Mustern, deterministischen Prompts und nachgelagerter Validierung. Nicht geeignet für dynamische Rechercheketten, offene Websuche, mehrsprachige Beschaffung oder Systeme, in denen das Modell selbständig das richtige Werkzeug wählen und Ergebnisse präzise verdichten muss. Wer lokale Souveränität und Apache-2.0-Gewichte braucht, kann es einsetzen. Die Pipeline muss das Modell jedoch führen, prüfen und bei Tool-Formatfehlern abfangen.