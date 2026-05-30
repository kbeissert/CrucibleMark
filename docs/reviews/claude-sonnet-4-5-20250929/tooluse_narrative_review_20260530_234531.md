**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:45:31


Bedingt deploy, weil die Tool-Aufrufe valide und meist treffsicher sind, das Modell aber bei Tool-Fehlern erfundene Inhalte ausgibt und damit die Vertrauenskette einer MCP-Pipeline bricht.

**Tool-Execution-Profil**

Claude Sonnet 4.5 arbeitet auf der Ausführungsseite stark. P1 liegt bei 90, Tool-Calls sind valide, und es brauchte keinen Retry. Das spricht für saubere MCP-Protokolltreue und dafür, dass das Modell Formate und Aufrufstruktur zuverlässig einhält. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt werden muss, trifft es die Werkzeugwahl sicher. Das wirkt nicht wie starres Schema-Fahren, sondern wie situative Auswahl. Beim URL-Construction-and-Fetch-Test, der die Ableitung einer Ziel-URL aus Weltwissen und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug für streng formalisierte Flows. Kurz: gute Tool-Intelligenz, leicht schwächere Präzision bei selbst konstruierten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 bei 50.83 ist der eigentliche Warnwert dieses Laufs. Solide bei HTTP Fetch & Extract und URL Construction & Fetch, deutlich schwach bei Web Search & Tool Selection, Tool Failure Handling (404) und besonders bei Multilingual Search & Synthesis. Das Modell kann Inhalte aus Tools übernehmen, aber es komprimiert und priorisiert sie nicht durchgängig belastbar genug für Pipelines, in denen die Antwort selbst als verwertbares Artefakt weitergereicht wird.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, bleibt es im Ergebnisraum. Content-Verification-State A und keine Halluzination sind ein positives Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko, nicht nur ein Qualitätsmangel: Wenn ein Modell in einzelnen Pfaden erfundene Fakten als Tool-Resultat ausgibt, ist die Infrastruktur nicht mehr auditierbar.

**Fehlerresilienz**

Hier liegt das produktionskritische Defizit. Im 404-Test, der transparentes Fehlermanagement statt erfundenen Ersatzinhalt prüft, halluziniert das Modell trotz fehlgeschlagenem Tool-Aufruf Seiteninhalt. P2 35 ist dabei nur Begleitwert. Der Kernbefund lautet: Es verschleiert den Fehlerfall. Für produktive Pipelines ist das ohne Ausnahme kritisch.

**Betriebsprofil**

Total 68.11s. Call 1 2.24s, MCP-Latenz 0.74s, Call 2 8.38s. Insgesamt langsam für die erzielte Synthesequalität. Kosten pro Run: $0.064233. Nicht teuer im absoluten Sinn, aber für ein Modell mit diesem Fehlermodus nicht effizient.

**Fazit & Empfehlung**

Geeignet für assistierte Research- und Operator-in-the-loop-Pipelines, in denen Tool-Auswahl wichtig ist und jede Endantwort noch validiert wird. Nicht geeignet für autonome Compliance-, Retrieval- oder Incident-Workflows, in denen Tool-Fehler strikt offengelegt werden müssen und die Antwort direkt weiterverarbeitet wird. Wenn Sie es einsetzen, dann nur mit harter Fehler-Gating-Logik, Ergebnisvalidierung und einer Policy, die bei jedem fehlgeschlagenen Fetch die Generierung stoppt.