**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:36:28


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 74.50 und nicht validem Tool-Call für unbeaufsichtigte Hochvertrauens-Pipelines nicht stabil genug wirkt.

**Tool-Execution-Profil**

Command A zeigt klare Werkzeugintelligenz statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis Suche statt direktem Fetch gewählt wird, erkennt das Modell den passenden Zugriffspfad sicher und erzielt P1 100. Das spricht für brauchbare Orchestrierungsfähigkeit in MCP-gestützten Abläufen. Beim Test URL Construction & Fetch, der die eigenständige Herleitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für Pipelines, die präzise URL-Bildung ohne Korrekturschritt erwarten.

Der Schwachpunkt ist operativ wichtiger als der Mittelwert vermuten lässt: Tool-Call valide steht auf False. Das bedeutet nicht, dass das Modell Werkzeuge nicht versteht. Es bedeutet, dass die Protokolltreue im Run nicht durchgängig verlässlich war. Da kein Retry nötig war, liegt der Befund eher bei einzelner Call-Qualität als bei systematischem Formatversagen. Für produktive Nutzung braucht es deshalb einen Executor, der Parameter strikt validiert und fehlerhafte Calls abfängt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 60 ist der eigentliche Grenzwert dieses Modells. Bei HTTP Fetch & Extract arbeitet es sauber, und bei URL Construction & Fetch erreicht es sogar P2 100. Sobald die Aufgabe aber stärker auf Verdichtung, Einordnung und sprachübergreifende Zusammenführung zielt, fällt die Qualität sichtbar ab. EU License Research mit P2 20 und Multilingual Search & Synthesis mit P2 40 zeigen, dass das Modell Ergebnisse zwar beschafft, aber nicht konstant präzise in belastbare Aussagen überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das entscheidende Vertrauenssignal. Der sehr niedrige P2-Wert zeigt aber, dass Nicht-Halluzinieren hier nicht mit guter inhaltlicher Verdichtung gleichzusetzen ist.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Aufruf gegen erfundenen Seiteninhalt prüft, bleibt Command A auf der sicheren Seite. Es halluziniert trotz Fehler keinen Ersatzinhalt. P2 60 zeigt keine elegante Fehlerkommunikation, aber akzeptables Produktionsverhalten: lieber unvollständig als erfunden.

**Betriebsprofil**

Total 40.00s. Modellaufrufe 0.84s und 4.88s. MCP-Latenz 0.94s. Für die gezeigte Leistung eher langsam. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit starker Tool-Governance, insbesondere Recherche, Suchrouting und strukturierte Fetch-Aufgaben mit nachgelagerter Validierung. Nicht geeignet als alleinige Instanz für Compliance, Policy-Auslegung oder mehrsprachige Synthese, wenn die textliche Endantwort ohne menschliche oder regelbasierte Kontrolle direkt weiterverarbeitet wird. Deployen, wenn ein strikter Tool-Validator, Response-Checks und ein konservativer Fallback für schwache Verdichtung vorhanden sind.