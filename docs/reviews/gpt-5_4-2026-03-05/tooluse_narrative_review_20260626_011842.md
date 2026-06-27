**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:42


Bedingt deploy: GPT-5.4 zeigt brauchbare Tool-Nutzung ohne erkannte Halluzination, aber der invalide Tool-Call und der nur moderate Gesamtertrag machen es für produktive MCP-Pipelines nur unter enger Guardrail-Führung vertretbar.

**Tool-Execution-Profil**

Die Tool-Ausführung ist uneinheitlich. Positiv ist der HTTP Fetch & Extract-Test, der präzise strukturierte Fakten aus Fetch-Content zieht, sowie der URL-Construction-Test, bei dem das Modell die Ziel-URL meist korrekt ableitet und den Fetch solide ausführt. Negativ fällt die Werkzeugwahl aus: Im Web Search & Tool Selection-Test erkennt es ohne expliziten Hinweis oft nicht zuverlässig, dass erst eine Suche und nicht direkt ein Fetch nötig ist. Das spricht nicht für belastbare Tool-Intelligenz, sondern eher für ein Muster, möglichst schnell auf bekannte URL- oder Fetch-Pfade zu springen. Für dynamische Pipelines ist das riskant, weil der erste Schritt oft die eigentliche Entscheidung ist. Dass der Tool-Call insgesamt als nicht valide gewertet wurde, verschärft diesen Befund. Immerhin war kein Retry nötig, also eher ein Auswahl- oder Protokollsauberkeitsproblem als ein kompletter Verständnisabbruch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. Die Synthesis bleibt insgesamt brauchbar, aber nicht präzise genug für Workflows, in denen mehrere Tool-Antworten zu einer belastbaren Entscheidungslage zusammengeführt werden müssen. Die Spannweite der Assets ist dafür zu groß: sehr stark bei Multilingual Search & Synthesis, deutlich schwach bei EU License Research.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, ist keine Halluzination erkannt worden. Das ist wichtig. Der sehr niedrige P2-Wert zeigt aber trotzdem, dass das Modell die Aufgabe nicht verlässlich in toolgebundene, entscheidungsfeste Aussagen überführt. Für Compliance-nahe Recherchen reicht das nicht.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich GPT-5.4 akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Seiteninhalt prüft, halluziniert es keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Fehlerbehandlung ist damit verwendbar, auch wenn die Kommunikation noch klarer und operativer sein dürfte.

**Betriebsprofil**

Total 58.59s. Call 1: 4.18s. MCP-Latenz: 0.39s. Call 2: 5.19s. Für die gezeigte Leistung langsam. Preis: $2.5/1M Input, $15.0/1M Output. Für ein Frontier-Modell nicht extrem, im Verhältnis zur Tool-Zuverlässigkeit aber teuer.

**Fazit & Empfehlung**

Geeignet für assistive Recherche-Pipelines mit menschlicher Abnahme, für multilingualen Web-Kontext und für Fetch-lastige Abläufe, in denen die Ziel-URL oft schon bekannt oder gut ableitbar ist. Nicht geeignet für autonome MCP-Orchestrierung, Compliance-Recherche, dynamische Tool-Auswahl und alle Pipelines, in denen der erste Tool-Schritt deterministisch richtig sein muss. Wenn Sie es einsetzen, dann mit hartem Tool-Routing, Call-Validierung und einer Schicht, die Synthesis gegen Rohquellen zurückprüft.