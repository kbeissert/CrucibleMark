**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:12


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, aber die Synthesequalität mit Halluzinationsbefund das Vertrauen in unbeaufsichtigte Tool-Pipelines begrenzt.

**Tool-Execution-Profil**

Hermes 4 70B arbeitet auf der Ausführungsseite stark. Die Tool-Calls sind valide, MCP-konform und in den suchgetriebenen Aufgaben treffsicher. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt wird, erkennt das Modell den richtigen Werkzeugtyp sicher. Das spricht gegen starres Musterfolgen und für tatsächliche Werkzeugwahl anhand der Aufgabe.

Schwächer ist es dort, wo es die Zieladresse selbst herleiten muss. Beim URL-Construction-&-Fetch-Test konstruiert es die URL oft brauchbar, aber nicht durchgehend präzise genug für deterministische Pipelines. Das ist kein Protokollproblem, sondern ein Präzisionsproblem vor dem Call. Dass ein Retry erforderlich war, passt dazu: eher Korrektur im Ablauf oder bei der Zielbestimmung, nicht grundlegendes Missverständnis der Tool-Schnittstelle.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung zeigt ein klares Gefälle zwischen Beschaffung und Verarbeitung. Hermes 4 70B holt Informationen zuverlässig, verdichtet sie aber häufig zu grob, lässt relevante Details liegen oder formuliert die Ausgabe nicht eng genug am Tool-Befund. Das sieht man besonders bei HTTP Fetch & Extract sowie Web Search & Tool Selection, wo die Ausführung stark ist, die Endantwort aber deutlich an Präzision verliert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es im verifizierten Web-Befund. Das ist das wichtigste Vertrauenssignal hier. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur. Für produktive Nutzung heißt das: Beschaffung ja, Synthese nur mit nachgelagerter Prüfung.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls prüft, erfindet Hermes 4 70B keinen Seiteninhalt. Das ist die Mindestbedingung für Produktion und wird erfüllt. Die schwache Wertung kommt daher, dass die Fehlerkommunikation wenig nützlich verdichtet ist. Operativ ist das akzeptabel: lieber knappe, unvollständige Fehlermeldung als konstruierter Ersatzinhalt.

**Souveränitätsprofil**

Lokal betreibbar mit offenen Gewichten und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84 und bleibt damit fleet-nah, aber nicht führend.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell Tools auswählt, Calls erzeugt und Rohbefunde an einen zweiten Prüf- oder Render-Schritt übergibt. Ebenfalls brauchbar für souveräne Recherche-Workflows mit Human-in-the-Loop. Nicht geeignet als alleinige letzte Instanz für Compliance, Extraktion mit hoher Faktendichte oder automatisierte Nutzerantworten ohne Verifikation. Wenn Sie ihm die Tool-Infrastruktur übergeben, dann als Beschaffer und Orchestrator, nicht als unkontrollierten Schlussredakteur.