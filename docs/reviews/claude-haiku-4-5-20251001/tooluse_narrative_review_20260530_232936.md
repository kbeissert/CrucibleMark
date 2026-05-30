**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:36


Bedingt deploy, weil Claude Haiku 4.5 valide Tool-Calls produziert und operativ zuverlässig wirkt, aber die Synthesetreue mit Combined 68.92 und P2 52.50 zu schwach für unbeaufsichtigte wissensintensive Pipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der tragfähige Teil des Modells. Tool-Calls waren valide, MCP-konform und ohne Retry. Das spricht gegen ein Protokoll- oder Formatproblem. Beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne Hinweis zwischen Suche und direktem Fetch unterscheidet, erreicht es P1 80. Das zeigt brauchbare Werkzeugwahl, aber keine durchgehend sichere Entscheidung in offenen Situationen. Beim Test URL Construction & Fetch, der die Ableitung einer korrekten Ziel-URL aus internem Wissen misst, liegt es ebenfalls bei P1 80. Das wirkt nicht wie starres Schema-Folgen, sondern wie solide, aber nicht deterministische Tool-Intelligenz. In produktiven Orchestrierungen kann man ihm Tool-Zugriff geben. Man sollte die Auswahlpfade jedoch durch Guardrails, URL-Validierung und gegebenenfalls Tool-Routing absichern.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. Die P2-Werte zeigen ein klares Muster: starke Ausführung, aber schwache Verdichtung. EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis fallen jeweils auf P2 40 zurück. Auch HTTP Fetch & Extract bleibt mit P2 35 deutlich unter Produktionsniveau für präzise Faktenverdichtung. Das Modell holt Informationen, verliert aber bei Priorisierung, Struktur und belastbarer Zusammenfassung an Schärfe.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell im verifizierten Inhalt. Halluzination wurde dort nicht erkannt, Content-Verification-State A. Gleichzeitig ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, sinkt die Vertrauenswürdigkeit der gesamten Tool-Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Aufrufen gegen erfundenen Ersatzinhalt stellt, verhält sich Claude Haiku 4.5 produktionsgerecht. P2 80 und keine Halluzination trotz 404. Das Modell kommuniziert Fehler hinreichend offen, statt Seitentext zu erfinden. Für robuste Pipelines ist das ein wesentlicher Pluspunkt.

**Betriebsprofil**

Call 1: 5.43s. MCP-Latenz: 1.35s. Call 2: 3.35s. Total: 60.75s. Kosten pro Run: $0.034324. Direkturteil: günstig, aber für ein kompaktes Schnellmodell in der End-to-End-Laufzeit nicht schnell genug, um die nur moderate Gesamtleistung zu kompensieren.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klaren Tools, niedrigen Kostenanforderungen und menschlicher oder regelbasierter Endkontrolle. Besonders brauchbar für Retrieval, URL-Ableitung, einfache Recherchewege und saubere Fehlerbehandlung. Nicht geeignet als letzte Instanz für Compliance, präzise Extraktion, mehrsprachige Synthese oder jede Pipeline, in der die Antwort direkt als verlässliches Tool-Abbild gelten muss. Empfehlung: als kostengünstiger Tool-Operator einsetzen, nicht als vertrauenswürdiger Synthese-Layer.