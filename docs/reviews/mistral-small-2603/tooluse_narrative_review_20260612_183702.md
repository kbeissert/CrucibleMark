**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:37:02


Bedingt deploy, weil das Modell trotz brauchbarer Teiltreffer im Tool-Pfad kein verlässlich valides MCP-Verhalten zeigt, Retry benötigt und mit Combined 53.46 sowie erkannter Halluzination das Vertrauensniveau für autonome Tool-Pipelines nicht erreicht.

**Tool-Execution-Profil**

Mistral Small 4 kann Tools ausführen, aber nicht stabil orchestrieren. Das Kernproblem ist nicht reine Abruffähigkeit, sondern Werkzeugwahl und Protokolltreue. Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt das Modell deutlich ab. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließenden Fetch misst, arbeitet es dagegen solide. Das spricht nicht für flexible Tool-Intelligenz, sondern eher für ein engeres Muster: Wenn die Zieladresse ableitbar ist, funktioniert der Zugriff. Wenn erst erkannt werden muss, welches Tool den Informationspfad öffnet, bricht die Leistung ein.

Dass der Tool-Call nicht durchgängig valide war und ein Retry erforderlich wurde, wirkt hier primär wie ein Kombinationseffekt aus Format- und Verständnisproblem. Es ist nicht nur MCP-Syntax, sondern die vorgelagerte Entscheidung, welches Tool überhaupt angesprochen werden muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung von 39.17 zeigt, dass Mistral Small 4 extrahierte Informationen nur begrenzt in belastbare, präzise Kurzantworten überführt. Das sieht man besonders bei HTTP Fetch & Extract sowie bei Multilingual Search & Synthesis. Für produktive Pipelines ist das kritisch, weil nicht der Tool-Call selbst, sondern die letzte Meile der Ergebnisaufbereitung beim Nutzer ankommt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt gegen aktuelle Web-Quellen prüft, bleibt das Modell ausreichend diszipliniert. Content-Verification-State A und keine Halluzination sind hier ein echtes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, halluziniert das Modell keinen Seiteninhalt. Das ist der entscheidende Punkt und für Produktion akzeptabel. Die eigentliche Schwäche liegt in der Qualität der Fehlerkommunikation und Nachverdichtung, nicht im Erfinden von Ersatzfakten.

**Souveränitätsprofil**

Lokal betreibbar, offen lizenzierbar und für souveräne Deployments attraktiv. Leistungseitig bleibt es aber 1.37 Punkte unter dem Fleet-Ø von 67.62. Der Souveränitätsvorteil kompensiert die Tool-Schwächen nur dann, wenn Governance wichtiger ist als autonome Tool-Zuverlässigkeit.

**Fazit & Empfehlung**

Geeignet für assistierte Pipelines mit engem Tool-Rahmen, vorgegebenen URLs, menschlicher Nachkontrolle und souveränem Betrieb. Nicht geeignet für dynamische MCP-Setups, in denen das Modell selbst zwischen Suche, Fetch und Synthese entscheiden muss. Wer ein lokal betreibbares Modell für kontrollierte Retrieval-Aufgaben sucht, kann es einsetzen. Wer einer Instanz eigenständig Tool-Infrastruktur übergeben will, sollte hier nicht auf Autonomie vertrauen.