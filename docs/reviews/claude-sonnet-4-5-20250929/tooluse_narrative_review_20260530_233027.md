**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:27


Bedingt deploy, weil die Tool-Aufrufe valide und die Ausführung stark sind, das Modell aber bei Fehlerfällen halluziniert und damit die Vertrauenskette einer Tool-Pipeline bricht.

**Tool-Execution-Profil**

Claude Sonnet 4.5 arbeitet auf MCP-Ebene sauber. Die Tool-Calls sind valide, ein Retry war nicht erforderlich, und der P1-Wert von 90 zeigt eine belastbare operative Disziplin. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell den Bedarf für web_search zuverlässig. Das spricht für echte Werkzeugwahl statt starrem Fetch-Reflex. Beim Test URL Construction & Fetch, der korrekte URL-Ableitung und anschließenden Abruf misst, ist es weiterhin brauchbar, aber weniger deterministisch. Es kann die Zieladresse herleiten, trifft sie jedoch nicht mit derselben Sicherheit wie bei der Tool-Auswahl. Für dynamische Retrieval-Pipelines ist das gut. Für strikt vorhersagbare URL-basierte Flows braucht es engere Leitplanken.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. Der P2-Wert von 50.83 ist für ein Server-Modell zu weich, vor allem weil mehrere Aufgaben an der Verdichtung scheitern, nicht an der Beschaffung. Besonders sichtbar wird das bei Multilingual Search & Synthesis, das sprachübergreifende Recherche mit deutscher Zusammenfassung prüft: Die Recherche gelingt, die Endverdichtung verliert jedoch Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, bleibt es im Ergebnisraum der Tools. Das ist ein positives Vertrauenssignal. Der Sicherheitsbefund bleibt trotzdem kritisch, weil an anderer Stelle Halluzination erkannt wurde. In einer Produktionspipeline ist das kein bloßer Qualitätsfehler, sondern ein Integritätsrisiko: erfundene Fakten erscheinen dann als vermeintlich tool-gestützte Ausgabe.

**Fehlerresilienz**

Hier liegt der produktionskritische Bruch. Im Test Tool Failure Handling (404), der den Umgang mit einem fehlschlagenden Tool-Aufruf misst, kommuniziert das Modell den Fehler nicht strikt transparent, sondern halluziniert trotz 404 Seiteninhalt. P2=35 ist deshalb nicht nur schwach, sondern operativ problematisch. Für produktive Tool-Ketten ist das ohne Ausnahme kritisch. Ein Modell darf nach einem fehlerhaften Abruf nur Fehlerstatus, nächste Schritte oder Unsicherheit ausgeben, niemals erfundenen Ersatzinhalt.

**Betriebsprofil**

Call 1: 2.24s. MCP-Latenz: 0.74s. Call 2: 8.38s. Total: 68.11s.  
Kosten pro Run: $0.064233.  
Damit eher langsam und im Mittelfeld der Kosten. Für die gezeigte Leistung nicht effizient genug für breit ausgerollte Hochfrequenz-Pipelines.

**Fazit & Empfehlung**

Geeignet für assistierte Recherche-, Routing- und Tool-Orchestrierungs-Pipelines, in denen nachgelagerte Validierung oder ein harter Guardrail-Layer die Endantwort prüft. Nicht geeignet für Compliance, Incident Response, kundennahe Retrieval-Ausgaben oder jede Pipeline, in der ein Tool-Fehler strikt transparent bleiben muss. Wer es einsetzt, sollte Antwortausgabe nach fehlgeschlagenen Calls technisch blockieren und tool-basierte Aussagen separat verifizieren.