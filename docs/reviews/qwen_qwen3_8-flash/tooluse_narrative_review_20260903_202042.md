**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:20:42


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und ein erkannter Halluzinationsbefund das Vertrauen für unbeaufsichtigte Produktionspipelines begrenzen.

**Tool-Execution-Profil**

Qwen3.8-Flash zeigt echte Werkzeugintelligenz statt bloßem Standardmuster. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis zwischen Suche und direktem Fetch unterschieden wird, wählt es das richtige Werkzeug sicher. Das spricht für brauchbare Orchestrierung in offenen MCP-Abläufen. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines mit harter URL-Präzision.

Der P1-Wert von 90 stützt diesen Eindruck. Praktisch wichtiger ist aber: Der Tool-Call war nicht durchgehend valide. Damit ist das Problem nicht die grundsätzliche Planungsfähigkeit, sondern die Protokolltreue am Übergabepunkt zur Infrastruktur. Da kein Retry nötig war, wirkt das nicht wie ein bloßes Formatstottern unter Last, sondern wie eine punktuelle, aber reale Unsicherheit in der Call-Erzeugung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 62.5 ist der klare Schwachpunkt des Modells. Besonders bei EU License Research, also der Verdichtung aktueller Web-Quellen zu Lizenzrestriktionen, und bei Multilingual Search & Synthesis verliert es Präzision, priorisiert Offensichtliches und lässt relevante Nuancen liegen. Für Recherchepipelines, in denen das Modell nicht nur Daten beschafft, sondern belastbar zusammenführen muss, ist das zu wenig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, halluziniert es nicht. Das ist der wichtige Befund. Gleichzeitig ist global ein Halluzinationssignal gesetzt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als angebliche Tool-Ausgabe framet, beschädigt es die Verlässlichkeit der gesamten Pipeline.

**Fehlerresilienz**

Beim 404-Test, der prüft, ob ein fehlgeschlagener Tool-Call offen benannt statt mit Ersatzinhalt kaschiert wird, reagiert Qwen3.8-Flash akzeptabel. Es erfindet keinen Seiteninhalt trotz Fehler. Die Fehlerkommunikation ist damit produktionsfähig, auch wenn die Synthese nach dem Fehler nicht besonders stark ausfällt.

**Betriebsprofil**

Call 1: 44.76s. MCP-Latenz: 1.03s. Call 2: 45.12s. Total: 545.47s. Langsam für die gezeigte Ergebnisqualität. Preis: $0.16/1M Input, $0.47/1M Output. Günstig für Frontier-Klasse, aber die Laufzeit relativiert den Kostenvorteil im operativen Durchsatz.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Wahl, Web-Recherche und kontrollierte Fehlerbehandlung wichtiger sind als hochwertige Verdichtung. Sinnvoll als agentischer Beschaffer oder Vorstufe vor einer zweiten Validierungs- oder Syntheseschicht. Nicht geeignet als alleinige Instanz für Compliance, mehrsprachige Recherche-Synthese oder jede Pipeline, in der Tool-Ausgaben ohne menschliche Kontrolle als vertrauenswürdige Fakten weitergereicht werden.