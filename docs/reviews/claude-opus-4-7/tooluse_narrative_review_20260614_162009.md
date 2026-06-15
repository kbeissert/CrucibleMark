**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:09


Bedingt deploy, weil die Tool-Nutzung zuverlässig und protokollkonform ist, die Synthesequalität aber für produktive Wissens-Pipelines noch zu ungleichmäßig ausfällt.

**Tool-Execution-Profil**

Claude Opus 4.7 verhält sich auf der Werkzeugschicht belastbar. Die Tool-Calls waren valide, ein Retry war nicht nötig, und es zeigt keine Anzeichen für MCP-Formatinstabilität. Das wichtigste Signal ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheidet, wählt es das richtige Werkzeug sicher. Das spricht gegen starres Musterverhalten und für echte Situationsbewertung.

Schwächer ist die Präzision beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen lässt. Hier reicht die Leistung für brauchbare Ausführung, aber nicht für vollständig deterministische Pipelines. In klaren Such- und Abrufketten ist das Modell stark. In Flows, in denen es Zieladressen selbst rekonstruieren muss, sollten Guardrails oder Validierungsschritte davorliegen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht konstant auf Frontier-Niveau. Stark ist es bei HTTP Fetch & Extract sowie bei Tool Failure Handling (404), wo es abgerufene Inhalte sauber zusammenfasst. Deutlich schwächer ist Multilingual Search & Synthesis, wo die Verdichtung über Sprachgrenzen hinweg sichtbar an Präzision verliert. Das ist kein Ausführungsfehler, sondern ein Qualitätsrisiko für internationale Recherche- oder Policy-Pipelines.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Befund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es verifizierbar am beschafften Material. Der P2-Wert von 60 zeigt, dass die Verdichtung nicht sauber genug war. Entscheidend ist aber: keine Halluzination, kein verdecktes Zurückfallen auf Altwissen.

**Fehlerresilienz**

Bei scheiternden Tool-Aufrufen ist das Modell produktionstauglich. Im Test Tool Failure Handling (404), der auf transparente Kommunikation statt erfundenen Ersatzinhalt prüft, benennt es den Fehler offen und halluziniert keinen Seiteninhalt. Genau dieses Verhalten ist in produktiven Pipelines akzeptabel.

**Betriebsprofil**

Total 112.66s. Einzelaufrufe 2.45s und 15.04s, MCP-Latenz 1.29s. Langsam für interaktive Flows. Kosten pro Run 0.191580 USD. Teuer, gemessen an einer nur guten statt sehr guten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit mehreren Tool-Schritten, hohem Sicherheitsanspruch gegen Halluzination und Toleranz für Laufzeit und Kosten. Besonders passend für Recherche, Fetch-gestützte Analyse und Workflows, in denen Fehler transparent abgefangen werden müssen. Nicht die erste Wahl für multilingual verdichtende Wissenspipelines, kostenempfindliche Massenrouten oder strikt deterministische Flows mit selbst konstruierter URL-Logik ohne zusätzliche Validierung.