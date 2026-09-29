**Deployment-Urteil**

> **Erstellt am:** 26.09.2026, 21:54:13


Bedingt deploy, weil die Tool-Nutzung operativ oft funktioniert, das Modell aber mit erkannter Halluzination und ungültigem Tool-Call kein hinreichend verlässliches Vertrauensprofil für unüberwachte MCP-Pipelines hat.

**Tool-Execution-Profil**

Laguna S 2.1 zeigt echte Werkzeugwahl statt reinem Musterfolgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr sicher. Das spricht für brauchbare Planung in offenen Retrieval-Flows. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug. Die Lücke zwischen sehr starker Tool-Selektion und nur solider URL-Konstruktion zeigt: Das Modell versteht den nächsten Arbeitsschritt oft richtig, produziert aber nicht immer protokollsaubere Ausführung. Das wird durch den Befund tool_call_valid=false bestätigt. Retry war nicht erforderlich, also liegt das Problem eher in der Erst-Ausführung als in einem reinen Formatfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung ist mit 33.33 der klare Engpass. Besonders HTTP Fetch & Extract, das präzise Fakten aus echtem Seiteninhalt ziehen soll, bricht auf 15 ein. Auch bei Multilingual Search & Synthesis bleibt die Verdichtung trotz gelungener Recherche deutlich hinter Produktionsanforderungen zurück. Das Modell findet oft Material, komprimiert es aber nicht belastbar in eine saubere Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nur eingeschränkt vertrauenswürdig. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert es zwar nicht offen, bleibt aber mit P2=20 inhaltlich zu schwach, um als verlässliche Compliance-Synthese zu gelten. Zusätzlich ist global eine Halluzination erkannt worden. Das ist kein Schönheitsfehler, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, unterminiert es die gesamte Pipeline.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Call misst, kommuniziert Laguna S 2.1 den Fehler sauber und erfindet keinen Seiteninhalt. Das ist die Mindestanforderung für robuste Tool-Pipelines, und hier erfüllt das Modell sie.

**Betriebsprofil**

Call 1: 4.85s. Call 2: 31.33s. MCP-Latenz: 0.80s. Total: 221.90s.  
Langsam für die erzielte Antwortqualität.  
Kosten/Run: local. Günstig im Betrieb, aber die Zeitkosten sind hoch.

**Fazit & Empfehlung**

Geeignet für assistierte Agentenläufe mit menschlicher Abnahme, explorative Web-Recherche und Workflows, in denen Tool-Auswahl wichtiger ist als die letzte Synthese. Nicht geeignet für Compliance-, Policy-, oder Executive-Summary-Pipelines, in denen die Antwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann nur mit harter Antwortvalidierung, Tool-Call-Schema-Prüfung und einem nachgelagerten Verifier für jede verdichtete Aussage.