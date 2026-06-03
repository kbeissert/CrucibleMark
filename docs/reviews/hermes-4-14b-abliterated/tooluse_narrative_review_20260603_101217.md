**Deployment-Urteil**

> **Erstellt am:** 03.06.2026, 10:12:17


Bedingt deploy, weil die Tool-Ausführung stark und protokollsauber ist, die Synthesetreue aber zu oft vom Tool-Ergebnis wegdriftet und damit für faktensensitive Pipelines ein Vertrauensrisiko bleibt.

**Tool-Execution-Profil**

Das Modell arbeitet auf der Ausführungsebene zuverlässig. Tool-Calls sind valide, MCP-konform und es brauchte keinen Retry. Das spricht gegen ein Formatproblem und für ein solides Verständnis der Tool-Schnittstelle. Besonders stark ist der Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis erkannt wird, dass eine Suche statt eines direkten Fetch nötig ist: Hier wählt das Modell das richtige Werkzeug sicher. Beim URL-Construction-and-Fetch-Test, der die eigenständige Ableitung einer Ziel-URL prüft, ist es brauchbar, aber weniger präzise. Das zeigt kein starres Muster, sondern echte Werkzeugwahl mit schwächerer Präzision im letzten Schritt der Adressbildung. Für dynamische Tool-Pipelines ist das gut genug. Für deterministische Retrieval-Ketten mit strikter URL-Korrektheit ist zusätzliche Validierung sinnvoll.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Die P2-Leistung ist mit 44.17 der klare Engpass. Das Modell findet Informationen, verdichtet sie aber oft zu grob oder verliert Details. Das sieht man besonders bei HTTP Fetch & Extract, das präzise Fakten aus echtem Content verlangt, und bei Multilingual Search & Synthesis, wo die deutschsprachige Verdichtung fremdsprachiger Quellen deutlich abfällt. Für Produktionssysteme heißt das: Gute Retrieval-Schicht, schwache letzte Meile der Antwortbildung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Parametern beantwortet werden, bleibt es formal im Tool-Pfad und halluziniert dort nicht. Das ist das positive Signal. Gleichzeitig ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit scheiternden Tool-Aufrufen misst, reagiert das Modell produktionsgerecht. Es kommuniziert den Fehler transparent und erfindet keinen Ersatzinhalt. Das ist für reale Pipelines akzeptabel, weil der Ausfall sichtbar bleibt und von Orchestrierung oder Nutzerlogik sauber behandelt werden kann.

**Betriebsprofil**

Total 114.04s. Call 1: 3.86s. Call 2: 14.22s. MCP-Latenz: 0.93s. Für die gezeigte Leistung langsam. Kosten/Run: local, daher günstig auf Geldseite, aber teuer in Laufzeit.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen das Modell Tools auswählen, Aufrufe sauber ausführen und Fehler transparent melden soll. Nicht geeignet als letzte autoritative Syntheseschicht für Compliance, Recherche mit hoher Faktendichte oder mehrsprachige Entscheidungsgrundlagen. Wenn Sie es einsetzen, dann mit harter Nachprüfung der Endantwort gegen Tool-Outputs, idealerweise durch Zitatspflicht oder einen separaten Verifier.