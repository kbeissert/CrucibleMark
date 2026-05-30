**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:17


Nicht deploy, weil das Modell bei schwacher Gesamtleistung Tool-Aufrufe nicht valide und nur per Retry stabil genug bekommt. Für produktive MCP-Pipelines ist diese Kombination aus Combined 48.50, ungültigen Tool-Calls und erkanntem Halluzinationsrisiko nicht tragfähig.

**Tool-Execution-Profil**

Mistral Medium 1.0 zeigt keine verlässliche Werkzeugintelligenz, sondern eher ein partiell funktionierendes Ausführungsmuster. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt es mit P1 35 klar ab. Das spricht gegen situative Tool-Wahl in offenen Umgebungen. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Modellwissen prüft, erreicht es mit P1 75 deutlich bessere Werte. Es kann also bekannte Pfade brauchbar konstruieren, erkennt aber nicht zuverlässig, wann ein anderes Werkzeug nötig ist.

Der Retry-Bedarf wirkt hier primär wie ein Protokoll- und Ausführungsproblem, nicht nur wie ein Antwortformatfehler. Dass Tool-Calls als nicht valide markiert sind, ist für MCP-Betrieb kritischer als ein bloß holpriges Schema. In einer Tool-Infrastruktur zählt der erste korrekte Call.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. P2 42.50 zeigt, dass die Verdichtung aus Tool-Outputs zu oft an Präzision verliert. Das sieht man besonders bei EU License Research mit P2 20 und bei Web Search & Tool Selection mit P2 20. Solide ist nur der engere Extraktionspfad: HTTP Fetch & Extract, also strukturierte Faktenentnahme aus echtem Fetch-Content, kommt auf P2 60.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es nicht offen. Das ist der positive Teil. Der Vertrauensbefund bleibt trotzdem schwach, weil Content-Verification-State B2 bei P2 20 zeigt, dass das Modell die Quelle nicht sauber in belastbare Aussagen überführt. Da global Halluzination erkannt wurde, ist das als Sicherheitsrisiko zu werten: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die gesamte Pipeline ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Call misst, verhält sich das Modell akzeptabel. P2 80 und keine Halluzination trotz 404 zeigen, dass es Fehler offenlegt statt Seiteninhalt zu erfinden. Das ist produktionsgerecht und einer der wenigen klar belastbaren Befunde.

**Betriebsprofil**

Call 1: 5.21s  
MCP-Latenz: 0.21s  
Call 2: 4.50s  
Total: 59.59s  
Kosten/Run: local  

Langsam für die gelieferte Qualität. Kostenseitig lokal, aber der Zeitbedarf steht nicht im Verhältnis zur Ausführungssicherheit.

**Fazit & Empfehlung**

Geeignet höchstens für überwachte Assistenz-Pipelines mit enger Tool-Vorgabe, einfacher Fetch-Extraktion und Pflichtprüfung durch eine zweite Instanz. Nicht geeignet für autonome MCP-Orchestrierung, dynamische Tool-Selektion, Compliance-nahe Recherche oder Workflows, in denen ein ungültiger Tool-Call bereits ein Incident ist. Wenn Sie einem Modell eigenständig Infrastruktur übergeben wollen, ist dieses hier nicht belastbar genug.