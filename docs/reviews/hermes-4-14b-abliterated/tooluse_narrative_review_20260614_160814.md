**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:08:14


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, die Gesamtnote mit 69.54 im brauchbaren Bereich liegt, aber die erkannte Halluzination die Pipeline-Vertrauensgrenze klar begrenzt.

**Tool-Execution-Profil**

Hermes 4 14B kann einer MCP-Toolkette formal übergeben werden. Die Tool-Calls waren valide, ein Retry war nicht nötig, und bei der Werkzeugwahl zeigt das Modell echte Situationsanpassung statt reines Schema-Folgen. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erreichte es P1 100. Das spricht für brauchbare Tool-Intelligenz in offenen Retrieval-Situationen. Beim Test URL Construction & Fetch, der die korrekte Ableitung einer Ziel-URL aus Vorwissen misst, landete es bei P1 80. Es kann also bekannte Pfade oft brauchbar konstruieren, aber nicht präzise genug für strikt deterministische Fetch-Pipelines. Insgesamt ist die Protokolltreue stark. Die Schwäche liegt nicht im Aufruf, sondern in dem, was nach dem Aufruf aus den Ergebnissen gemacht wird.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. P2 50 zeigt ein klares Muster: Das Modell beschafft Informationen, verdichtet sie aber inkonsistent. Besonders schwach ist HTTP Fetch & Extract, das präzise Extraktion aus echtem Seiteninhalt misst, mit P2 15. Auch Web Search & Tool Selection bleibt mit P2 35 nach korrekter Recherche in der Auswertung zu grob. Für produktive Pipelines heißt das: Retrieval gelingt häufiger als saubere, faktengebundene Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis beantwortet werden, blieb es formal im Tool-Pfad. P2 40 und Content-Verification-State A zeigen aber nur eingeschränkt belastbare Verdichtung. Da insgesamt eine Halluzination erkannt wurde, ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Infrastruktur ihre Prüfspur.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsnah. Im Test Tool Failure Handling (404), der Transparenz bei fehlschlagenden Aufrufen statt erfundenem Ersatzinhalt misst, erreichte es P2 80. Es kommunizierte den Fehler, ohne Seiteninhalt zu erfinden. Das ist für reale MCP-Pipelines akzeptabel und deutlich wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar, ohne externen Datentransfer, und damit für souveräne Deployments attraktiv. Mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.84 bleibt es zugleich fleet-nah konkurrenzfähig. Der Preis dafür ist nicht die Tool-Nutzung, sondern die begrenzte Synthesedisziplin der abliterierten Variante.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit Human-in-the-Loop, für Recherche-Vorstufen, Fehlerdiagnose und agentische Workflows, in denen das Tooling die Hauptarbeit macht und nachgelagerte Validierung existiert. Nicht geeignet für Compliance, regulatorische Ausgaben, präzise Extraktionspipelines oder autonome Systeme, die Tool-Ergebnisse ungeprüft weiterreichen. Wenn Sie ein offenes lokales Modell für MCP-Orchestrierung suchen, ist es ein brauchbarer Operator. Wenn Sie belastbare faktengebundene Synthese brauchen, ist es die falsche Endstufe.