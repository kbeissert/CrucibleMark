**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:21:13


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen in produktive MCP-Pipelines begrenzen. Der kombinierte Befund ist damit nur für kontrollierte Tool-Infrastrukturen tragfähig.

**Tool-Execution-Profil**

GLM-5.1 zeigt echte Werkzeugintelligenz statt bloßer Schema-Nachahmung. Beim Web-Search-&-Tool-Selection-Test, der prüft ob ohne Hinweis search statt fetch gewählt wird, trifft es die richtige Entscheidung sicher. Das ist ein starkes Signal für agentische Orchestrierung. Beim URL-Construction-Test, der die eigenständige Ableitung der Ziel-URL misst, arbeitet es brauchbar, aber nicht präzise genug für deterministische Fetch-Pipelines. Der P1-Wert bleibt hoch, die Protokolltreue nicht. Dass der Gesamtbefund tool_call_valid=false ausfällt, ist deshalb relevant: Das Modell findet oft den richtigen Arbeitspfad, produziert aber nicht durchgehend formal verlässliche Calls. Retry war nicht erforderlich, also liegt das Problem eher in punktueller Call-Validität als in systematischem MCP-Formatversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 59.17 der klare Schwachpunkt. Besonders bei HTTP Fetch & Extract, wo präzise Extraktion aus echtem Seiteninhalt verlangt wird, verliert das Modell an Genauigkeit. Es kann Ergebnisse zusammenführen, aber nicht stabil genug für Pipelines, in denen Eigennamen, Jahreszahlen oder Lizenzdetails unverändert übernommen werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Vorwissen beantwortet werden, halluziniert es nicht. Das ist positiv. Trotzdem bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als abgerufene Ergebnisse ausgibt, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Call erzwingt, bleibt GLM-5.1 auf der akzeptablen Seite. Es erfindet keinen Seiteninhalt und reagiert damit produktionstauglich auf offensichtliche Tool-Fehler. Der P2-Wert von 60 zeigt aber auch hier nur durchschnittliche Klarheit in der Fehlerkommunikation. Für robuste Systeme ist das ausreichend, für stark automatisierte Folgeschritte ohne menschliche Kontrolle nicht ideal.

**Betriebsprofil**

Total 325.02s. Call 1 6.27s. MCP-Latenz 2.78s. Call 2 45.12s. Langsam. Kosten pro Run: local. Preisblatt: $1.05/1M Input, $3.5/1M Output. Für die gezeigte Leistung ist die Tail-Latenz der kritische operative Nachteil.

**Fazit & Empfehlung**

Geeignet für überwachte Recherche- und Orchestrierungs-Pipelines, in denen das Modell Tools auswählen, Suchpfade aufspannen und mehrsprachige Ergebnisse zusammenziehen soll. Nicht geeignet für Compliance-, Extract-and-Trust- oder vollautomatische Fetch-Pipelines, in denen jedes Tool-Ergebnis formal korrekt aufgerufen und exakt verdichtet werden muss. Wer GLM-5.1 einsetzt, sollte strikte Tool-Call-Validierung, Antwortverifikation und enge Guardrails vor nachgelagerten Aktionen erzwingen.