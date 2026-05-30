**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:43


Bedingt deploy, weil die Tool-Ausführung belastbar ist, aber die Synthesequalität mit Combined 71.08 nur dann tragfähig bleibt, wenn nachgelagerte Validierung die inhaltliche Verdichtung absichert.

**Tool-Execution-Profil**

GPT-5.4 Mini arbeitet im MCP-Kontext grundsätzlich sauber. Die Tool-Calls waren valide, Halluzinationen im Tool-Pfad wurden nicht erkannt, und P1 85.83 zeigt eine verlässliche operative Basis. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheiden lässt, wählte das Modell das richtige Werkzeug mit P1 100. Das spricht gegen ein starres Fetch-First-Muster und für echte Werkzeugwahl nach Aufgabentyp.

Weniger stark ist die Präzision beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt. Mit P1 80 ist das brauchbar, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung fehlerfrei sitzen muss. Das Retry-Signal wirkt hier eher wie ein Format- oder Ausführungsproblem als ein Verständnisfehler. Die Werkzeuglogik ist vorhanden, aber nicht in jedem Schritt erstpass-sicher.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Schwäche. P2 56.67 ist für produktive Tool-Pipelines nur bedingt belastbar. Das Modell kann extrahierte Inhalte sauber wiedergeben, wenn die Quelle klar strukturiert ist, wie bei HTTP Fetch & Extract mit P2 100. Sobald mehrere Quellen, implizite Einschränkungen oder sprachübergreifende Zusammenführung nötig sind, sinkt die Verdichtungsqualität sichtbar. EU License Research mit P2 20 ist dafür der klare Warnhinweis.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist besser als die reine P2-Leistung vermuten lässt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Der Content-Verification-State B2 und die sehr niedrige P2 zeigen also eher unsaubere oder unvollständige Verdichtung als erfundene Fakten. Für Compliance-nahe Pipelines ist das relevant: Das Modell bricht Vertrauen nicht aktiv, aber es verdichtet aktuelle Evidenz zu unpräzise.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call statt erfundenem Seiteninhalt misst, bleibt das Modell auf der akzeptablen Seite. P2 60 ist kein starkes Incident-Handling, aber produktionsfähig: Es kommuniziert den Fehler, statt Ersatzinhalt zu halluzinieren. Das ist für robuste Orchestrierung wichtiger als sprachliche Eleganz.

**Betriebsprofil**

Call 1: 2.50s. MCP-Latenz: 1.35s. Call 2: 3.28s. Total: 42.81s. Kosten pro Run: 0.018911 USD. Operativ: eher langsam im End-to-End-Lauf, dafür günstig. Preis-Leistung ist solide, wenn hohe Antworttreue nicht die Primäranforderung ist.

**Fazit & Empfehlung**

Geeignet für allgemeine MCP-Pipelines mit klaren Tools, gut strukturierten Quellen und nachgelagerter Prüfung der Ergebniszusammenfassung. Nicht geeignet als unbeaufsichtigte Schicht für Compliance, Lizenzbewertung oder andere Fälle, in denen aktuelle Web-Evidenz präzise und vollständig verdichtet werden muss. Wenn Sie ein Modell suchen, dem Sie Tool-Infrastruktur anvertrauen, ist die Ausführung hier überzeugender als die Schlussredaktion. Deploy nur dort, wo ein Verifier, Schema-Checks oder menschliche Freigabe die Synthese absichern.