**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:20:14


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und die schwache Synthesetreue das Vertrauen in produktive Tool-Pipelines begrenzen. Der Gesamteindruck ist brauchbar, aber nicht freigabefähig für unbeaufsichtigte High-Trust-Strecken.

**Tool-Execution-Profil**

MiMo V2.6 Flash zeigt echte Werkzeugintelligenz. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, wählt es das richtige Werkzeug souverän. Das spricht gegen starres Musterverhalten. Auch beim Multilingual-Search-&-Synthesis-Test bleibt die Ausführungsseite stabil.

Schwächer ist die Präzision im letzten Schritt. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL und anschließendes Fetch prüft, erreicht es nur ein solides, aber nicht deterministisches Niveau. Dazu kommt, dass mindestens ein Tool-Call insgesamt nicht valide war. Das ist kein Retry-Problem und damit kein bloßes Formatrauschen, sondern ein Protokollrisiko: In MCP-Pipelines muss der Call beim ersten Mal strukturell stimmen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 59.17 der klare Engpass. Besonders EU License Research und HTTP Fetch & Extract zeigen, dass das Modell abgerufene Inhalte nicht zuverlässig in belastbare, präzise Aussagen überführt. Für Produktivsysteme zählt nicht nur, dass ein Tool benutzt wurde, sondern dass die Antwort den Tool-Befund korrekt und vollständig abbildet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, halluziniert es zwar nicht offen, aber das Ergebnis bleibt mit P2=20 deutlich zu schwach. Das ist ein Sicherheitsrisiko, nicht nur ein Qualitätsmangel: Wenn ein Modell aktuelle Web-Befunde nicht sauber bindet, kann es in Compliance- oder Policy-Pipelines scheinbar fundierte, tatsächlich aber ungesicherte Aussagen ausgeben.

**Fehlerresilienz**

Beim 404-Test reagiert MiMo V2.6 Flash produktionstauglich. Es kommuniziert den Fehlschlag transparent und erfindet keinen Seiteninhalt. Genau dieses Verhalten ist für robuste Orchestrierung entscheidend, weil die Pipeline den Fehler dann kontrolliert weiterbehandeln kann.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Deployments operativ attraktiv. Mit 73.42 liegt es 0.00-Punkte unter dem Fleet-Ø von 68.17. Die MIT-lizenzierten offenen Gewichte sind ein echter Vorteil, zumal sich das Provenienzrisiko im Self-Hosting deutlich reduziert.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen Tool-Auswahl, Web-Recherche und transparentes Fehlerverhalten wichtiger sind als präzise Endverdichtung. Nicht geeignet für Compliance, Lizenzprüfung, faktenkritische Extraktion oder andere Strecken, in denen das Modell Tool-Befunde exakt und revisionsfest zusammenfassen muss. Empfehlung: als Orchestrator oder Recherche-Front-End mit nachgelagerter Verifikation einsetzen, nicht als letzte vertrauensgebende Syntheseschicht.