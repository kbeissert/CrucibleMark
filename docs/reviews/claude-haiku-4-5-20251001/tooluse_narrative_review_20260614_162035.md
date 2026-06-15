**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:35


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthesetreue aber nicht stabil genug für faktenkritische Pipelines. Der kombinierte Befund ist nur moderat, obwohl die Tool-Calls valide waren.

**Tool-Execution-Profil**

Claude Haiku 4.5 verhält sich auf der Ausführungsebene brauchbar. Mit P1 86.67 produziert es valide MCP-konforme Tool-Calls und brauchte keinen Retry, was gegen ein Formatproblem spricht. Entscheidend ist aber die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne Hinweis die richtige Wahl zwischen Suche und direktem Abruf prüft, erreicht es 80. Das zeigt echte, aber nicht durchgehend sichere Tool-Intelligenz. Es erkennt den Bedarf für web_search oft, wirkt dabei jedoch nicht deterministisch.

Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Abruf misst, erreicht es ebenfalls 80. Das spricht für solide operative Kompetenz, aber nicht für präzise Steuerung unter schwachen Prompts. In einer MCP-Pipeline kann man ihm Tools übergeben. Man sollte die Tool-Auswahl jedoch durch Systemregeln, Tool-Beschreibungen und enge Erfolgskriterien absichern.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Schwäche. P2 52.50 ist für produktive Ergebnisnutzung zu niedrig. Das sieht man konsistent in EU License Research, HTTP Fetch & Extract, Web Search & Tool Selection und Multilingual Search & Synthesis, wo die Ausführung gelingt, die Verdichtung aber auf 35 bis 40 fällt. Das Modell holt Informationen, komprimiert sie jedoch nicht zuverlässig in eine belastbare, präzise Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, blieb es im verifizierten Inhaltsraum. P2 40 ist schwach, aber Halluzination wurde dort nicht erkannt. Gleichzeitig ist der globale Halluzinations-Flag ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparentes Verhalten bei einem fehlschlagenden Abruf prüft, reagiert Claude Haiku 4.5 akzeptabel. P2 80 und keine Halluzination trotz 404 bedeuten: Es ersetzt fehlenden Seiteninhalt nicht durch Erfindungen. Das ist produktionsreif.

**Betriebsprofil**

Call 1 5.43s, MCP-Latenz 1.35s, Call 2 3.35s, Total 60.75s. Operativ schnell auf Einzelaufrufebene, aber der Gesamtrun ist nicht kurz. Kosten pro Run: 0.034324 USD. Günstig bis moderat, gemessen an der nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für assistive MCP-Pipelines mit klarer Tool-Führung, begrenzter Antwortverantwortung und nachgelagerter Validierung, etwa Recherche-Vorstufen, Link-Sammlung, URL-Abruf und robuste Fehlerbehandlung. Nicht geeignet für Compliance-, Policy-, Extract-and-Summarize- oder multilingual verdichtende Workflows, in denen die Antwort selbst als verlässliches Endprodukt dient. Wenn Sie es einsetzen, dann als schneller Tool-Operator, nicht als letzte Syntheseinstanz.