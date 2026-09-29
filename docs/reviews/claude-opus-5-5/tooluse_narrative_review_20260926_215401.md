**Deployment-Urteil**

> **Erstellt am:** 26.09.2026, 21:54:01


Bedingt deploy, weil die Tool-Nutzung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauensmodell einer MCP-Pipeline direkt berühren. Der Gesamteindruck ist gut, aber nicht frei übergabefähig.

**Tool-Execution-Profil**

Claude Opus 5.5 zeigt echte Werkzeugintelligenz. Beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, entscheidet es korrekt und sicher. Das spricht gegen starres Schema-Verhalten und für kontextabhängige Orchestrierung. Auch die EU License Research-Aufgabe und die mehrsprachige Recherche laufen auf P1 sauber.

Schwächer ist die Präzision in der Ausführung. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist die Richtung richtig, aber nicht deterministisch genug. Der globale Befund tool_call_valid=false bestätigt das operative Risiko: Das Modell plant gut, produziert aber nicht durchgängig protokollsaubere Calls. Retry war nicht nötig, daher liegt das Problem eher in Ausführungspräzision als in Formatkollaps.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung von 62.50 zeigt, dass Claude Opus 5.5 gefundene Inhalte meist brauchbar zusammenzieht, aber nicht zuverlässig eng an den Quellbefund gebunden bleibt. Besonders im HTTP Fetch & Extract-Test und in der mehrsprachigen Synthese bleibt die Verdichtung funktional, aber nicht hochpräzise. Der 404-Fall zieht das Bild deutlich nach unten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, bleibt das Modell auf der richtigen Seite. Dort wurde keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal für aktuelle Recherche. Der übergreifende Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird nicht nur die Antwort schlechter, sondern die Verlässlichkeit der gesamten Infrastruktur beschädigt.

**Fehlerresilienz**

Hier liegt die harte Grenze für produktiven Einsatz. Im Tool Failure Handling (404)-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls prüfen soll, halluziniert das Modell trotz Fehler Seiteninhalt. P2=35 ist nicht bloß schwach, sondern produktionskritisch. Ein 404 muss als 404 kommuniziert werden. Ersatzinhalt ist in MCP-Pipelines nicht tolerierbar, weil Downstream-Komponenten den Text sonst als echten Fetch-Befund behandeln.

**Betriebsprofil**

Total 108.54s pro Run. Call-Latenzen 2.85s und 14.03s, MCP-Latenz 1.21s. Für die gezeigte Leistung langsam. Preis: $5.0/1M Input und $25.0/1M Output. Für Frontier-Niveau nicht billig, gemessen an der Synthesetreue und dem Fehlerrisiko eher teuer.

**Fazit & Empfehlung**

Geeignet für orchestrierende Recherche-Pipelines mit menschlicher Freigabe, insbesondere wenn Tool-Wahl und Langkontext wichtiger sind als streng deterministische Ergebnisbindung. Nicht geeignet für Compliance-, Dokumentations-, Incident- oder andere Ketten, in denen ein fehlgeschlagener Tool-Call strikt als Fehler propagiert werden muss. Vor produktivem Einsatz braucht das Modell harte Guardrails: Tool-Result-Verification, 404-Abbruchlogik und Validierung aller Tool-Ausgaben vor der Synthese.