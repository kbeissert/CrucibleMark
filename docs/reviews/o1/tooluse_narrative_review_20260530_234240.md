**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:40


Bedingt deploy, weil OpenAI o1 valide Tool-Calls liefert und insgesamt brauchbar mit MCP-Infrastruktur arbeitet, aber die Synthesetreue mit Halluzinationssignal das Vertrauen in produktive Antwortpfade begrenzt.

**Tool-Execution-Profil**

Beim reinen Tool-Einsatz ist das Modell stark. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 liegt mit 90 auf klarem Produktionsniveau. Besonders relevant ist die Werkzeugwahl: Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Fetch unterscheiden lässt, wählt o1 das richtige Werkzeug sicher. Das spricht für echte Tool-Intelligenz statt starrem Schema. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann per Fetch abrufen lässt, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 heißt hier: Der Ablauf funktioniert oft, doch die URL-Herleitung ist nicht präzise genug für fragile Pipelines mit strikten Pfadannahmen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht stark genug für High-Trust-Pipelines. P2 liegt bei 65, mit klarer Streuung: HTTP Fetch & Extract ist sehr gut, aber URL Construction & Fetch und Multilingual Search & Synthesis fallen deutlich ab. Das Muster ist wichtig: o1 kann gefundene Inhalte sauber extrahieren, verliert aber an Präzision, sobald mehrere Quellen, Sprachwechsel oder schwächer strukturierte Evidenz zusammengeführt werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt o1 im zulässigen Rahmen. Content-Verification-State A und keine Halluzination sind hier ein gutes Vertrauenssignal. Trotzdem steht global ein Halluzinationsflag im Lauf. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Aussagen als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Tool-Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt verlangt, reagiert o1 produktionsgerecht. Es halluziniert keinen Ersatzinhalt und kommuniziert den Fehlschlag ausreichend klar. P2 80 ist dafür akzeptabel. Für reale Systeme ist das wichtiger als sprachliche Eleganz.

**Betriebsprofil**

Total 147.62s pro Run. Langsam. Einzelaufrufe 6.54s und 16.93s, MCP-Latenz 1.14s. Kosten 0.708810 pro Run. Teuer. Für die gebotene Tool-Ausführung vertretbar, für breit ausgerollte Online-Pipelines schwer.

**Fazit & Empfehlung**

Geeignet für kontrollierte MCP-Pipelines mit klaren Tools, nachvollziehbaren Zwischenschritten und nachgelagerter Validierung, etwa Recherche-Workflows, technische Voranalysen und planungsintensive Agentenschritte. Nicht geeignet als ungeprüfte Endinstanz für Compliance, mehrsprachige Synthese oder antwortnahe User-Facing-Ausgabe, wenn jedes Tool-Ergebnis exakt und belegtreu verdichtet werden muss.