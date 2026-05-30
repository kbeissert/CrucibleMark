**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:58


Bedingt deploy, weil die Tool-Ausführung stark und protokollsauber ist, das Modell aber bei Tool-Fehlern halluziniert und damit eine MCP-Pipeline sicherheitstechnisch entwerten kann. Der kombinierte Score ist gut, das Vertrauensprofil nicht.

**Tool-Execution-Profil**

Claude Sonnet 4.5 arbeitet auf der Ausführungsebene verlässlich. Tool-Calls waren valide, ein Retry war nicht nötig, und P1 mit 90 zeigt, dass das Modell MCP-konform operiert. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt es die richtige Werkzeugklasse sicher. Das spricht gegen starres Pattern-Matching und für echte Werkzeugwahl im Kontext.

Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus vorhandenem Wissen prüft, ist es brauchbar, aber nicht völlig deterministisch. P1 von 80 heißt: Es kann die Zieladresse oft korrekt konstruieren und dann fetch ausführen, ist aber nicht präzise genug für fragile Pipelines, in denen schon kleine URL-Abweichungen Folgeschäden erzeugen. Für agentische Orchestrierung ist das stark. Für strikt deterministische Retrieval-Pfade braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 50.83 ist der eigentliche Schwachpunkt dieses Laufs. Solide bei HTTP Fetch & Extract und URL Construction & Fetch, deutlich schwächer bei Web Search & Tool Selection und vor allem bei Multilingual Search & Synthesis. Das Modell findet Informationen, verdichtet sie aber nicht durchgehend präzise genug für Architekturen, die auf verlustarme Ergebnisübernahme angewiesen sind.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingt, bleibt es im beschafften Material. P2 60 ist nicht brillant, aber der Vertrauensbefund ist positiv: Content-Verification-State A, keine Halluzination. Das ist das richtige Signal für Compliance-nahe Recherchen. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko, weil erfundene Fakten in einer Tool-Pipeline nicht nur ungenau, sondern infrastrukturschädlich sind.

**Fehlerresilienz**

Hier liegt die produktionskritische Grenze. Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlgeschlagenen Abruf misst, halluziniert das Modell trotz 404 Seiteninhalt. P2 35 ist deshalb kein bloßer Qualitätsabfall, sondern ein Vertrauensbruch. In Produktion ist nur explizite Fehlerkommunikation akzeptabel. Ersatzinhalt zu erfinden ist ohne Ausnahme ein Blocker für unbeaufsichtigte Pipelines.

**Betriebsprofil**

2.24s bis erster Call, 8.38s bis zweiter Call, 68.11s gesamt. Eher langsam. MCP-Latenz 0.74s. Kosten pro Run: 0.064233 USD. Nicht teuer, aber für die gebotene Synthesetreue kein Effizienzvorteil.

**Fazit & Empfehlung**

Geeignet für überwachte Tool-Pipelines mit starker Post-Validation, etwa Rechercheassistenz, explorative Web-Orchestrierung und Operator-in-the-loop-Workflows. Nicht geeignet für autonome Retrieval-, Compliance-, Incident- oder Support-Pipelines, in denen Tool-Fehler sauber propagiert werden müssen und jedes ausgegebene Faktum als toolgestützt gelten soll. Wenn Sie es einsetzen, dann nur mit harter Fehlerbehandlung, Ergebnisvalidierung und einer Policy, die Antworten nach fehlgeschlagenen Tool-Calls unterdrückt.