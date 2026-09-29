**Deployment-Urteil**

> **Erstellt am:** 27.09.2026, 17:13:18


Bedingt deploy, weil die Tool-Nutzung insgesamt stark ist, aber die Call-Validität nicht sauber genug ist und die Synthese nur auf mittlerem Produktionsniveau liegt. Combined 77.67 ist tragfähig, aber nicht selbsttragend ohne Guardrails.

**Tool-Execution-Profil**

Qwen 3.8 Omni Flash zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Web Search & Tool Selection-Test erkennt es ohne expliziten Hinweis korrekt, dass für aktuelle Informationen eine Suche statt eines direkten Fetch nötig ist. Das ist ein starkes Signal für agentische Orchestrierung. Auch bei EU License Research und Multilingual Search & Synthesis arbeitet es tool-seitig sicher.

Schwächer wird es bei der formalen Ausführung. Tool-Call valide ist insgesamt false, obwohl P1 mit 90 hoch liegt. Das spricht nicht für ein Verständnisproblem, sondern für Unsauberkeit in einzelnen Aufrufen oder Parametern. Beim URL-Construction-Test, der prüft ob das Modell die Zieladresse selbst ableiten und dann abrufen kann, reicht es nur zu brauchbarer statt deterministischer Präzision. Beim HTTP Fetch & Extract-Test zeigt sich dasselbe Muster: Zugriff meist korrekt, aber nicht robust genug für Pipelines, die auf strikt reproduzierbare Calls angewiesen sind.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. P2 von 66.67 bedeutet: Das Modell kann Ergebnisse zusammenführen, verliert aber bei faktennaher Verdichtung Präzision. Besonders beim HTTP Fetch & Extract-Test, der exakte Extraktion aus echtem Seiteninhalt misst, fällt die Qualität deutlich ab. Für Berichte und Erstentwürfe reicht das. Für Compliance, Vertrags- oder Regulatorik-Summaries ist es zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der wichtigste positive Befund. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, halluziniert es nicht. P2 60 ist inhaltlich nicht stark, aber vertrauensseitig akzeptabel: Es erfindet keine scheinbar aktuellen Fakten außerhalb der Tool-Basis.

**Fehlerresilienz**

Beim 404-Test reagiert das Modell produktionsgerecht. Es kommuniziert den Fehlschlag transparent und halluziniert keinen Ersatzinhalt. P2 80 in diesem Szenario ist ein gutes Signal für sichere Degradation: Die Pipeline bleibt überprüfbar, wenn ein Tool scheitert.

**Betriebsprofil**

Call 1: 5.80s. Call 2: 83.76s. MCP-Latenz: 1.55s. Total pro Run: 546.63s. Klar langsam. Preis: $0.15/1M Input, $0.47/1M Output. Günstig für ein Frontier-Modell, aber die Laufzeit ist im Verhältnis zur gezeigten Syntheseleistung schwer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Recherche, Tool-Auswahl und kontrollierter Fehlerbehandlung, besonders wenn aktuelle Web-Daten wichtiger sind als perfekte Verdichtung. Nicht geeignet als letzte Instanz für präzise Extraktion, regulatorische Zusammenfassungen oder strikt deterministische Fetch-Flows ohne zusätzliche Validierung. Deploy nur mit Schema-Checks, Response-Validation und einer nachgelagerten Kontrolle der extrahierten Fakten.