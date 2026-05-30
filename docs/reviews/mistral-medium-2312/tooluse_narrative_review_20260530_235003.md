**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:50:03


Nicht deploy für autonome MCP-Pipelines, weil der kombinierte Befund schwach ist, Tool-Calls nicht durchgängig valide sind und ein Halluzinationssignal das Vertrauen in Tool-Ausgaben bricht.

**Tool-Execution-Profil**

Mistral Medium 1.0 wirkt bei der Tool-Nutzung nicht wirklich agentisch, sondern eher schemagetrieben. Das sieht man an der Lücke zwischen Web Search & Tool Selection und URL Construction & Fetch. Beim Test, ob das Modell ohne Hinweis erkennt, dass zuerst web_search statt fetch nötig ist, fällt es mit P1 35 deutlich ab. Wenn die Ziel-URL bereits aus eigenem Wissen ableitbar ist, arbeitet es mit P1 75 wesentlich solider. Das spricht gegen echte Werkzeugwahl unter Unsicherheit und für ein festes Muster: bekannte URL ableiten, dann fetch. Für dynamische Pipelines ist genau diese Schwäche kritisch. Dass Retry erforderlich war, wirkt hier weniger wie ein reines Formatproblem als wie ein Verständnisproblem bei der Wahl des passenden Werkzeugs und der Protokollsequenz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. Die P2-Leistung von 42.5 zeigt, dass es Inhalte aus Tools nicht stabil in präzise, entscheidungsreife Antworten überführt. Das Muster ist konsistent: HTTP Fetch & Extract ist mit P2 60 noch brauchbar, aber EU License Research mit P2 20, Web Search & Tool Selection mit P2 20 und Multilingual Search & Synthesis mit P2 40 liegen klar unter Produktionsniveau.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training kommen, halluziniert es zwar nicht direkt, aber der Content-Verification-State B2 bei P2 20 ist kein Vertrauenssignal. Zusätzlich ist global ein Halluzinationsbefund gesetzt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Pipeline ihre Verlässlichkeit.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt misst, erreicht es P2 80 und halluziniert trotz Fehlschlag nicht. Das ist der belastbarste Produktionshinweis im Profil. Es kann also Scheitern offenlegen, auch wenn es bei erfolgreicher Tool-Nutzung nicht konsistent genug arbeitet.

**Betriebsprofil**

Call 1: 5.21s. MCP-Latenz: 0.21s. Call 2: 4.50s. Total: 59.59s.  
Kosten/Run: local.  
Für die gezeigte Leistung zu langsam.

**Fazit & Empfehlung**

Geeignet höchstens als beaufsichtigtes Hilfsmodell in einfachen Fetch-und-Zusammenfassen-Pipelines mit harter Validierung, engen Prompts und verpflichtender menschlicher Abnahme. Nicht geeignet für autonome Recherche, Tool-Routing, Compliance-nahe Aufgaben oder mehrstufige MCP-Orchestrierung, in der das Modell selbst entscheiden muss, welches Tool wann aufzurufen ist.