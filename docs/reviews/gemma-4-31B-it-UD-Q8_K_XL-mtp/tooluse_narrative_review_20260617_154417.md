**Deployment-Urteil**

> **Erstellt am:** 17.06.2026, 15:44:17


Bedingt deploy, weil die Tool-Nutzung oft funktional ist, aber die MCP-Ausführung nicht durchgehend valide bleibt und die Synthesetreue für verlässliche Produktionspipelines zu schwach ausfällt.

**Tool-Execution-Profil**

Gemma 4 31B Instruct zeigt echte Tool-Orientierung, nicht bloß starres Fetch-Verhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht für situationsbezogene Werkzeugwahl. Auch Multilingual Search & Synthesis und EU License Research liefen auf P1 stark.

Schwächer ist die operative Präzision. Beim URL-Construction-Test, der die eigenständige Ableitung einer Zieladresse und den anschließenden Fetch prüft, ist die Richtung korrekt, aber nicht deterministisch genug für robuste Pipelines. Kritischer ist, dass der Tool-Call insgesamt nicht valide war. Das ist kein reines Qualitätsdetail, sondern ein Integrationsproblem auf Protokollebene. Für MCP-Umgebungen heißt das: vor den produktiven Einsatz gehört ein strikter Wrapper mit Schema-Validierung, Argument-Normalisierung und Abbruch bei ungültigen Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung bleibt deutlich hinter der Tool-Ausführung zurück. In HTTP Fetch & Extract, URL Construction & Fetch und Multilingual Search & Synthesis fasst es Ergebnisse brauchbar zusammen, aber nicht präzise genug für Workflows, in denen exakte Fakten, Bedingungen oder Versionsstände erhalten bleiben müssen. Das Modell findet Informationen öfter, als es sie sauber in eine belastbare Antwort überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, gab es keine erkannte Halluzination. Das ist das wichtigste Entlastungssignal dieses Laufs. Gleichzeitig ist P2 dort nur 40. Das Modell erfindet also nicht offen, verdichtet aber zu unscharf, um in Compliance-nahen Pfaden ohne Nachkontrolle Vertrauen zu tragen.

**Fehlerresilienz**

Beim 404-Test, der transparentes Fehlverhalten statt erfundenem Seiteninhalt verlangt, reagiert das Modell akzeptabel. Es halluziniert keinen Ersatzinhalt. P2 60 zeigt aber, dass die Fehlerkommunikation eher ausreichend als vorbildlich ist. Für Produktion ist das tragbar, solange der Orchestrator Fehlerpfade selbst strikt behandelt und keine implizite Weiterverarbeitung aus Modelltext ableitet.

**Souveränitätsprofil**

Lokal betreibbar und mit 68.33 Combined leicht über dem Fleet-Ø von 67.80. Der Sovereignty Gap ist n/a-Punkte unter dem Fleet-Ø von 67.80.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines mit menschlicher Aufsicht oder programmatischer Zweitprüfung, vor allem für Recherche, Suchschritt-Auswahl und mehrsprachige Vorarbeit. Nicht geeignet als ungeprüfte Endinstanz für Compliance, Vertragslogik, Lizenzbewertung oder andere Pfade, in denen die Antwort den Tool-Befund exakt und protokolltreu repräsentieren muss. Wer es einsetzt, sollte die Stärke in der Werkzeugwahl nutzen und die Schwäche in Call-Validität und Verdichtung durch harte Guardrails ausgleichen.