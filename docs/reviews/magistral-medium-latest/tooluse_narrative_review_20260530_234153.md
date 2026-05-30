**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:53


Nicht deploy, weil die Tool-Calls nicht valide waren, Retries nötig wurden und der Combined-Score von 33.58 die Schwelle für verlässliche MCP-Pipelines klar verfehlt.

**Tool-Execution-Profil**

Magistral Medium zeigt kein belastbares Tool-Verhalten für produktive Orchestrierung. P1 von 41.67 bedeutet hier vor allem, dass das Modell den Übergang von Absicht zu formal korrektem Tool-Aufruf nicht stabil beherrscht. Die Tool-Selection-Daten sind dafür eindeutig: Beim Web-Search-and-Tool-Selection-Test, der ohne Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, bleibt es bei 35 Punkten. Beim URL-Construction-and-Fetch-Test, der präzise URL-Ableitung und sauberen Fetch verlangt, ebenfalls 35. Das spricht nicht für flexible Werkzeugwahl, sondern für ein starres Muster mit schwacher Situationsanpassung.

Dass `retry_required=true` gesetzt ist, wirkt hier eher wie ein Ausführungsproblem als wie ein reines Formatproblem. Gegen ein bloßes Syntaxthema spricht, dass die Schwäche konsistent über Suchwahl, URL-Bildung und mehrsprachige Recherche auftritt. Für eine MCP-Pipeline heißt das: zusätzlicher Kontrollcode, höhere Latenz und unsaubere Failure-Modes.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 26.67 ist der eigentliche Blocker, weil die Nutzlast nach dem Tool-Call nicht zuverlässig in brauchbare, präzise Antworten überführt wird. Das Bild ist stark uneinheitlich: HTTP Fetch & Extract gelingt mit P2 40 noch brauchbar, Tool Failure Handling (404) mit P2 80 sogar klar akzeptabel. Dagegen fallen EU License Research und Multilingual Search & Synthesis mit P2 0 vollständig aus. Gerade in Recherchepfaden mit mehreren Quellen oder Sprachwechseln bricht die Verdichtung weg.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Formal ja, aber nicht vertrauensstark. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, liegt P2 bei 0 bei Content-Verification-State B2. Es halluziniert nicht offen, aber es liefert auch keine verifizierbare, aus Tool-Inhalten abgeleitete Synthese. Für Compliance-nahe Pipelines reicht das nicht. Ein Modell muss hier nicht nur nichts erfinden, sondern sichtbar am abgerufenen Material bleiben.

**Fehlerresilienz**

Hier liegt die positive Ausnahme. Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, kommuniziert das Modell den Fehler sauber und halluziniert keinen Seiteninhalt. P2 80 ist für Produktion akzeptabel. Das schützt vor dem schlimmsten Fehlerbild: erfundener Ersatzinhalt trotz fehlgeschlagenem Abruf.

**Souveränitätsprofil**

Souveränitätsseitig attraktiv, leistungsmäßig nicht ausreichend. Das Modell liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Open-weights und europäischer Anbieter sind für Governance interessant, aber die lokale beziehungsweise souveräne Einsetzbarkeit kompensiert die Tool-Schwäche nicht.

**Fazit & Empfehlung**

Geeignet höchstens für überwachte Reasoning-Stufen ohne direkte Tool-Autorität, etwa als nachgelagerter Textumformer hinter hart validierten Retrieval-Komponenten. Nicht geeignet für autonome MCP-Pipelines, dynamische Tool-Wahl, Compliance-Recherche oder mehrsprachige Web-Workflows. Wenn Sie einem Modell Infrastruktur übergeben wollen, muss es Tools korrekt wählen, valide aufrufen und Ergebnisse belastbar verdichten. Das zeigt Magistral Medium in diesem Test nicht.