**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:16:59


Bedingt deploy: Das Modell trifft Tool-Entscheidungen oft richtig, ist aber für produktive MCP-Pipelines ohne Guardrails nicht vertrauenswürdig genug, weil Halluzination erkannt wurde, der Tool-Call nicht durchgängig valide war und die Gesamtausbeute nur moderat bleibt.

**Tool-Execution-Profil**

Kimi K2.7 Code zeigt echte Werkzeugintelligenz statt reinem Schema-Fahren. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt es den Bedarf an web_search sehr sicher. Das spricht für brauchbare Orchestrierung in offenen Recherchepfaden. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, ist es weniger präzise. P1 80 ist brauchbar, aber für deterministische Pipelines nicht stark genug. Kritischer ist, dass Tool-Call valide insgesamt false steht. Damit ist das Modell nicht MCP-sicher im engen Sinne. Es versteht den Workflow, produziert aber nicht konstant protokollsaubere Ausführung. Dass kein Retry nötig war, spricht eher gegen ein reines Formatproblem und eher für inkonsistente Ausführung im Erstversuch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 70 wirkt auf den ersten Blick tragbar, aber die Asset-Streuung ist für Produktionsbetrieb zu groß. HTTP Fetch & Extract fällt bei der Verdichtung deutlich ab, und Multilingual Search & Synthesis sowie EU License Research landen in der Ergebnisverdichtung faktisch bei null. Das Modell kann also Tools benutzen, verliert aber bei der Überführung in belastbare Endaussagen an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Signal ist negativ, auch ohne formale Halluzination im Einzelfall. Beim Test EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus parametischem Vorwissen beantwortet werden, liefert P2 0. Das ist ein Vertrauensproblem. Zusätzlich ist Halluzination global erkannt worden. In einer Tool-Pipeline ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Das Modell kann erfundene oder nicht ausreichend belegte Aussagen als Tool-Ergebnisrahmen ausgeben.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert das Modell akzeptabel. Es kommuniziert den Fehler im Wesentlichen offen und erfindet keinen Seiteninhalt. P2 80 und keine Halluzination trotz 404 sind für Produktion ein positives Signal. Auf Infrastrukturebene scheitert es also nicht reflexhaft in Ersatzfakten.

**Betriebsprofil**

Total 107.33s pro Run. Langsam. Einzelaufrufe 4.03s und 12.72s, MCP-Latenz 1.13s. Kosten/Run local. Preisniveau des Modells: $0.67 pro 1M Input, $3.4 pro 1M Output. Für die gezeigte Zuverlässigkeit ist das Betriebsprofil eher schwer als effizient.

**Fazit & Empfehlung**

Geeignet für interne Engineering-Assistenz mit nachgelagerter Validierung, besonders dort, wo Tool-Auswahl wichtiger ist als exakte Endverdichtung. Nicht geeignet für Compliance-, Recherche- oder Freigabe-Pipelines, in denen Tool-Ergebnisse unverfälscht zusammengeführt werden müssen. Wenn Sie es einsetzen, dann nur mit strikter Tool-Call-Validierung, Quellennachweis-Pflicht pro Aussage und einer zweiten Instanz zur Ergebnisprüfung vor der Ausgabe.