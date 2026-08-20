**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:21:24


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Calls nicht durchgängig valide protokollkonform waren und die Synthesequalität für produktive Entscheidungsstrecken zu ungleich ausfällt.

**Tool-Execution-Profil**

Claude Sonnet 5 zeigt echte Werkzeugintelligenz statt starrem Musterverhalten. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den richtigen Zugriffspfad zuverlässig. Das spricht für brauchbare Orchestrierung in offenen MCP-Pipelines. Auch bei EU License Research und Multilingual Search & Synthesis setzt es die nötigen Schritte konsequent um.

Schwächer ist die Ausführung dort, wo das Modell eine Ziel-URL selbst herleiten muss. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines. Das ist kein Planungsfehler, sondern ein Präzisionsproblem im letzten Schritt. Kritischer ist, dass der Tool-Call insgesamt als nicht valide markiert wurde. Für Produktion heißt das: fachlich oft richtige Tool-Wahl, aber MCP-Integration nur mit strikter Schema-Validierung, Guardrails und gegebenenfalls einem Call-Sanitizer vor dem tatsächlichen Tool-Dispatch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Ordentlich, aber nicht auf dem Niveau, das man für belastbare Executive-Summaries oder Compliance-Auszüge blind freigeben sollte. Die starken 100 Punkte bei HTTP Fetch & Extract zeigen, dass es strukturierte Web-Inhalte sauber herausziehen kann. Dagegen fallen EU License Research und URL Construction & Fetch in der Verdichtung sichtbar ab, und bei Multilingual Search & Synthesis ist die deutschsprachige Zusammenführung der schwächste Punkt. Das Muster ist klar: gute Extraktion, wechselhafte Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell innerhalb der abgefragten Ergebnisse. Keine Halluzination wurde erkannt. Das ist ein Vertrauenssignal. Der P2-Wert von 60 zeigt aber, dass korrektes Recherchieren nicht automatisch in eine präzise, belastbare Endzusammenfassung übersetzt wird.

**Fehlerresilienz**

Bei Tool-Fehlern ist das Modell produktionstauglich. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt prüft, halluziniert es keinen Seiteninhalt und kommuniziert den Fehlschlag nachvollziehbar. Genau dieses Verhalten braucht eine Tool-Pipeline: sichtbarer Fehler statt erfundener Erfolg.

**Betriebsprofil**

Call 1: 2.48s. Call 2: 10.12s. MCP-Latenz: 0.89s. Total: 80.95s.  
Kosten/Run: local.  
Für die gezeigte Leistung: eher langsam im End-to-End-Run. Kosten hier nicht bewertbar.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-, Routing- und Tool-Auswahl-Pipelines, in denen ein nachgelagerter Validator Strukturfehler abfängt und ein Mensch oder Regelwerk die Schlussverdichtung prüft. Nicht geeignet als unkontrollierte Endinstanz für Compliance-Synthesen, mehrsprachige Entscheidungsnotizen oder Workflows, in denen ein formal invalider Tool-Call bereits ein Incident ist. Wer Claude Sonnet 5 einsetzt, sollte ihm die Werkzeuge geben, aber nicht das letzte Wort ohne Absicherung.