**Deployment-Urteil**

> **Erstellt am:** 28.06.2026, 21:57:19


Bedingt deploy: DeepSeek V3.1 zeigt brauchbare Tool-Steuerung, ist aber für produktive MCP-Pipelines ohne harte Guardrails nicht vertrauenswürdig, weil Halluzination erkannt wurde und der Tool-Call im Lauf nicht durchgehend valide blieb.

**Tool-Execution-Profil**

Die Tool-Ausführung ist auf den ersten Blick stärker als die Gesamtnote vermuten lässt. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den richtigen Werkzeugtyp zuverlässig. Das spricht gegen starres Musterverhalten und für echte Werkzeugwahl im Prompt-Kontext. Auch beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL aus eigenem Wissen misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines.

Der Kernbefund lautet daher: DeepSeek V3.1 versteht, welches Tool grundsätzlich gebraucht wird, produziert aber nicht konsistent genug protokollsaubere Ergebnisse. Für Architekturen mit tolerantem Orchestrator ist das handhabbar. Für strikt validierende MCP-Strecken ist es noch kein Selbstläufer. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt damit eher in der inhaltlichen und formalen Erstqualität als in einem bloßen Reparaturfall.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 51.67 der klare Engpass. Bei HTTP Fetch & Extract und bei URL Construction & Fetch verdichtet das Modell sauber genug. Sobald die Aufgabe stärker selektive Bewertung oder Suchergebnisse über mehrere Quellen verlangt, fällt die Synthesequalität sichtbar ab. Besonders auffällig ist das bei Web Search & Tool Selection: gute Werkzeugwahl, aber schwache Verdichtung des Ertrags.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell hinreichend auf dem Tool-Pfad. Dort wurde keine Halluzination erkannt. Das ist ein wichtiges Vertrauenssignal. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko: Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, untergräbt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Hier liegt der produktionskritische Bruch. Im Test Tool Failure Handling (404), der transparentes Fehlermanagement statt erfundenem Ersatzinhalt prüft, halluziniert DeepSeek V3.1 trotz fehlgeschlagenem Aufruf Seiteninhalt. Das ist nicht nur schwache Fehlerbehandlung, sondern ein Ausschlusskriterium für autonome Retrieval- oder Compliance-Pipelines. Ein akzeptables Modell sagt in diesem Fall klar, dass der Abruf gescheitert ist.

**Betriebsprofil**

Call 1: 4.22s. MCP-Latenz: 0.89s. Call 2: 18.85s. Total: 143.77s. Langsam für die gezeigte Verlässlichkeit. Kosten/Run: local. Preisblatt: günstig bis moderat, aber die Laufzeit relativiert den Kostenvorteil.

**Fazit & Empfehlung**

Geeignet für assistierte Recherche-Pipelines, interne Analysten-Workflows und Tool-gestützte Systeme mit strikter Ergebnisvalidierung außerhalb des Modells. Nicht geeignet für unbeaufsichtigte Agenten, Compliance-Automation, Incident-Workflows oder jede Pipeline, in der Tool-Fehler sauber und wahrheitsgemäß behandelt werden müssen. Wenn Sie DeepSeek V3.1 einsetzen, dann nur mit harter Antwortprüfung, expliziter Tool-Error-Gating-Logik und einer Policy, die unbestätigte Inhalte konsequent verwirft.