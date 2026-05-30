**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:15


Bedingt deploy, weil Gemma 4 E4B valide Tool-Calls produziert, keine Halluzination im Benchmark gezeigt hat und mit 74.67 insgesamt produktionsfähig wirkt, aber die Synthesequalität für präzise Ergebnisverdichtung sichtbar begrenzt bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Es arbeitet MCP-konform, der Tool-Call war valide und es brauchte keinen Retry. Das ist für produktive Tool-Pipelines die Grundvoraussetzung, und diese Hürde nimmt es sauber.

Bei Web Search & Tool Selection, also dem Test ob ohne expliziten Hinweis das richtige Recherche-Werkzeug gewählt wird, erreicht es P1 100. Das spricht gegen ein starres Fetch-Muster und für brauchbare Werkzeugwahl in offenen Aufgaben. Beim URL-Construction-Test, der prüft ob das Modell die Ziel-URL selbst ableitet und dann korrekt per Fetch arbeitet, fällt es auf P1 80. Die Richtung stimmt, aber die URL-Ableitung ist nicht präzise genug für vollständig deterministische Flows. Für dynamische Recherche ist das akzeptabel. Für Pipelines mit hart kodierten Zielpfaden sollte man Validierung vor den Fetch legen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 60 insgesamt zeigt, dass es Treffer aus Tools meist korrekt zusammenzieht, aber nicht zuverlässig in eine dichte, belastbare Endantwort überführt. Das sieht man auch an HTTP Fetch & Extract und URL Construction & Fetch mit jeweils P2 60 sowie besonders an Multilingual Search & Synthesis mit P2 40. Für produktive Nutzung heißt das: eher Extraktion und Weitergabe, weniger eigenständige Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, bleibt es sauber. P2 60 ist kein Qualitätsausreißer nach oben, aber der entscheidende Befund ist Content-Verification-State A und keine erkannte Halluzination. Das Modell antwortet also aus der abgerufenen Quelle heraus statt aus Trainingswissen zu improvisieren.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, reagiert das Modell akzeptabel. P2 80 und keine Halluzination trotz Fehler zeigen: Es erfindet keinen Seiteninhalt als Ersatz. Genau dieses Verhalten braucht man in Produktion. Ein Fehler bleibt ein Fehler und wird nicht in scheinbare Sicherheit umgedeutet.

**Souveränitätsprofil**

Lokal betreibbar und einsatzfähig. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Damit ist es im souveränen Betrieb konkurrenzfähig, aber kein Ausreißer nach oben. Die lokale Ausführung ist hier ein realistischer Vorteil, nicht nur ein Compliance-Argument.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen das Modell Tools zuverlässig auslösen, Ergebnisse abrufen und Fehler transparent weiterreichen soll. Besonders passend für Recherche-, Routing- und Kontrollschichten mit menschlicher oder programmatischer Nachverdichtung. Nicht die richtige Wahl für Pipelines, in denen die Endantwort selbst schon hochpräzise, mehrsprachig sauber verdichtet und direkt entscheidungsreif sein muss. Für Compliance-nahe und souveräne lokale Deployments ist es brauchbar, solange man die letzte Synthesestufe absichert.