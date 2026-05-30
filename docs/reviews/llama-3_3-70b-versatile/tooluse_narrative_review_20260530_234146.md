**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:46


Bedingt deploy, weil die Tool-Calls formal valide sind, aber die Gesamtleistung mit 42.33 und vor allem die schwache Synthesetreue für produktive Tool-Pipelines nicht belastbar genug ist.

**Tool-Execution-Profil**

Das Modell spricht MCP formal korrekt an. Tool-Call valide: true, Retry war nicht erforderlich. Das ist ein positives Basissignal für Integrationen, weil kein Protokoll- oder Formatbruch auffällt.

In der eigentlichen Werkzeugwahl zeigt es jedoch wenig agentische Intelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, erreicht es nur P1 40. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Modellwissen ableitet und dann sauber abruft, bleibt es ebenfalls bei P1 40. Das spricht nicht für adaptive Tool-Auswahl, sondern eher für ein starres Muster: Es kann Calls ausführen, erkennt aber zu oft nicht, welches Werkzeug den Informationsbedarf wirklich deckt. Positiv abgesetzt ist nur HTTP Fetch & Extract mit P1 80. Wenn die richtige Ressource bereits feststeht, arbeitet das Modell also deutlich verlässlicher als in offenen Tool-Selection-Situationen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 liegt insgesamt bei 31.67. Besonders problematisch ist, dass aus vorhandenem Tool-Material häufig keine belastbare, präzise Verdichtung entsteht. Das sieht man auch an HTTP Fetch & Extract mit P2 15 und URL Construction & Fetch mit P2 15. Für Pipelines, die strukturierte Tool-Ausgaben in entscheidungsreife Antworten überführen sollen, ist das zu wenig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, ist das Vertrauenssignal ebenfalls schwach: P2 20 bei Content-Verification-State B2. Zwar wurde dort keine Halluzination erkannt, aber global ist hallucination_flag=true. Das ist kein bloßes Qualitätsproblem, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Fakten als Tool-Ergebnisse präsentiert, verliert die gesamte Pipeline ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Hier verhält sich das Modell produktionsgerecht. Im Test Tool Failure Handling (404), der einen scheiternden Tool-Aufruf simuliert, erreicht es P2 80 und erfindet keinen Ersatzinhalt. Es kommuniziert den Fehler transparent. Das ist für Produktion akzeptabel und klar besser als die eigentliche Syntheseleistung.

**Souveränitätsprofil**

Lokal betreibbar und kostenseitig attraktiv, aber nicht fleet-kompetitiv genug. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet ist das Modell für souveräne, kostensensitive Pipelines mit enger Führung: bekannte URLs, feste Tool-Pfade, klare Fehlerbehandlung, menschliche Nachprüfung. Nicht geeignet ist es für offene Recherche, Compliance-nahe Auswertung, dynamische Tool-Orchestrierung oder jede Pipeline, in der Tool-Ergebnisse präzise verdichtet und als verlässliche Entscheidungsgrundlage ausgegeben werden müssen. Für produktive MCP-Infrastruktur taugt es eher als ausführender Baustein unter starker Guardrail-Steuerung, nicht als selbstständig vertrauenswürdiger Tool-Agent.