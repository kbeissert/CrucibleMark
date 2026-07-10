**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:06:42


Bedingt deploy, weil die Tool-Nutzung oft zielführend ist, aber valide Tool-Calls nicht konsistent gelingen und die Synthesequalität für produktive Entscheidungsstrecken zu schwach bleibt.

**Tool-Execution-Profil**

Gemma 4 26B-A4B Instruct zeigt echte Werkzeugintelligenz bei der Auswahl. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr sicher. Das spricht gegen ein starres Muster und für brauchbare situative Planung. Auch beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließenden Fetch misst, arbeitet es überwiegend korrekt, aber nicht präzise genug für deterministische Pipelines.

Der Hauptvorbehalt ist operativ: Tool-Call valide steht insgesamt auf false. Das heißt nicht, dass das Modell Tools grundsätzlich nicht versteht. Es heißt, dass die Protokolltreue im MCP-Kontext nicht zuverlässig genug ist, um unbeaufsichtigt jede Übergabe zu tragen. Da kein Retry erforderlich war, liegt das Problem eher in Konsistenz und Ausführung als in einem bloßen Formatfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung bleibt mit 60 deutlich hinter der Tool-Ausführung zurück. Das Muster zieht sich durch mehrere Assets: EU License Research und Multilingual Search & Synthesis zeigen ordentliche Rechercheanläufe, aber die Verdichtung verliert Präzision, Priorisierung und belastbare Schlussführung. Für Pipelines, die aus Tool-Output direkt entscheidungsreife Antworten erwarten, ist das zu wenig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Vertrauenspunkt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert es nicht. Das Modell erfindet also keine aktuelle Compliance-Lage aus dem Parametergedächtnis. Allerdings ist die Antwort danach nur begrenzt belastbar verdichtet. Vertrauen in die Quelle ist da, Vertrauen in die Zusammenfassung nur bedingt.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsgerecht. Im 404-Test, der transparentes Fehlermanagement gegen erfundenen Ersatzinhalt prüft, kommuniziert es den Fehlschlag sauber und halluziniert keinen Seiteninhalt. Das ist für reale MCP-Pipelines ein wichtiger Sicherheitsanker.

**Betriebsprofil**

Call 1: 12.25s. Call 2: 39.58s. MCP-Latenz: 0.84s. Total: 316.04s. Langsam für die erreichte Qualität. Kosten/Run: local. Günstig im Betrieb, aber die Zeitkosten sind hoch.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Vorstrukturierungs-Pipelines, in denen Tool-Auswahl wichtig ist und ein nachgelagerter Validator oder ein stärkeres Synthese-Modell die Endantwort absichert. Nicht geeignet als alleinige letzte Instanz für Compliance, Policy oder andere toolgestützte Entscheidungsantworten, bei denen präzise Verdichtung und strikt valide MCP-Ausführung ohne Aufsicht erforderlich sind.