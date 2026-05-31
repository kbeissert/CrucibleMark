**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:53:04


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthese aber zu oft von den Tool-Ergebnissen wegdriftet und damit das Vertrauen in produktive MCP-Pipelines begrenzt. Combined 63.29 ist dafür nur ein Hintergrundsignal.

**Tool-Execution-Profil**

Bei der Werkzeugnutzung wirkt GPT OSS 120B Cloud kompetent. Tool-Call valide: true, kein Retry erforderlich. Das spricht für saubere MCP-konforme Aufrufe und gegen ein reines Formatproblem. Besonders stark ist das Modell im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird: P1 100. Das zeigt echte Werkzeugwahl und nicht nur starres Fetch-first-Verhalten.

Weniger präzise ist es beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL aus Eigenwissen misst: P1 80. Das reicht für flexible Recherchepfade, aber nicht für deterministische Pipelines mit fragiler URL-Logik. Insgesamt ist das Ausführungsprofil klar stärker als die nachgelagerte Verarbeitung der Ergebnisse.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 39.17 ist für ein Frontier-Modell schwach. Das Muster ist konsistent: HTTP Fetch & Extract erreicht noch P2 60, URL Construction & Fetch P2 80, aber Web Search & Tool Selection fällt auf P2 35, Multilingual Search & Synthesis auf P2 40 und Tool Failure Handling (404) auf P2 20. Das Modell findet Informationen, verdichtet sie aber nicht verlässlich in eine belastbare Antwortstruktur.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Genau hier liegt das Sicherheitsrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt P2 bei 0 bei Content-Verification-State B2. Halluzination erkannt ist dort zwar False, global aber True. Für Produktion zählt der Befund: Wenn ein Modell in einer Tool-Pipeline Inhalte ausgibt, die nicht sauber an den Tool-Output gebunden sind, unterläuft es die Kontrollfunktion der gesamten Infrastruktur.

**Fehlerresilienz**

Im 404-Test reagiert das Modell akzeptabel, aber nicht gut. Es halluziniert keinen Seiteninhalt trotz Fehler. Das ist die Mindestanforderung für Produktion. P2 20 zeigt jedoch, dass die Fehlerkommunikation schwach verdichtet und operativ wenig hilfreich ist. Für robuste Systeme ist das tragbar, solange die Orchestrierung Fehler selbst abfängt und nicht auf die Modellzusammenfassung vertraut.

**Betriebsprofil**

Call 1 3.37s. MCP-Latenz 1.24s. Call 2 7.52s. Total 72.82s.  
Kosten pro Run: 0.002596 USD.  
Direkte Einordnung: günstig, aber langsam im Gesamtlauf und gemessen an der Syntheseleistung nicht effizient.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen das Modell primär Tools auswählt, Calls erzeugt und Rohergebnisse an nachgelagerte Validatoren oder regelbasierte Parser übergibt. Nicht geeignet für Compliance-, Recherche- oder Entscheidungs-Pipelines, in denen die Modellantwort selbst als verlässliche Verdichtung des Tool-Outputs dient. Wenn Sie es einsetzen, dann mit strikter Output-Validierung, Source-Binding und möglichst geringer Freiheit in der finalen Antwortbildung.