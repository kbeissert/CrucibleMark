**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:59


Bedingt deploy, weil Grok 4 Fast valide Tool-Calls erzeugt und nicht halluziniert, aber die Synthesetreue mit Combined 72.50 und besonders P2 60.00 für vertrauensabhängige Pipelines zu inkonsistent bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Es produziert valide MCP-konforme Aufrufe, brauchte keinen Retry und zeigt im Benchmark keine Protokollbrüche. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis das richtige Werkzeug gewählt wird, traf es die Entscheidung sauber und erreichte volle Ausführungssicherheit. Das spricht gegen ein rein starres Muster und für brauchbare Werkzeugwahl im laufenden Betrieb.

Weniger präzise ist es beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst. Hier ist die Leistung solide, aber nicht deterministisch genug für fragile Pipelines mit strengem URL-Schema. Praktisch heißt das: stark bei Such- und Discovery-Schritten, vorsichtiger Einsatz bei Konstruktion aus implizitem Wissen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. Die Ausführung ist meist korrekt, aber die Verdichtung bleibt oft zu flach oder verliert entscheidende Details. Das sieht man besonders bei EU License Research mit P2 40 und bei Multilingual Search & Synthesis mit P2 20. Für produktive Pipelines ist das relevant, weil nicht der Call selbst, sondern die letzte textuelle Verdichtung an nachgelagerte Systeme oder Entscheider weitergereicht wird.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, blieb es auf der sicheren Seite. Content-Verification-State A und keine erkannte Halluzination sind hier das wichtige Signal. Das Modell verdichtet schwach, aber es erfindet in diesem Test keine aktuellen Lizenzfakten.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der prüft, ob das Modell bei einem fehlgeschlagenen Abruf transparent bleibt statt Seiteninhalt zu erfinden, reagierte es sauber. P2 80 bei ausbleibender Halluzination bedeutet: Fehler werden kommuniziert, nicht kaschiert. Das ist für Tool-Pipelines wichtiger als rhetorische Glätte.

**Betriebsprofil**

Calls: 2.00s und 1.99s. MCP-Latenz: 1.12s. Total pro Run: 30.67s. Schnell im Modell, aber der End-to-End-Run bleibt deutlich länger als die Einzelaufrufe vermuten lassen. Kosten pro Run: 0.018736. Für Frontier-Betrieb günstig bis moderat, gemessen an der Leistung.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen zuverlässige Tool-Ausführung, Suchentscheidungen und transparente Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Gut passend für Retrieval, Web-Recherche, Vorstrukturierung und menschlich überprüfte Copilot-Workflows. Nicht die erste Wahl für Compliance-Zusammenfassungen, mehrsprachige Synthese oder jede Pipeline, in der die finale Antwort selbst als belastbares Arbeitsprodukt gelten muss.