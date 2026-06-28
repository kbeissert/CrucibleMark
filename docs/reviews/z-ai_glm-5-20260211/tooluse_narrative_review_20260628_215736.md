**Deployment-Urteil**

> **Erstellt am:** 28.06.2026, 21:57:36


Bedingt deploy, weil die Tool-Ausführung stark ist, die Tool-Calls aber nicht durchgängig valide sind und die Synthesequalität für produktionskritische Auswertung zu inkonsistent bleibt.

**Tool-Execution-Profil**

GLM-5 zeigt echte Werkzeugintelligenz. Beim Web Search & Tool Selection-Test erkennt es ohne expliziten Hinweis, dass erst Suche statt direktem Fetch nötig ist, und handelt damit agentisch statt schematisch. Das ist ein starkes Signal für MCP-gestützte Pipelines mit unklarer Informationslage. Auch bei EU License Research arbeitet es sauber tool-first.

Schwächer ist die Präzision im Ausführen. Beim URL-Construction-Test, der prüft ob das Modell die Ziel-URL aus eigenem Wissen ableitet und dann korrekt fetched, ist die Richtung richtig, aber nicht deterministisch genug für harte Produktionspfade. Dazu passt der Befund, dass der Tool-Call insgesamt nicht durchgängig valide war. Das wirkt hier eher wie ein Ausführungs- und Formatproblem als wie ein Planungsdefizit. Retry war nicht nötig, also kein schwerer Protokollbruch, aber auch kein blind vertrauenswürdiger Call-Emitter.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. P2 von 60 zeigt sich konkret in den schwachen Verdichtungen bei EU License Research und Multilingual Search & Synthesis. Das Modell findet die Informationen oft, komprimiert sie aber nicht mit der Präzision, die Architekten für Compliance-, Policy- oder mehrsprachige Recherchepfade brauchen. Für einfache Extraktion ist es brauchbar. Für belastbare Ergebnisaufschreibung braucht es Nachkontrolle.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Vertrauensbefund. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, halluziniert es nicht. Der P2-Wert von 40 ist daher kein Sicherheitsalarm, sondern ein Verdichtungsproblem: Es bleibt näher an den Quellen, als es sie gut zusammenfasst.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit Tool-Fehlern statt erfundenem Ersatzinhalt misst, kommuniziert GLM-5 den Fehlschlag sauber und halluziniert keinen Seiteninhalt. Genau dieses Verhalten hält eine Tool-Pipeline vertrauensfähig, auch wenn ein externer Schritt ausfällt.

**Betriebsprofil**

Call 1: 3.29s. MCP-Latenz: 0.82s. Call 2: 43.93s. Total: 288.28s. Deutlich langsam, mit ausgeprägter Tail-Latenz. Kosten/Run: local. Preis laut Modellprofil niedrig, die Zeitkosten pro Run sind im Verhältnis zur gezeigten Syntheseleistung hoch.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, Suchsteuerung und transparenter Fehlerumgang wichtiger sind als perfekte Endverdichtung. Nicht geeignet als unbeaufsichtigter letzter Synthese-Layer für Compliance, Policy oder andere textkritische Entscheidungsstrecken. Wenn Sie GLM-5 einsetzen, dann als planendes und suchendes Modell mit nachgelagerter Validierung oder mit einem zweiten Modell für die abschließende Ergebnisverdichtung.