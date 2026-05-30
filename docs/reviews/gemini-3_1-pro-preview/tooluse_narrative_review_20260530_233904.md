**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:04


Bedingt deploy, weil die Tool-Ausführung produktionsreif wirkt, die Synthesetreue aber zu inkonsistent ist, um unbeaufsichtigt sensible Tool-Pipelines zu tragen. Der kombinierte Score ist gut, aber für ein Frontier-Generalist-Modell liegt das Risiko nicht in den Calls, sondern in der Verdichtung.

**Tool-Execution-Profil**

Gemini 3.1 Pro Preview wählt Werkzeuge überwiegend intelligent statt mechanisch. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, erreicht es volle Tool-Ausführung und zeigt gutes Situationsverständnis. Das spricht für echte Werkzeugwahl statt starrem Fetch-First-Muster. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Die Calls selbst sind valide, MCP-konform und ohne Retry gelaufen. Das ist ein starkes Produktionssignal.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 von 60 zeigt ein wiederkehrendes Muster: Das Modell findet Quellen und ruft sie korrekt ab, verliert aber bei der Verdichtung an Präzision. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Tool-Nutzung stark, die Endzusammenfassung aber zu grob ist. Für Architekturen, in denen das Modell nicht nur beschafft, sondern belastbar zusammenführen soll, ist das die eigentliche Schwachstelle.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, bleibt das Modell im sicheren Bereich. Content-Verification-State A und keine erkannte Halluzination sind das wichtige Signal. Der P2-Wert von 40 zeigt also keine freie Erfindung, sondern mangelhafte Verdichtung eines real beschafften Ergebnisses. Das ist deutlich weniger gefährlich, aber weiterhin relevant.

**Fehlerresilienz**

Beim 404-Test, der die Reaktion auf einen scheiternden Tool-Call misst, kommuniziert Gemini 3.1 Pro Preview den Fehler transparent und erfindet keinen Seiteninhalt. P2 von 80 ist dafür ausreichend. Für Produktion ist das akzeptabel. Ein Modell darf scheitern. Es darf den Fehlschlag nur nicht verdecken. Genau diese Grenze hält es ein.

**Betriebsprofil**

4.09s erster Call, 13.26s zweiter Call, 108.34s gesamt. Eher langsam. MCP-Latenz 0.71s, also liegt der Hauptanteil beim Modelllauf. 0.034276 USD pro Run. Für Frontier-API moderat bepreist, gemessen an der Syntheseleistung aber kein Effizienzvorteil.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Auswahl, valide Ausführung und saubere Fehleroffenlegung wichtiger sind als hochwertige Endverdichtung. Gut passend für Recherche-Orchestrierung, Vorstufen in Retrieval-Flows und menschlich geprüfte Analysten-Workflows. Nicht die erste Wahl für Compliance-Synthese, Executive Briefings oder autonome Agenten, die Tool-Ergebnisse ohne zweite Kontrollschicht in finale Aussagen überführen.