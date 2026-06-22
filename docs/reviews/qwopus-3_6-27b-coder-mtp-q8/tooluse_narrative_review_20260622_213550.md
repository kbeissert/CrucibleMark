**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:35:50


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die MCP-Calls nicht durchgängig valide waren und die Synthesequalität für vertrauenskritische Pipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Qwopus-3.6-27B-Coder zeigt echte Werkzeugintelligenz statt reinem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, traf es die richtige Entscheidung durchgehend. Das spricht für brauchbare Orchestrierung in offenen Aufgabenlagen. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen ableitet und anschließend fetch verlangt, arbeitet es nur solide statt deterministisch. Das ist für produktive Pipelines relevant, weil schon kleine URL-Fehler Folgeketten brechen.

Der P1-Wert von 89.17 zeigt insgesamt hohe Ausführungsstärke. Gleichzeitig ist der Tool-Call nicht als valide markiert. Das ist der zentrale Vorbehalt. Nicht die Werkzeugwahl ist das Problem, sondern die Protokolltreue im letzten Meter. Für MCP-Pipelines heißt das: gute Planungs- und Selektionslogik, aber ein Adapter oder striktes Call-Validation-Layer sollte Pflicht sein.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Der P2-Wert von 63.33 ist für produktive Zusammenfassungen nutzbar, aber nicht stark genug für regulatorische, juristische oder entscheidungsvorbereitende Endausgaben ohne Nachprüfung. Das sieht man besonders an EU License Research: sehr gute Beschaffung, aber schwache Verdichtung. Dagegen sind HTTP Fetch & Extract und Multilingual Search & Synthesis brauchbar, solange die Ausgabe noch von einem nachgelagerten Prüfschritt kontrolliert wird.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Grundsätzlich ja, und das ist der wichtigere Befund. Im Honeypot EU License Research, der genau diesen Fehler provoziert, wurde keine Halluzination erkannt. Das Modell antwortet also nicht leichtfertig aus altem Weltwissen. Der Vertrauensrahmen bleibt damit intakt, auch wenn die Verdichtung der abgerufenen Inhalte qualitativ zu flach ist.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call verlangt, erfindet das Modell keinen Seiteninhalt. Das ist produktionsreif genug. Die P2-Leistung von 60 zeigt aber, dass die Fehlerkommunikation nicht immer sauber priorisiert und präzise formuliert wird. Akzeptabel für Assistenz- und Engineering-Flows. Für vollautomatische Nutzerantworten sollte ein Fehler-Template vorgeschaltet werden.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetitiv. Mit 76.00 Combined liegt das Modell 8.07 Punkte über dem Fleet-Ø von 67.93. Für souveräne Umgebungen ist das ein belastbarer Befund. Das Provenienzrisiko der Community-Finetune-Kette bleibt jedoch mittel und gehört in die Governance-Prüfung.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Engineering-, Coding- und Recherchepipelines, in denen das Modell Tools auswählt, Ergebnisse einsammelt und ein Mensch oder Validator die Endausgabe prüft. Nicht die erste Wahl für Compliance-, Rechts- oder Policy-Pipelines, in denen die Synthese selbst bereits entscheidungsfähig sein muss. Wenn Sie es einsetzen, dann mit hartem Tool-Call-Schema, URL- und Argument-Validierung sowie einem zweiten Prüfschritt für verdichtete Aussagen.