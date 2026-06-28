**Deployment-Urteil**

> **Erstellt am:** 28.06.2026, 21:57:10


Bedingt deploy, weil die Tool-Ausführung oft stark ist, aber die Synthesetreue mit Combined 54.75 und ungültigem Tool-Call-Verhalten nicht ausreicht, um eine MCP-Pipeline ohne enge Leitplanken zu tragen.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, aber keine durchgehend verlässliche Protokolldisziplin. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, entscheidet es korrekt und erreicht volle Tool-Ausführung. Das spricht gegen ein starres Muster. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen misst, arbeitet es brauchbar, aber nicht deterministisch genug für harte Produktionspfade.

Kritisch ist der Meta-Befund: tool_call_valid=False. Das bedeutet nicht, dass es Tools grundsätzlich nicht versteht. Es bedeutet, dass die Aufrufe oder das umgebende Format nicht konsistent MCP-tauglich sind. Für einen Agentic-Orchestrator in der Frontier-Klasse ist das ein relevanter Mangel. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt also eher in der Erstpräzision als in wiederholtem Formatversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 29.17 ist der zentrale Befund dieses Laufs. Das Modell kann Informationen beschaffen, verliert aber beim Verdichten, Zuordnen und sauberen Rückführen in die Antwort. Das sieht man besonders an EU License Research und Multilingual Search & Synthesis, wo die Rechercheleistung hoch war, die inhaltliche Verarbeitung aber auf null fiel. Für produktive Tool-Pipelines ist genau das der Bruchpunkt: Das Tool hilft nur, wenn das Modell dessen Output belastbar weiterverarbeitet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, lag P2 bei 0. Zwar wurde dort keine Halluzination markiert, aber der globale Halluzinationsbefund ist dennoch True. Das ist ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Call gegen halluzinierten Ersatzinhalt misst, bleibt das Modell auf der akzeptablen Seite. Es erfindet keinen Seiteninhalt trotz Fehler. P2 40 ist nicht stark, aber operativ brauchbar. Für Produktion ist entscheidend: Es verschleiert den Fehler nicht.

**Betriebsprofil**

Call 1: 23.98s. Call 2: 2.87s. MCP-Latenz: 0.98s. Total: 167.01s. Langsam. Kosten/Run: local. Günstig im Inferenzpreis, aber die Laufzeit ist im Verhältnis zur schwachen Syntheseleistung nicht attraktiv.

**Fazit & Empfehlung**

Geeignet für überwachte Recherche-Pipelines, in denen ein zweites System die Antwort validiert oder nur Rohmaterial übernommen wird. Nicht geeignet für Compliance, Policy, Lizenz- oder mehrsprachige Wissenspipelines, in denen Tool-Ergebnisse präzise zusammengeführt und ohne Faktendrift ausgegeben werden müssen. Wenn Sie es einsetzen, dann als Tool-nahen Sammler mit strikter Ausgabevalidierung, nicht als letzte Instanz der Synthese.