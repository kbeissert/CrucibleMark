**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:22:38


Bedingt deploy, weil GLM-5.2 trotz starker Tool-Wahl kein verlässliches End-to-End-Verhalten für MCP-Pipelines zeigt: der Combined-Score ist schwach, und der Tool-Call war nicht durchgehend valide.

**Tool-Execution-Profil**

GLM-5.2 zeigt echte Werkzeugintelligenz, aber keine deterministische Ausführungssicherheit. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erkennt das Modell den richtigen Zugriffspfad sauber und erreicht volle Tool-Selection-Leistung. Das spricht gegen bloßes Schablonenverhalten.

Der Gegenpol ist der Test URL Construction & Fetch, der misst, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch ausführt. Dort fällt es vollständig aus. Das ist für produktive Pipelines kritisch, weil viele Agent-Flows nicht nur das richtige Tool, sondern auch präzise Parameterbildung verlangen. MCP-Konformität wirkt damit situativ, nicht robust. Es versteht, wann gesucht werden muss. Es scheitert, wenn es Zieladressen selbst konstruieren und den Call exakt formen soll.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. Die P2-Leistung ist insgesamt schwach, obwohl einzelne Aufgaben wie HTTP Fetch & Extract und Web Search & Tool Selection brauchbare Verdichtung zeigen. Sobald die Aufgabe mehrsprachige Recherche oder fehleranfällige Ableitung verlangt, bricht die Synthesequalität deutlich ein. Für Architekturen, in denen das Modell Tool-Output in entscheidungsreife Kurzfassungen überführen soll, ist das zu inkonsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem vortrainierten Wissen beantwortet werden, bleibt GLM-5.2 innerhalb des Tool-Rahmens. Es wurde keine Halluzination erkannt. Das ist das wichtigste Vertrauenssignal in diesem Lauf und verhindert ein härteres Negativurteil.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlgeschlagenen Tool-Call prüft, halluziniert GLM-5.2 keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Antwortqualität bleibt aber schwach: Es kommuniziert den Fehlschlag nicht souverän genug, um daraus einen sauberen Fallback-Pfad oder einen klaren Operator-Hinweis zu machen. Für Produktion ist das akzeptabel, aber nur mit externer Fehlerbehandlung im Orchestrator.

**Betriebsprofil**

Total 232.50s pro Run. Davon ein zweiter Modell-Call mit 55.52s und 0.92s MCP-Latenz. Langsam für die erreichte Qualität. Kosten lokal. Wirtschaftlich nur dann vertretbar, wenn lokale Inferenz strategisch wichtiger ist als Durchsatz.

**Fazit & Empfehlung**

Geeignet für überwachte Recherche- und Orchestrationspipelines, in denen das Modell Tool-Typen auswählen darf, aber URL-Bildung, Parameterhärtung und Fehlerpfade vom System erzwungen werden. Nicht geeignet als autonomer Tool-Agent mit freier Request-Konstruktion oder für mehrsprachige Retrieval-Synthese ohne starke Guardrails. Wer GLM-5.2 einsetzt, sollte es als planendes Frontend mit eng geführter Tool-Schicht betreiben, nicht als frei handelnden MCP-Executor.