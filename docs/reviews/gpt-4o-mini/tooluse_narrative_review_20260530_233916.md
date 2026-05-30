**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:16


Bedingt deploy, weil GPT-4o Mini valide Tool-Calls erzeugt und operativ stabil wirkt, aber die Synthesequalität mit Combined 66.21 und erkanntem Halluzinationsereignis nicht ausreicht, um unbeaufsichtigt vertrauenswürdige Tool-Ausgaben weiterzureichen.

**Tool-Execution-Profil**

In der Tool-Ausführung arbeitet das Modell solide. P1 83.33, valide Calls und kein Retry-Bedarf sprechen für saubere MCP-Anbindung und brauchbare Protokolltreue. Das ist für Produktion relevant, weil Integrationsfehler hier nicht das Hauptproblem sind.

Bei der Werkzeugwahl zeigt es aber nur begrenzte Eigenintelligenz. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheiden soll, erreicht es zwar P1 80, die inhaltliche Folgeleistung bricht aber stark ein. Das deutet auf funktionierende Tool-Nutzung ohne verlässliche Entscheidungsschärfe. Beim URL-Construction-Test, der korrekte Ziel-URL plus anschließenden Fetch verlangt, bleibt es ebenfalls bei P1 80. Das spricht eher für ein robustes, aber schematisches Muster als für konsistent gute Werkzeugwahl in offenen Pipelines.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Grenze des Modells. P2 48.33 ist für produktive Tool-Pipelines schwach. Positiv fällt HTTP Fetch & Extract auf, wo strukturierte Inhalte sauber übernommen werden. Kritisch sind dagegen Web Search & Tool Selection mit P2 15 und Multilingual Search & Synthesis mit P2 15. Sobald mehrere Quellen, Sprachwechsel oder Auswahlentscheidungen zusammenkommen, verliert das Modell Präzision und priorisiert nicht zuverlässig die belastbaren Fakten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt bei aktuellen Lizenzrestriktionen prüft, halluziniert es nicht offen, aber P2 40 und Content-Verification-State B2 reichen nicht für hohes Vertrauen. Dazu kommt der globale Halluzinationsbefund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Inhalte als Tool-basierte Antwort ausgibt, wird die gesamte Pipeline als Quelle unzuverlässig.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf misst, bleibt das Modell akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler grundsätzlich offen. P2 60 ist nicht stark, aber produktionsfähig. Für robuste Workflows ist das wichtiger als sprachliche Eleganz.

**Betriebsprofil**

Call 1: 1.87s. MCP-Latenz: 1.16s. Call 2: 3.56s. Total: 39.51s. Kosten pro Run: $0.001794. Günstig. Einzelaufrufe schnell. Gesamtlaufzeit für die gezeigte Leistung eher lang.

**Fazit & Empfehlung**

Geeignet für kostensensitive Pipelines mit klarer Tool-Vorstruktur, einfacher Extraktion und verpflichtender Downstream-Validierung. Nicht geeignet für Compliance, Recherche-Synthese, mehrsprachige Wissensaggregation oder agentische Tool-Orchestrierung, in denen das Modell selbst priorisieren und belastbar zusammenführen muss. Wenn Sie es einsetzen, dann als günstigen Executor für eng gefasste Schritte, nicht als letzte Instanz für toolgestützte Wahrheit.