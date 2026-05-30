**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:01


Bedingt deploy, weil die Tool-Ausführung belastbar ist, das Modell aber im Honeypot faktenseitig aus dem Training ausweicht und damit das Vertrauen in toolgestützte Antworten bricht. Der Combined-Score von 75.29 ist dafür nicht das Hauptsignal, sondern die erkannte Halluzination bei valide ausgeführten Tool-Calls.

**Tool-Execution-Profil**

Claude Opus 4.6 arbeitet MCP-seitig sauber. Die Tool-Calls waren valide, ein Retry war nicht nötig, und P1 mit 86.67 bestätigt ein robustes Ausführungsprofil. Besonders stark ist die Werkzeugwahl: Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft das Modell die richtige Entscheidung sicher. Das spricht gegen bloßes Schema-Folgen und für echte Tool-Intelligenz.

Beim URL-Construction-and-Fetch-Test, der die Herleitung einer Ziel-URL aus Eigenwissen misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist klar: Wenn die Aufgabe erst eine Suchentscheidung verlangt, agiert das Modell stark. Wenn es eine präzise URL selbst konstruieren muss, sinkt die Verlässlichkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. Claude Opus 4.6 extrahiert und verdichtet Fetch-Inhalte sehr gut, etwa bei HTTP Fetch & Extract und bei Multilingual Search & Synthesis. Der P2-Gesamteindruck von 65 zeigt aber, dass diese Qualität nicht stabil über alle Aufgaben hinweg gehalten wird. Vor allem in suchgetriebenen Recherchefällen fällt die Verdichtung gegenüber der Tool-Nutzung deutlich ab.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das eigentliche Produktionsrisiko. Beim EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, erreicht das Modell nur P2=15, Content-Verification-State B1, mit erkannter Halluzination. Das ist kein bloßer Qualitätsfehler. In Compliance-, Policy- oder Risk-Pipelines ist es ein Sicherheitsproblem, weil erfundene Fakten als scheinbar toolgestützte Synthese erscheinen können.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt stellt, hat es keinen Seiteninhalt erfunden und den Fehlschlag sauber behandelt. Für produktive Systeme ist das ein wichtiges Positivsignal.

**Betriebsprofil**

Total 193.11s. Einzelaufrufe 14.39s und 16.63s, MCP-Latenz 1.17s. Langsam. Kosten pro Run 0.273305 USD. Teuer. Gemessen an der starken Orchestrierung okay, gemessen am Vertrauensrisiko in der Synthese nicht durchgängig effizient.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen Tool-Auswahl, mehrstufige Planung und saubere Fehlerbehandlung wichtiger sind als hochvertrauenswürdige Endverdichtung. Nicht geeignet als letzte Instanz für Compliance, Regulatorik, Lizenzprüfung oder andere Workflows, in denen jede Aussage strikt an Tool-Belege gebunden sein muss. Sicher einsetzbar wird es erst mit hartem Grounding, Quellenausgabe pro Behauptung und nachgelagerter Verifikation, die ungestützte Synthese aktiv blockiert.