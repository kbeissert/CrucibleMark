**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:21:37


Bedingt deploy, weil die Tool-Nutzung verlässlich wirkt und keine Halluzination erkannt wurde, die Synthesequalität mit Combined 78.80 aber nicht stabil genug für hochkritische Ergebnisverdichtung ist.

**Tool-Execution-Profil**

Qwen 3.5 397B A17B verhält sich auf der Ausführungsebene produktionsnah. Tool-Calls waren valide, MCP-konform und ohne Retry. Das ist der wichtigste Basisschutz für eine Tool-Pipeline. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt das Modell die passende Werkzeugklasse sicher. Das spricht gegen ein starres Call-Muster und für echte Werkzeugwahl. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines mit enger Fehlertoleranz. Die Ausführung ist damit stark, aber nicht blind vertrauenswürdig, wenn der Pfad aus Modellwissen abgeleitet werden muss.

Wichtig zur Einordnung: Das Modell ist primär ein Vision-Language-System. Die hier sichtbare Text-Tool-Kompetenz ist deshalb belastbar, bildet aber nicht seine volle Produktfläche ab.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht auf Frontier-Niveau. P2 von 68 zeigt, dass es gefundene Informationen oft korrekt zusammenführt, dabei aber an Präzision verliert. Das sieht man besonders im Test Multilingual Search & Synthesis, der sprachübergreifende Recherche und deutsche Zusammenfassung prüft: Die Suche gelingt, die Verdichtung bleibt deutlich hinter der Ausführung zurück.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es im Honeypot EU License Research keine Daten. Positiv ist nur das indirekte Signal: In den vorliegenden Läufen wurde keine Halluzination erkannt. Für Compliance- oder Lizenzpipelines ist das hilfreich, aber kein Ersatz für einen bestandenen Honeypot.

**Fehlerresilienz**

Beim 404-Test, der prüft, ob ein fehlgeschlagener Tool-Call transparent behandelt wird oder erfundener Seiteninhalt erscheint, bleibt das Modell auf der sicheren Seite. Es halluziniert trotz Fehler nicht. Das ist für Produktion akzeptabel. Die P2 von 60 zeigt allerdings, dass die Fehlerkommunikation funktional ist, aber nicht immer optimal verdichtet oder geführt wird.

**Betriebsprofil**

Total 190.54s pro Run. Call 1: 3.13s. MCP-Latenz: 0.79s. Call 2: 34.19s. Langsam. Kosten pro Run: 0.004944. Günstig bis sehr günstig für diese Größenklasse. Preis-Leistung ist gut, Latenz bleibt der operative Engpass.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen saubere Tool-Ausführung wichtiger ist als perfekte Endverdichtung: Recherche-Agenten, Discovery-Workflows, multimodale Vorstufen und assistierte Analysten-Tools. Nicht die erste Wahl für Compliance, mehrsprachige Executive Summaries oder andere Pfade, in denen die Antwort selbst das Produkt ist. Wenn Sie es einsetzen, dann mit nachgelagerter Validierung der Zusammenfassung und klaren Guards für URL-Ableitung und finale Nutzertexte.