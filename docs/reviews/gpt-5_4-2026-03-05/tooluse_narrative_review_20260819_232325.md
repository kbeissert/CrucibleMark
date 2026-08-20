**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:23:25


Bedingt deploy, weil die Tool-Nutzung insgesamt nur moderat belastbar ist und der Tool-Call nicht durchgehend valide blieb, obwohl kein Halluzinationsbefund vorliegt. Für produktive MCP-Pipelines reicht das für überwachte Workflows, nicht für autonome Übergabe.

**Tool-Execution-Profil**

GPT-5.4 zeigt keine stabile Werkzeugintelligenz. Das Kernproblem ist nicht rohe Extraktion, sondern die Wahl des richtigen Werkzeugs. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis eine Suche statt eines direkten Fetch nötig ist, fällt das Modell mit schwacher Trefferquote auf. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und anschließendes Fetch misst, arbeitet es deutlich besser. Das spricht gegen adaptive Tool-Wahl und eher für ein Muster: Wenn eine URL naheliegt, liefert es brauchbare Calls. Wenn erst entschieden werden muss, welches Tool die Informationslücke schließt, wird es unsicher. Für MCP-Umgebungen heißt das: gute Chancen in vorstrukturierten Pipelines, erhöhtes Risiko in offenen Rechercheflüssen. Retry war nicht erforderlich. Das Problem liegt also nicht primär im Format, sondern in der Entscheidung vor dem Call.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. GPT-5.4 kann Fetch-Inhalte sehr stark komprimieren und korrekt herausziehen, was der sehr gute Lauf bei HTTP Fetch & Extract klar zeigt. Diese Stärke bricht aber ein, sobald Recherche, Quellenauswahl oder Mehrsprachigkeit dazukommen. Die Verdichtung ist dann nicht robust genug für verlässliche Endausgaben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Ergebnis bei EU License Research ist der kritische Punkt. Der Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen geholt statt aus Trainingswissen beantwortet werden. Hier ist die Synthese schwach. Zwar wurde keine Halluzination erkannt, aber das Modell zeigt auch kein starkes Vertrauenssignal, dass es sich konsequent an frisch beschaffte Quellen bindet. Für Compliance-nahe oder zeitkritische Faktenabfragen ist das zu wenig.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich GPT-5.4 brauchbar. Im 404-Test, der transparente Kommunikation bei einem fehlgeschlagenen Aufruf statt erfundenem Seiteninhalt misst, bleibt das Modell sauber und produziert keinen Ersatzinhalt. Das ist für Produktion akzeptabel. Die Pipeline kann auf diesem Verhalten aufbauen, wenn Fehlerpfade explizit modelliert sind.

**Betriebsprofil**

Total 39.71s. Modellaufrufe 2.45s und 3.93s. MCP-Latenz 0.24s. Für die erreichte Leistung langsam. Preis: $2.5/1M Input, $15.0/1M Output. Für einen Frontier-Generalisten nicht günstig genug, um schwache Tool-Selektion zu kompensieren.

**Fazit & Empfehlung**

Geeignet für assistierte Tool-Pipelines mit enger Aufgabenführung, festen URL- oder Fetch-Pfaden und nachgelagerter Validierung. Nicht geeignet für autonome Rechercheketten, Compliance-Abfragen oder dynamische Tool-Router, in denen das Modell selbst erkennen muss, ob Suche, Fetch oder Quellenwechsel nötig ist. Wenn Sie GPT-5.4 einsetzen, dann als starken Verdichter hinter einer separaten Orchestrierungsschicht, nicht als primären Tool-Entscheider.