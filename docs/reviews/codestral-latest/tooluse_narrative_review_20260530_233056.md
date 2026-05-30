**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:56


Bedingt deploy, weil Codestral valide Tool-Calls erzeugt und das MCP-Protokoll sauber bedient, aber die Synthesetreue mit Combined 64.96 nur für eng geführte Pipelines belastbar ist.

**Tool-Execution-Profil**

Die operative Seite ist solide. P1 liegt bei 83.33, der Tool-Call war valide und es brauchte keinen Retry. Das spricht gegen ein Protokoll- oder Formatproblem und für verlässliche Ausführung innerhalb einer MCP-gestützten Kette. Besonders stark ist es beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen Suche und direktem Abruf prüft: P1 100 zeigt echte Werkzeugwahl statt reinem Standardmuster. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Fetch-first-Pipelines. Insgesamt wirkt Codestral nicht blind tool-hörig. Es erkennt, wann Suche nötig ist. Es ist aber präziser im Aufruf als in der nachgelagerten Verarbeitung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 47.50. Die größten Schwächen liegen in EU License Research mit P2 20, in HTTP Fetch & Extract mit P2 35 und besonders in Multilingual Search & Synthesis mit P2 15. Das Modell holt also Informationen oft korrekt ein, komprimiert sie aber zu unzuverlässig, sobald mehrere Fakten, Sprachwechsel oder Compliance-nahe Details zusammengeführt werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal gemischt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, wurde keine Halluzination erkannt. Das ist wichtig. Gleichzeitig zeigt der Verifikationszustand B1 bei P2 20, dass es den Tool-Inhalt nicht vertrauenswürdig genug in eine belastbare Aussage überführt. Da insgesamt eine Halluzination erkannt wurde, ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die ganze Tool-Infrastruktur ihre Beweiskraft.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt prüft, erreichte Codestral P2 80 und halluzinierte keinen Seiteninhalt trotz Fehler. Das ist der richtige Ausfallmodus für produktive Systeme: lieber offen scheitern als scheinbar erfolgreich fabrizieren.

**Souveränitätsprofil**

Lokal betreibbar und operativ konkurrenzfähig, aber nicht fleet-stark. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Für souveräne Entwicklungs- und Assistenzumgebungen ist das tragfähig. Für wissenskritische Produktionsketten bleibt der Abstand relevant.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit klaren Guardrails, vor allem in Coding-, Retrieval- und URL-/Search-gesteuerten Workflows, bei denen ein nachgelagerter Validator die Endaussage prüft. Nicht geeignet für Compliance-, Research- oder mehrsprachige Synthese-Pipelines, in denen das Modell Tool-Ergebnisse eigenständig verdichten und als verlässliche Tatsachen ausgeben soll. Wenn Sie Codestral einsetzen, dann als ausführendes Tool-Modell mit enger Ergebnisprüfung, nicht als letzte Instanz für inhaltliche Wahrheit.