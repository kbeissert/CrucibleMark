**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:02:23


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue für produktive Tool-Pipelines nicht stabil genug bleibt und mindestens ein invalider Tool-Call das Protokollvertrauen beschädigt.

**Tool-Execution-Profil**

Gemma 4 31B Instruct zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf nach web_search zuverlässig. Das spricht für brauchbare Planungsfähigkeit in dynamischen MCP-Abläufen. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht präzise genug für deterministische Pipelines. Genau hier liegt die operative Schwäche: P1 ist insgesamt hoch, doch der invalide Tool-Call zeigt, dass MCP-Konformität nicht durchgängig sitzt. Für Systeme mit strikter Schema-Validierung ist das ein Integrationsrisiko. Positiv ist, dass kein Retry erforderlich war. Das wirkt eher wie ein punktuelles Format- oder Präzisionsproblem als wie ein grundlegendes Verständnisdefizit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung ist mit 49.17 der klare Engpass. Besonders bei HTTP Fetch & Extract, also strukturierter Faktenextraktion aus realem Seiteninhalt, und bei Multilingual Search & Synthesis verliert das Modell Präzision in der Verdichtung. Es holt Informationen über Tools, komprimiert sie aber nicht robust genug zu belastbaren Endaussagen. Für produktive Ausgabekanäle mit Compliance-, Policy- oder Kundenwirkung ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, halluziniert es nicht. Das ist der wichtigere Vertrauensbefund. Gleichzeitig ist der globale Halluzinations-Flag ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, untergräbt es die gesamte Tool-Infrastruktur. Hier ist deshalb obligatorisch, jede Endantwort gegen Tool-Rohdaten oder strukturierte Guardrails zu prüfen.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt abgrenzt, reagiert das Modell akzeptabel. Es halluziniert trotz Fehler keinen Seiteninhalt. Die Fehlerkommunikation ist damit produktionsfähig, auch wenn sie nicht besonders stark verdichtet.

**Betriebsprofil**

Call 1: 4.61s. MCP-Latenz: 1.06s. Call 2: 21.46s. Total: 162.79s. Lokal günstig, aber für die erzielte Synthesequalität langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Orchestrierungs-Pipelines, in denen das Modell Tools auswählen, Suchpfade eröffnen und Fehlersituationen sauber offenlegen soll. Nicht geeignet als ungeprüfte letzte Instanz für faktenkritische Zusammenfassungen, Compliance-Ausgaben oder kundenseitige Endantworten. Sinnvoll ist es als Tool-using worker mit nachgelagerter Validierung, nicht als autonomer Synthese-Owner.