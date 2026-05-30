**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:30


Nicht deploy. Der Befund ist hier nicht nur schwach, sondern unbrauchbar für eine MCP-gestützte Tool-Pipeline, weil weder valide Tool-Calls noch belastbare Teil-Scores vorliegen und der Combined Score bei 0.00 liegt.

**Tool-Execution-Profil**

Für den produktiven Einsatz fehlt der zentrale Nachweis, dass qwen3.7-max Tools korrekt auswählt und MCP-konforme Aufrufe erzeugt. `tool_call_valid=false` ist dabei das entscheidende Signal. Es sagt nicht nur, dass einzelne Ergebnisse fehlen. Es sagt, dass die Infrastruktur diesem Modell aktuell keine verlässliche Werkzeugausführung anvertrauen kann.

Die beiden Kernprüfungen zur Werkzeugwahl bleiben unbeantwortet. Beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne expliziten Hinweis erkennt, dass eine Websuche statt eines direkten Fetch nötig ist, gibt es keinen verwertbaren P1-Befund. Dasselbe gilt für URL Construction & Fetch, also die Fähigkeit, eine Ziel-URL korrekt herzuleiten und anschließend sauber abzurufen. Damit lässt sich weder adaptive Tool-Intelligenz noch ein deterministisches Muster erkennen. Es fehlt schlicht Evidenz. `retry_required=false` entlastet das Modell nicht. Ohne valide Calls ist das kein Formatproblem mit einmaliger Korrektur, sondern ein grundlegendes Ausführungsdefizit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine belastbare Aussage. Für keines der sechs Assets liegt ein P2-Wert vor. Damit ist offen, ob das Modell extrahierte Inhalte präzise zusammenfasst, strukturiert priorisiert und ohne semantische Drift in eine Antwort überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal vorsichtig positiv, aber schwach abgesichert. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen statt aus Trainingswissen, wurde keine Halluzination erkannt. Das ist ein Mindestkriterium für Vertrauen, ersetzt aber keinen Nachweis sauberer Tool-Nutzung oder verifizierter Synthese.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf misst, wurde kein Seiteninhalt halluziniert. Das ist produktionsseitig wichtig. Ein Modell, das bei Fehlern nichts erfindet, beschädigt die Pipeline nicht zusätzlich. Dennoch bleibt der Befund begrenzt, weil positive Fehlerkommunikation allein kein Ersatz für funktionierende Tool-Ausführung ist.

**Betriebsprofil**

Latenz: n/a. Kosten pro Run: local. Im Verhältnis zur Leistung nicht bewertbar, weil keine verwertbaren Laufzeit- oder Qualitätssignale vorliegen.

**Fazit & Empfehlung**

Nicht für produktive Agenten, Rechercheketten, Compliance-Flows oder andere Tool-gebundene Pipelines freigeben. Allenfalls als isoliertes Textmodell in nicht-kritischen Umgebungen testen, in denen keine echte MCP-Orchestrierung erforderlich ist. Vor einer erneuten Bewertung braucht es zuerst einen sauberen Nachweis valider Tool-Calls, belastbarer Ergebnisse in Web Search & Tool Selection sowie URL Construction & Fetch und verwertbarer Synthese über mehrere Assets.