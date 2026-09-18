**Deployment-Urteil**

> **Erstellt am:** 18.09.2026, 09:33:43


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein erkannter Halluzinationsfall bei zugleich nicht valide abgeschlossenem Tool-Call das Vertrauen für autonome Produktionspipelines begrenzt.

**Tool-Execution-Profil**

Occamy zeigt echte Werkzeugorientierung, keine reine Antwort-vor-Tool-Reflexe. Beim Test **Web Search & Tool Selection**, der prüft, ob ohne Hinweis statt fetch ein Suchwerkzeug gewählt werden muss, erkennt das Modell den richtigen Werkzeugtyp sehr sicher. Das spricht für Planungsintelligenz in offenen Retrieval-Schritten. Beim Test **URL Construction & Fetch**, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, ist es brauchbar, aber weniger präzise. Hier wirkt das Modell nicht starr, sondern situationsabhängig kompetent: Es wählt Tools gut, produziert aber nicht durchgehend robuste, protokollsaubere Calls. Dass der globale Tool-Call als nicht valide markiert wurde, ist für MCP-Pipelines relevant. Das Problem liegt damit nicht in der grundsätzlichen Werkzeugwahl, sondern in der letzten Meile der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 42.50 passt zum Muster der Assets: **HTTP Fetch & Extract** und **Multilingual Search & Synthesis** zeigen deutliche Schwächen bei präziser Verdichtung, obwohl die Recherche oft gelingt. Occamy kommt also an Informationen heran, transformiert sie aber nicht zuverlässig in belastbare, knappe Ergebnisform. Für Architekturen, in denen das Modell Tool-Output in entscheidungsreife Fakten überführen soll, ist das die zentrale Grenze.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt Occamy akzeptabel am abgerufenen Material und halluziniert dort nicht. Das ist ein gutes Vertrauenssignal. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim Test **Tool Failure Handling (404)**, der transparentes Verhalten bei fehlgeschlagenem Abruf misst, reagiert Occamy akzeptabel. Es erfindet trotz 404 keinen Seiteninhalt. Diese Fehlerdisziplin ist produktionsrelevant. Ein Modell darf scheitern. Es darf nur keinen Ersatzinhalt behaupten.

**Souveränitätsprofil**

Lokal betreibbar und mit 65.29 Combined nur 2.74-Punkte unter dem Fleet-Ø von 68.03. Für eine local_sovereign-Option ist das konkurrenzfähig, aber nicht stark genug, um die Treueprobleme im Syntheseschritt zu kompensieren.

**Fazit & Empfehlung**

Geeignet für souveräne MCP-Pipelines, in denen das Modell primär Tools auswählt, Suchpfade anstößt und Rohresultate an nachgelagerte Validatoren oder deterministische Parser übergibt. Nicht geeignet als letzte Instanz für Compliance, Research-Synthesis oder entscheidungskritische Zusammenfassungen. Wer Occamy einsetzt, sollte Antworten strikt an Tool-Artefakte binden, freie Verdichtung minimieren und jedes finale Nutzerergebnis durch strukturierte Verifikation absichern.