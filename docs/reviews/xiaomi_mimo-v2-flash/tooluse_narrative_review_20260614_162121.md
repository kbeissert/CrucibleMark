**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:21:21


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein ungültiger Tool-Call bei gleichzeitig erkanntem Halluzinationsereignis das Vertrauen für unüberwachte MCP-Pipelines begrenzt. Der kombinierte Score von 75.75 stützt das als brauchbares, aber nicht freigabereifes Default-Modell.

**Tool-Execution-Profil**

Xiaomi MiMo V2 Flash zeigt ein klar brauchbares Ausführungsprofil. P1 von 90.00 spricht dafür, dass es Tools grundsätzlich zielgerichtet ansteuert und operative Schritte meist korrekt aufsetzt. Der kritische Gegenpunkt ist jedoch `tool_call_valid=false`. Das ist kein kleiner Formfehler, sondern ein Integrationsrisiko: In einer MCP-Pipeline zählt nicht nur die Absicht, sondern protokollkonforme Ausführung.

Zu den beiden eigentlichen Auswahltests gibt es keine Einzeldaten. Deshalb lässt sich nicht belastbar sagen, ob das Modell beim Web-Search-&-Tool-Selection-Test selbstständig zwischen Suche und direktem Fetch unterscheidet oder ob es nur einem Standardmuster folgt. Ebenso fehlt die Evidenz, ob es beim URL-Construction-Test Zieladressen präzise genug ableitet. Für Produktion heißt das: gute generelle Tool-Nutzung, aber keine abgesicherte Aussage zur Werkzeugwahl in offenen Situationen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 von 62.50 ist kein Ausfall, aber für produktive Ergebnisverdichtung zu niedrig, wenn aus mehreren Tool-Antworten eine belastbare Endaussage entstehen soll. Das Modell kann Ergebnisse zusammenführen, verliert dabei aber erkennbar an Präzision und Disziplin.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist der wichtige Vertrauensanker. Gleichzeitig bleibt der globale Halluzinationsflag ein Sicherheitsrisiko: Sobald ein Modell auch nur punktuell erfundene Fakten als angebliche Tool-Ergebnisse ausgibt, wird nicht nur die Antwort, sondern die gesamte Tool-Infrastruktur unzuverlässig.

**Fehlerresilienz**

Beim Tool Failure Handling (404), also dem Test auf transparente Reaktion bei einem fehlschlagenden Abruf, halluzinierte das Modell keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Es spricht dafür, dass MiMo V2 Flash Fehlerzustände eher offenlegt als kaschiert. Für robuste Pipelines ist das akzeptabel.

**Betriebsprofil**

0.70s erster Call, 0.81s MCP-Latenz, 3.26s zweiter Call, 28.57s total. Schnell im Einzelaufruf, langsam im Gesamtdurchlauf. Kosten pro Run: local. Preislich günstig, leistungsmäßig nur dann attraktiv, wenn lokale Ausführung wichtiger ist als maximale Synthesetreue.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Tool-Pipelines mit menschlicher Kontrolle, klaren Guardrails und Validierung nach jedem Tool-Schritt. Besonders sinnvoll für Recherche, Vorstrukturierung und transparente Fehlerbehandlung. Nicht die richtige Wahl für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die Endsynthese ohne Nachprüfung unmittelbar weiterverwendet wird. Wenn Sie es einsetzen, dann als ausführendes Zwischenmodell mit nachgelagerter Prüfung, nicht als letzte vertrauensgebende Instanz.