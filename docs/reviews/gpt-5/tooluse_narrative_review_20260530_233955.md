**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:55


Bedingt deploy, weil GPT-5 valide Tool-Calls produziert und keine Halluzinationen im Benchmark gezeigt hat, die Synthesetreue nach Tool-Nutzung aber nur knapp produktionsreif ist.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet GPT-5 grundsätzlich MCP-konform. Der Tool-Call war valide, und P1 85.83 zeigt ein belastbares Ausführungsniveau. Entscheidend ist: Das Modell erkennt im Web-Search-&-Tool-Selection-Test meist korrekt, dass für unbekannte oder aktuelle Informationen zuerst Suche statt direktem Fetch nötig ist. Das spricht gegen bloßes Schema-Fahren und für echte Werkzeugwahl. Im URL-Construction-Test leitet es Zieladressen brauchbar aus Vorwissen ab und führt Fetch danach korrekt aus, aber nicht mit der Präzision, die man für streng deterministische Pipelines verlangen würde. Der erforderliche Retry wirkt hier eher wie ein Format- oder Ablaufproblem als wie ein Verständnisfehler. Das Muster ist: richtige Absicht, nicht immer im ersten Schuss sauber orchestriert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 56.67 ist für ein Frontier-Generalistenmodell der eigentliche Warnwert. GPT-5 sammelt Informationen zuverlässig, komprimiert sie aber in mehreren Assets zu grob oder zu generisch. Das sieht man besonders bei EU License Research und Tool Failure Handling (404), wo die Ausgabe formal korrekt bleibt, aber entscheidende Präzision und belastbare Verdichtung fehlen. Besser ist es bei HTTP Fetch & Extract, wo strukturierte Fakten aus echtem Seiteninhalt sauberer übernommen werden.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Vertrauenspunkt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, wurde keine Halluzination erkannt. Content-Verification-State A stützt dieses Urteil. Das Modell ist also eher konservativ als erfinderisch. Für produktive Tool-Pipelines ist das deutlich wichtiger als stilistische Schwächen in der Zusammenfassung.

**Fehlerresilienz**

Im 404-Test, der die Reaktion auf einen fehlschlagenden Tool-Call misst, hat GPT-5 keinen Seiteninhalt erfunden. Das ist akzeptables Produktionsverhalten. Die Schwäche liegt nicht in falschem Ersatzinhalt, sondern in der Qualität der Fehlerkommunikation und der anschließenden Verdichtung. Man kann diesem Modell Fehlerpfade anvertrauen, solange die Anwendung klare Fallback-Regeln vorgibt.

**Betriebsprofil**

Total 188.78s. Langsam. Einzelaufrufe 6.88s und 23.18s plus 1.40s MCP-Latenz. Kosten pro Run 0.077128 USD. Für die gezeigte Leistung nicht günstig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen korrekte Tool-Nutzung, vorsichtige Ausgabe und transparente Fehlerbehandlung wichtiger sind als knappe, präzise Endverdichtung. Gut passend für Recherche- und Assistenzstrecken mit nachgelagerter Validierung oder einem zweiten Verdichtungsschritt. Nicht die erste Wahl für Compliance-Summaries, entscheidungsnahe Briefings oder andere Pipelines, in denen die Antwort selbst bereits das finale, exakt kondensierte Produkt sein muss.