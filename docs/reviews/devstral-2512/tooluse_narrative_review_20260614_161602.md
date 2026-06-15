**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:16:02


Bedingt deploy, weil Devstral 2 keine Halluzinationen zeigte, aber invalide Tool-Calls produzierte und mit 48.50 kombiniert klar unter der Schwelle für vertrauenswürdige Standard-Orchestrierung bleibt.

**Tool-Execution-Profil**

Die Kernschwäche liegt nicht im Zugriff auf Tools an sich, sondern in der Wahl und Form des Aufrufs. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob statt fetch ein web_search nötig ist, erkennt das Modell den Werkzeugwechsel nur unzuverlässig. Das spricht gegen echte Tool-Intelligenz in offenen Pipelines. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließendes fetch misst, arbeitet es deutlich besser. Das Muster wirkt deshalb nicht wie generelle Tool-Unfähigkeit, sondern wie ein eher starres Vorgehen: bekannte direkte Abrufpfade funktionieren, situationsabhängige Werkzeugwahl nicht stabil genug. Da Retry erforderlich war und der Tool-Call als nicht valide markiert ist, spricht mehr für ein Protokoll- oder Formatproblem als für reines Inhaltsverständnis. Für MCP-Pipelines ist das trotzdem kritisch, weil Orchestratoren deterministische Call-Strukturen brauchen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 bei 40 zeigt, dass Devstral 2 gewonnene Inhalte nur begrenzt sauber zusammenführt. Das sieht man besonders bei HTTP Fetch & Extract, das präzise Faktenextraktion aus echtem Seiteninhalt misst, und bei Multilingual Search & Synthesis, das sprachübergreifende Recherche mit deutscher Zusammenfassung prüft. Dort bricht die Verdichtung praktisch weg.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die Synthesequalität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb das Modell an den Tool-Pfad gebunden. Keine Halluzination, Content-Verification-State A. Das ist für Compliance-nahe Workflows wichtiger als der reine P2-Wert.

**Fehlerresilienz**

Beim 404-Test, der misst, ob ein fehlgeschlagener Tool-Call transparent behandelt wird, reagiert Devstral 2 produktionsgerecht. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. P2 80 und keine Halluzination trotz 404 sind ein belastbares Positivsignal. Für produktive Systeme ist das akzeptabel, weil ein sichtbarer Fehler korrigierbar ist, erfundener Ersatzinhalt aber nicht.

**Betriebsprofil**

Total 57.71s pro Run. Modell-Calls 4.74s und 4.51s, MCP-Latenz 0.37s. Damit insgesamt langsam. Kosten 0.004757 pro Run. Damit günstig. Preis passt, Leistung nicht.

**Fazit & Empfehlung**

Geeignet für eng geführte Coding- oder Retrieval-Pipelines mit starker externer Tool-Steuerung, hartem Schema-Check und automatischen Retries. Nicht geeignet für offene MCP-Setups, in denen das Modell selbstständig zwischen Suche, Fetch und Synthese wechseln muss. Wer es einsetzt, sollte die Werkzeugwahl außerhalb des Modells treffen und die Antwort als nachgelagerte Verarbeitung behandeln, nicht als verlässliche Agentensteuerung.