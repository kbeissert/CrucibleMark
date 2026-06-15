**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:53


Bedingt deploy, weil GLM 5.1 Tools zuverlässig und protokollkonform nutzt, aber die Synthesequalität mit erfundener oder unsauber verdichteter Ausgabe für vertrauenskritische Pipelines noch zu instabil ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Mit P1 90 produziert GLM 5.1 valide Calls, bleibt MCP-konform und brauchte keinen Retry. Das spricht gegen ein Formatproblem und für belastbares Tooling-Verhalten. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis search statt fetch gewählt wird, traf es die Werkzeugwahl sauber. Das zeigt echte Werkzeugintelligenz und nicht nur starres Fetch-first-Verhalten. Beim URL-Construction-and-Fetch-Test, der die präzise Ableitung einer Ziel-URL misst, bleibt es brauchbar, aber weniger deterministisch. Für bekannte Zielstrukturen reicht das oft. Für Pipelines mit harter URL-Präzision sollte man Guardrails oder Validierung davor setzen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 59.17 ist für produktive Tool-Pipelines der kritische Wert, weil hier nicht der Call, sondern die Übergabe in verwertbare Antwortform scheitert. Positiv sind HTTP Fetch & Extract sowie Tool Failure Handling (404) mit jeweils 80. Schwach sind aber EU License Research mit 40 und Web Search & Tool Selection mit 35. Das Muster ist klar: Es findet die Quelle oft, verdichtet sie aber nicht stabil genug in präzise, belastbare Aussagen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Fehler prüfen soll, halluziniert es nicht und der Verifikationsstatus ist sauber. Das ist ein wichtiges Vertrauenssignal. Gleichzeitig ist global ein Halluzinationsereignis erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, untergräbt es die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf misst, reagiert GLM 5.1 produktionsgerecht. Es kommuniziert den Fehler offen und erfindet keinen Seiteninhalt. Genau dieses Verhalten ist für Betriebspipelines akzeptabel, weil Orchestrierung und Fallbacks darauf aufsetzen können.

**Betriebsprofil**

Call 1: 9.61s. Call 2: 41.74s. MCP-Latenz: 0.77s. Total: 312.72s. Klar langsam. Kosten pro Run: 0.014060. Günstig bis moderat, aber die Laufzeit steht nicht im Verhältnis zu einer nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Auswahl, Web-Recherche und transparente Fehlerbehandlung wichtiger sind als die finale sprachliche Verdichtung. Dazu zählen Recherche-Vorstufen, Routing, Source Collection und Human-in-the-Loop-Workflows. Nicht geeignet für Compliance, regulatorische Zusammenfassungen, Executive Briefs oder andere Endpunkte, in denen die Antwort selbst als verlässliches Arbeitsprodukt gelten muss. Wenn Sie es einsetzen, dann mit strikter Output-Prüfung und bevorzugt als Tool-Operator, nicht als letzte Syntheseschicht.