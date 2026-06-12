**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:02:32


Bedingt deploy, weil das Modell keine Halluzination gezeigt hat, aber keine validen Tool-Calls liefert und im Lauf einen Retry benötigt. Der Combined-Score von 59.38 bestätigt kein Vertrauensniveau, das für unbeaufsichtigte MCP-Pipelines ausreicht.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht im Faktenvertrauen, sondern in der Ausführung. P1 von 68.33 ist für ein Frontier-Generalist-Modell nur tragbar, wenn die Calls formal stabil sind. Das ist hier nicht der Fall: tool_call_valid ist false. Damit scheitert das Modell an einer Grundanforderung produktiver Tool-Nutzung, nämlich aus einer korrekten Absicht einen protokollkonformen MCP-Aufruf zu machen.

Zu Web Search & Tool Selection sowie URL Construction & Fetch liegen keine Einzeldaten vor. Deshalb lässt sich nicht belastbar sagen, ob das Modell Werkzeuge situativ auswählt oder einem starren Muster folgt. Für die Produktionsbeurteilung ist das bereits ein negatives Signal, weil gerade diese Tests die eigentliche Tool-Intelligenz sichtbar machen würden.

Der erforderliche Retry spricht eher für ein Format- oder Protokolldefizit als für reines Verständnisversagen. Das ist operativ relevant: Solche Fehler lassen sich durch Wrapper, Validatoren und strikte Tool-Schemas teilweise abfangen. Ohne diese Leitplanken bleibt die Pipeline jedoch fragil.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 50.00 ist der schwächste Teil des Profils und zeigt, dass das Modell aus Tool-Output keine verlässlich präzise, entscheidungsreife Verdichtung macht. Für Architekturen, in denen das Modell Ergebnisse extrahieren, priorisieren oder in klare Handlungsempfehlungen überführen soll, ist das zu dünn.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es aus dem Honeypot EU License Research keine Daten. Positiv ist nur, dass keine Halluzination erkannt wurde. Das ist besser als ein aktiver Vertrauensbruch, ersetzt aber keinen echten Nachweis, dass das Modell in Compliance-nahen Recherchen strikt an den abgerufenen Quellen bleibt.

**Fehlerresilienz**

Für den 404-Test, also den Umgang mit absichtlich scheiternden Tool-Aufrufen, liegen keine Daten vor. Deshalb bleibt offen, ob das Modell Fehler transparent meldet oder stillschweigend Ersatzinhalt erzeugt. Für Produktion ist genau diese Unterscheidung entscheidend. Ohne Nachweis robuster Fehlerkommunikation sollte man das Modell nur hinter Guardrails einsetzen.

**Betriebsprofil**

6.58s erster Call, 25.42s zweiter Call, 194.67s total. Langsam für die gezeigte Leistung. MCP-Latenz 0.44s, also liegt das Problem nicht am Tool-Layer. Kosten pro Run: 0.005278. Günstig, aber der Preis kompensiert die Instabilität nicht.

**Fazit & Empfehlung**

Geeignet ist qwen3.6-plus:free für kostenkritische, überwachte Assistenz-Pipelines mit harter Tool-Validierung, Retries und nachgelagerter Prüfung durch ein zweites System. Nicht geeignet ist es für autonome MCP-Orchestrierung, Compliance-Recherche, deterministische Fetch-Workflows oder jede Pipeline, in der ein ungültiger Tool-Call den Geschäftsprozess blockiert. Wenn Sie es einsetzen, dann nur als vorstrukturierende Schicht, nicht als vertrauenswürdigen Tool-Operator.