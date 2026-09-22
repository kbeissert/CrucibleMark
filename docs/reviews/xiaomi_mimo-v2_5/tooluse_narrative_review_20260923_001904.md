**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:19:04


Bedingt deploy, weil die Tool-Ausführung stark ist, aber invalide Tool-Calls und ein Halluzinationssignal das Vertrauen in eine unbeaufsichtigte MCP-Pipeline begrenzen. Der Combined-Score ist gut, reicht hier aber nicht als Freifahrtschein.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 zeigt klare Werkzeugintelligenz bei der Auswahl des richtigen Pfads. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis erst gesucht statt direkt gefetcht wird, erkennt das Modell den Bedarf korrekt und erreicht volle Tool-Execution. Das spricht gegen ein starres Muster. Beim URL-Construction-Test, der die präzise Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist es brauchbar, aber nicht deterministisch genug. P1 von 80 heißt in der Praxis: Das Modell kommt oft ans Ziel, aber nicht verlässlich genug für Pipelines mit enger Schematreue.

Kritisch ist der Befund „Tool-Call valide: false“. Das ist kein bloßer Stilfehler, sondern ein Integrationsrisiko auf MCP-Ebene. Positiv ist, dass kein Retry erforderlich war. Das deutet eher auf einzelne Protokoll- oder Argumentfehler als auf ein grundsätzliches Verständnisproblem hin.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 von 70 wirkt akzeptabel, aber die Streuung ist hoch. HTTP Fetch & Extract und Tool Failure Handling (404) sind mit 80 solide. Dagegen fallen EU License Research mit 40, Web Search & Tool Selection mit 40 und vor allem Multilingual Search & Synthesis mit 15 deutlich ab. Das Modell kann also Informationen beschaffen, verdichtet sie aber nicht stabil in belastbare Endantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Das ist der wichtigste Entlastungspunkt. Gleichzeitig steht global „Halluzination erkannt: true“. Damit bleibt ein Sicherheitsrisiko bestehen: Sobald ein Modell erfundene Fakten als Tool-Ergebnisse ausgibt, wird die gesamte Tool-Infrastruktur fragwürdig.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei Tool-Fehlern statt erfundenem Seiteninhalt misst, reagiert MiMo V2.5 produktionstauglich. P2 von 80 und keine Halluzination trotz Fehler bedeuten: Es kommuniziert Fehlschläge offen und füllt Lücken nicht mit Ersatzfakten. Das ist für produktive Agenten ein tragfähiges Minimum.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es mit einem Sovereignty Gap von -0.89 Punkten unter dem Fleet-Ø von 68.17 praktisch auf Fleet-Niveau.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Recherche- und Orchestrierungs-Pipelines mit menschlicher Abnahme oder nachgelagerter Validierung. Weniger geeignet für Compliance-, Policy- oder mehrsprachige Synthese-Workflows, in denen die Endantwort selbst beweisfähig sein muss. Wenn Sie MiMo V2.5 einsetzen, dann als Tool-Operator mit engem Output-Schema und externem Verifier, nicht als letzte vertrauensgebende Instanz.