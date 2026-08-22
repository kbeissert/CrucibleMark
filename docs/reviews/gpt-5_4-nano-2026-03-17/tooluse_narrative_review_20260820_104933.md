**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:49:33


Bedingt deploy, weil die Tool-Ausführung in Teilen funktioniert, aber die Kombination aus ungültigen Tool-Calls, erkannter Halluzination und schwacher Gesamtsynthese das Modell für autonome MCP-Pipelines unzuverlässig macht.

**Tool-Execution-Profil**

GPT-5.4 Nano zeigt kein stabiles Werkzeugurteil. Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt es deutlich ab. Beim URL-Construction-and-Fetch-Test, der die eigenständige Ableitung einer Ziel-URL misst, arbeitet es dagegen solide. Das spricht nicht für echte Tool-Intelligenz, sondern eher für ein festes Muster: bekannte oder direkt konstruierbare URLs funktionieren, offene Recherchepfade nicht. Für MCP-gestützte Infrastrukturen ist das kritisch, weil dynamische Pipelines genau diese Wahlleistung verlangen. Dass der Tool-Call insgesamt als nicht valide markiert wurde, verschärft den Befund. Das Problem liegt damit nicht nur in der Antwortqualität, sondern in der Protokolltreue gegenüber der Tool-Schicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung zeigt, dass GPT-5.4 Nano gefundene Inhalte oft nicht präzise genug zusammenführt. Besonders bei EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis bricht die Verdichtungsqualität deutlich ein. Brauchbare Extraktion aus klar vorliegendem Fetch-Content ist möglich, aber die Überführung in belastbare Antworten bleibt inkonsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist positiv. Gleichzeitig ist global eine Halluzination erkannt worden. In einer Tool-Pipeline ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als scheinbare Tool-Ergebnisse ausgibt, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem fehlschlagenden Tool-Call prüft, reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler und bleibt damit grundsätzlich transparent. Die P2-Ausprägung ist nur mittel, aber für Produktion ist der entscheidende Punkt erfüllt: Es verschleiert den Fehlschlag nicht durch erfundene Ersatzinhalte.

**Betriebsprofil**

Call 1: 1.19s. Call 2: 1.94s. MCP-Latenz: 0.20s. Total: 20.00s. Preis: lokal ausgewiesen. Für die gezeigte Leistung schnell auf Einzelaufruf-Ebene, aber der Gesamtrun ist im Verhältnis zur schwachen Ergebnisqualität nicht effizient.

**Fazit & Empfehlung**

Geeignet als günstiger Hilfsbaustein für eng geführte Aufgaben mit vorgegebener URL, einfacher Extraktion und kontrollierter Fehlerbehandlung. Nicht geeignet als eigenständig entscheidendes Modell für Recherche, Tool-Auswahl, mehrsprachige Synthese oder Compliance-nahe Antworten. Wenn es in eine Pipeline kommt, dann nur mit harter Tool-Validierung, Schema-Prüfung, Antwort-Guardrails und einer nachgelagerten Verifikation durch ein zuverlässigeres Modell oder deterministische Checks.