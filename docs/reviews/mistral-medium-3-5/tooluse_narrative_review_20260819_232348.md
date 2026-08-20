**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:23:48


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen in unbeaufsichtigte MCP-Pipelines begrenzen. Der Gesamteindruck ist gut, aber nicht robust genug für High-Trust-Automation.

**Tool-Execution-Profil**

Mistral Medium 3.5 zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Ablaufverhalten. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, wählt es das richtige Werkzeug sicher. Das spricht für brauchbare Orchestrierungslogik. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es brauchbar, aber weniger präzise. Das ist der typische Punkt, an dem produktive Pipelines deterministische Guardrails brauchen.

Kritisch ist der Befund, dass der Tool-Call nicht durchgehend valide war. Da kein Retry nötig war, wirkt das nicht wie ein bloßes Formatproblem mit anschließender Selbstkorrektur, sondern wie ein einmaliger Protokoll- oder Parameterausrutscher, den die Laufzeit nicht abgefangen hat. Für MCP bedeutet das: gute Tool-Intelligenz, aber keine durchgehend verlässliche Protokollhygiene.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung ist mit 59.17 der klare Schwachpunkt. Besonders bei EU License Research, das aktuelle Lizenzrestriktionen aus Web-Quellen zusammenführen soll, und bei HTTP Fetch & Extract, das präzise Faktentreue aus Fetch-Inhalten misst, verliert das Modell an Genauigkeit und Verdichtungsschärfe. Es findet Material, aber die letzte Meile der belastbaren Zusammenfassung ist nicht konstant stark.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es nicht. Das ist der wichtigste Vertrauensanker in diesem Bericht. Gleichzeitig ist der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, wird nicht nur eine Antwort schlecht, sondern die Infrastruktur selbst unzuverlässig.

**Fehlerresilienz**

Beim 404-Test, der prüft ob ein fehlgeschlagener Tool-Call transparent kommuniziert oder Seiteninhalt erfunden wird, reagiert das Modell akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. Die Fehlerkommunikation ist damit produktionsfähig, auch wenn sie nicht besonders stark verdichtet oder handlungsleitend ausfällt.

**Betriebsprofil**

Total 39.11s pro Run. MCP-Latenz 2.04s. Modell-Calls 0.64s und 3.84s. Für die gezeigte Qualität langsam. Kosten: local. Preislich günstig im Betrieb, aber die Zeit pro Durchlauf ist für interaktive Tool-Pipelines hoch.

**Fazit & Empfehlung**

Geeignet für recherchierende MCP-Pipelines mit menschlicher Kontrolle, für mehrsprachige Beschaffung, Discovery-Schritte und Tool-Auswahl vor nachgelagerter Validierung. Nicht geeignet für Compliance, Lizenzprüfung, regulatorische Antworten oder andere Pfade, in denen die Synthese selbst als belastbarer Endbefund dient. Deployen nur mit Schema-Validation, Tool-Call-Guardrails und einer zweiten Instanz zur Ergebnisprüfung.