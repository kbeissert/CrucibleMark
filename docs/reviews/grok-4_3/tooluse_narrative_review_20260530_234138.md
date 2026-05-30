**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:38


Bedingt deploy, weil Grok 4.3 valide Tool-Calls liefert und keine Halluzination im Lauf zeigte, aber die Synthesetreue mit Combined 63.67 und besonders schwachem P2 nicht stabil genug für vertrauenskritische MCP-Pipelines ist.

**Tool-Execution-Profil**

Die operative Tool-Seite ist brauchbar. P1 von 83.33, valide Tool-Calls und kein Retry-Bedarf zeigen, dass das Modell MCP-konform arbeitet und Aufrufe formal sauber absetzt. Das ist die Mindestvoraussetzung für produktive Tool-Nutzung, und die erfüllt Grok 4.3.

Bei der Werkzeugwahl wirkt es jedoch eher solide als intelligent. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, erreicht es 80 und erkennt den Bedarf meist korrekt. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann fetch ausführen lässt, liegt es ebenfalls bei 80. Das spricht für robuste Basiskompetenz, aber nicht für besonders adaptive Tool-Strategie. Das Muster ist konsistent gut, nicht erkennbar planend oder präzise genug für stark verzweigte Agentenflüsse.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher der kritische Punkt. P2 von 43.33 zeigt, dass Grok 4.3 gefundene Inhalte nur begrenzt sauber zusammenzieht. Das sieht man auch in den Assets: EU License Research fällt auf 20, mehrere weitere Aufgaben bleiben bei 40, nur HTTP Fetch & Extract und Multilingual Search & Synthesis erreichen 60. Für einfache Zusammenfassungen reicht das. Für Compliance, Policy oder extraktionsnahe Übergaben an nachgelagerte Systeme ist es zu ungenau.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt prüft, halluziniert das Modell zwar nicht, aber der Content-Verification-State B2 bei P2=20 ist kein starkes Vertrauenssignal. Das Modell bleibt formal auf der sicheren Seite, zeigt aber keine verlässliche Bindung an die recherchierte Evidenz.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit Tool-Fehlern gegen erfundenen Ersatzinhalt prüft, bleibt Grok 4.3 auf der akzeptablen Seite. Es halluziniert trotz Fehler keinen Seiteninhalt. P2=40 zeigt allerdings, dass die Fehlerkommunikation nicht besonders präzise oder hilfreich verdichtet ist. Für Produktion ist das akzeptabel, weil Transparenz wichtiger ist als Eleganz.

**Betriebsprofil**

52.75s total: langsam.  
2.70s und 5.17s Modell-Calls, 0.92s MCP-Latenz: die End-to-End-Zeit liegt nicht am Tooling allein.  
$0.011412 pro Run: günstig bis moderat.  
Im Verhältnis zur Leistung ist das Preisprofil in Ordnung, das Latenzprofil nicht.

**Fazit & Empfehlung**

Geeignet für allgemeine MCP-Pipelines mit niedriger Faktensensitivität, etwa Recherche-Vorstufen, mehrsprachige Suche und einfache Tool-gestützte Assistenz. Nicht geeignet für Compliance, Lizenzprüfung, präzise Evidence-Synthesis oder Workflows, in denen Tool-Ergebnisse knapp und belastbar in strukturierte Entscheidungen übersetzt werden müssen. Wenn Sie es einsetzen, dann mit enger Ausgabevalidierung und klarer Trennung zwischen Tool-Ausführung und finaler fachlicher Verdichtung.