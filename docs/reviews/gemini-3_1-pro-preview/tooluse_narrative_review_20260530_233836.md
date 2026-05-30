**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:36


Bedingt deploy, weil die Tool-Ausführung produktionsreif wirkt, die Synthese aber zu oft an Präzision verliert. Bei validen Tool-Calls, keiner erkannten Halluzination und einem Combined-Score von 74.17 ist das Modell für Tool-Pipelines tragfähig, aber nicht für hochwertige Verdichtungsaufgaben ohne nachgelagerte Kontrolle.

**Tool-Execution-Profil**

Hier liegt die klare Stärke. Gemini 3.1 Pro Preview wählt Werkzeuge nicht blind nach Schema, sondern zeigt brauchbare Tool-Intelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 100. Das spricht für saubere Situationsdiagnose in offenen Pipelines. Beim URL-Construction-Test, der korrekte Ziel-URL plus anschließenden Abruf verlangt, bleibt es mit P1 80 solide, aber nicht deterministisch genug für fragile Fetch-Ketten. Die Calls selbst waren valide, MCP-konform und ohne Retry. Das ist für produktive Orchestrierung wichtiger als sprachliche Eleganz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 60 zeigt ein Modell, das Ergebnisse meist brauchbar zusammenführt, aber Details nicht konsistent scharf hält. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis mit jeweils P2 40. Für Recherche-Pipelines mit knapper, kontrollierter Weitergabe reicht das oft. Für Compliance, Policy oder Executive Summaries ist es zu ungleichmäßig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt; Content-Verification-State A. Das Modell bleibt also grundsätzlich in der Tool-Spur. Das senkt das Risiko, dass es alte Modellkenntnisse als frische Recherche ausgibt.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenem Abruf statt erfundenem Seiteninhalt misst, reagiert das Modell akzeptabel. P2 80 und keine Halluzination trotz Fehler bedeuten: Es kommuniziert Scheitern sichtbar, statt Lücken zu kaschieren. Für Produktion ist das die Mindestanforderung, und sie wird erfüllt.

**Betriebsprofil**

Total 108.34s. Call 1: 4.09s. Call 2: 13.26s. MCP-Latenz: 0.71s. Insgesamt langsam für einen Generalist-Frontier-Einsatz. Kosten pro Run: 0.034276. Preislich moderat, gemessen an der Leistung vertretbar, aber nicht effizient.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche- und Routing-Pipelines, in denen Tool-Wahl, Protokolltreue und ehrlicher Fehlerumgang wichtiger sind als erstklassige Endverdichtung. Nicht geeignet als letzte Instanz für Compliance-Texte, mehrsprachige Synthesen mit hohem Genauigkeitsanspruch oder jede Pipeline, in der die Modellantwort ohne Review direkt weiterverwendet wird. Gute Orchestrierungs-Komponente, nur mittelstarker Synthese-Layer.