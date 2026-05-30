**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:07


Bedingt deploy, weil Grok 3 valide Tool-Calls erzeugt und im Tool-Zugriff stark ist, aber die Synthesetreue mit Combined 67.67 nur moderat ausfällt und eine Halluzination im Lauf als Sicherheitsrisiko zählt.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet Grok 3 belastbar. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 von 90 zeigt eine stabile MCP-Anbindung. Besonders stark ist das Modell beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis das passende Werkzeug gewählt wird: Hier erkennt es sauber, dass web_search statt fetch nötig ist. Das spricht gegen starres Musterverhalten und für echte Werkzeugwahl.

Weniger präzise ist es beim URL-Construction-Test, der misst, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch ausführt. P1 80 ist brauchbar, aber nicht deterministisch genug für Pipelines, die exakte URL-Bildung ohne Nachsteuerung erwarten. Auch bei HTTP Fetch & Extract bleibt die Ausführung solide, doch nicht fehlerfrei.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher nur eingeschränkt produktionsfest. P2 von 45 zeigt, dass Grok 3 gefundene Inhalte oft nicht sauber genug zu belastbaren Arbeitsresultaten komprimiert. Das sieht man auch an EU License Research mit P2 40 und besonders deutlich an Multilingual Search & Synthesis mit P2 15. Für Pipelines, in denen aus Tool-Output direkt Compliance-, Policy- oder Kundenantworten entstehen, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt prüft, blieb Grok 3 beim abgefragten Web-Inhalt. Content-Verification-State A und keine Halluzination sind hier ein klares Vertrauenssignal. Gleichzeitig gilt: Der globale Halluzinationsfund ist als Sicherheitsrisiko zu lesen. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die Tool-Infrastruktur selbst unzuverlässig.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call prüft, halluziniert Grok 3 keinen Ersatzinhalt. Das ist der entscheidende Punkt. P2 40 heißt nicht gute Antwortqualität, aber akzeptable Produktionshygiene: Fehler werden offengelegt statt kaschiert.

**Betriebsprofil**

Total 48.83s. Call-Latenzen 2.52s und 4.78s, MCP 0.84s. Insgesamt langsam. Kosten pro Run 0.043641 USD. Für die gelieferte Syntheseleistung eher teuer.

**Fazit & Empfehlung**

Geeignet für recherchierende Pipelines mit Human-in-the-Loop, bei denen Tool-Wahl wichtiger ist als die letzte Verdichtungsstufe. Ebenfalls brauchbar für Agenten, die erst Quellen finden und Ergebnisse dann an einen zweiten Prüfschritt übergeben. Nicht geeignet für autonome Compliance-, Policy- oder mehrsprachige Antwortpipelines, in denen Tool-Output ohne nachgelagerte Validierung direkt veröffentlicht oder weiterverarbeitet wird.