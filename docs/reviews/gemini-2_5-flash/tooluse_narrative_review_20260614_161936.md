**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:36


Bedingt deploy, weil Gemini 2.5 Flash valide Tool-Calls produziert und in der Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 71.08 und erkannter Halluzination nicht stabil genug für hochkritische Faktenpipelines wirkt.

**Tool-Execution-Profil**

Das Modell versteht MCP-gestützte Tool-Nutzung klar besser als es Ergebnisse verdichtet. Tool-Call valide und ohne Retry-Bedarf spricht für saubere Protokolltreue. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den passenden Werkzeugtyp sicher. Das ist kein starres Call-Muster, sondern ein brauchbares Signal für Werkzeugintelligenz in offenen Pipelines. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile URL-Schemata. Die P1-Leistung von 90 zeigt: Für Tool-Orchestrierung ist das Modell verlässlich, solange nachgelagerte Systeme die inhaltliche Ausgabe noch prüfen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Die P2-Leistung von 52.50 zeigt ein wiederkehrendes Problem: Das Modell holt Informationen korrekt, komprimiert sie aber nicht präzise genug weiter. Besonders bei HTTP Fetch & Extract, wo strukturierte Fakten aus echtem Seiteninhalt extrahiert werden sollen, verliert es Genauigkeit. Für Produktionssysteme heißt das: Die Retrieval-Schicht ist brauchbar, die Antwortschicht braucht Guardrails, etwa Schema-Zwang, Feldvalidierung oder Second-Pass-Checks.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt Trainingswissen erzwingen soll, bleibt es formal im Tool-Pfad und halluziniert dort nicht. Das ist ein wichtiges Vertrauenssignal. Gleichzeitig ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnisrahmung ausgibt, verliert die gesamte Tool-Infrastruktur ihren Nachweiswert.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, erfindet das Modell keinen Ersatzinhalt. Das ist produktionsseitig akzeptabel. Die Fehlerkommunikation ist nicht besonders stark verdichtet, aber sie bleibt ehrlich. Genau das ist im Betrieb wichtiger als sprachliche Glätte.

**Betriebsprofil**

Call 1: 1.26s. MCP-Latenz: 0.77s. Call 2: 4.22s. Total: 37.51s. Kosten/Run: $0.005286. Günstig. Für die gezeigte Tool-Leistung schnell genug. Für die Synthesequalität nicht teuer, aber auch kein Modell, dem man ungeprüft die letzte Antwortschicht überlassen sollte.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines, in denen das Modell suchen, auswählen, abrufen und Fehler transparent melden soll. Nicht geeignet als alleinige Instanz für Compliance, Policy, Lizenz- oder andere faktenkritische Endantworten. Empfehlenswert ist der Einsatz als Tool-Operator mit nachgeschalteter Validierung oder als erste Agentenstufe vor einem strengeren Verifier.