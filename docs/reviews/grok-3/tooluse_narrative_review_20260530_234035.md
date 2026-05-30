**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:35


Bedingt deploy, weil Grok 3 valide Tool-Calls erzeugt und im Ausführen stark ist, aber die Synthesetreue mit Combined 67.67 und global gesetzter Halluzinationsmarke nicht stabil genug für vertrauenskritische Pipelines wirkt.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet Grok 3 klar über Mindestniveau. P1 von 90 zeigt, dass das Modell MCP-konform agiert und keine Formatschwäche hat. Das sieht man besonders dort, wo Werkzeugwahl gefragt ist: Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung sauber. Das spricht für echte Tool-Intelligenz statt für ein starres Fetch-Muster. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar und führt den Abruf aus, aber nicht mit der Präzision, die man für deterministische Pipelines erwartet. Das Profil ist also klar: richtige Werkzeugklasse meist erkannt, Ausführung belastbar, Präzision in selbst abgeleiteten Zugriffspfaden nur ordentlich.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher unzuverlässig. P2 von 45 ist der eigentliche Engpass. Die Schwäche liegt nicht in der Beschaffung, sondern in der Verdichtung und Rückübersetzung in belastbare Antwortform. Das wird bei HTTP Fetch & Extract und besonders bei Multilingual Search & Synthesis sichtbar. Dort holt es die Informationen, verliert aber Genauigkeit, Priorisierung oder sprachübergreifende Konsistenz.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, bleibt Grok 3 im Testfall auf dem Tool-Pfad. Content-Verification-State A und keine Halluzination in diesem Asset sind ein gutes Vertrauenssignal. Trotzdem bleibt die globale Halluzinationsmarke ein Sicherheitsrisiko: In einer Tool-Pipeline ist nicht nur schlechte Zusammenfassung das Problem, sondern jede erfundene Tatsache, die wie Tool-Output aussieht.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem scheiternden Tool-Aufruf misst, reagiert Grok 3 akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler. P2 von 40 zeigt zwar schwache Fehlerverdichtung, aber keine gefährliche Erfindung. Für Produktion ist das wichtig: Transparente Fehlermeldung ist handhabbar, erfundener Ersatzinhalt wäre ein Ausschlusskriterium.

**Betriebsprofil**

Total 48.83s. Tool-Aufrufe 2.52s und 4.78s, MCP-Latenz 0.84s. Insgesamt langsam. Kosten pro Run 0.043641 USD. Für die gezeigte Leistung nicht günstig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Wahl und Tool-Ausführung wichtiger sind als perfekte Ergebnisverdichtung: Rechercheassistenz, explorative Web-Aufgaben, operator-in-the-loop Workflows. Nicht geeignet für Compliance, mehrsprachige Wissenssynthese, präzise Extraktionsstrecken oder automatisierte Systeme, die Tool-Output ohne menschliche Kontrolle weiterverarbeiten. Wenn Grok 3 eingesetzt wird, dann mit strikter Nachprüfung der finalen Antwortschicht, nicht der Tool-Schicht.