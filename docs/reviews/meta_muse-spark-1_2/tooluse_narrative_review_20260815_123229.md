**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:32:29


Nicht deploy. Das Modell ist für MCP-gestützte Produktion derzeit nicht freigabefähig, weil kein valider Tool-Call zustande kam und der kombinierte Benchmark-Befund bei 0.00 liegt.

**Tool-Execution-Profil**

Für ein als agentisch positioniertes Frontier-Modell ist das Kernproblem nicht schwache Qualität, sondern fehlende nachweisbare Tool-Ausführung. `tool_call_valid=false` bedeutet, dass keine belastbare MCP-konforme Interaktion belegt ist. Damit fehlt die Mindestvoraussetzung für jede Tool-Pipeline.

Die Daten zu Web Search & Tool Selection und URL Construction & Fetch sind jeweils n/a. Das lässt keine positive Aussage darüber zu, ob das Modell zwischen Suche und direktem Fetch intelligent unterscheidet oder nur einem festen Muster folgt. Genau diese Unterscheidung ist in produktiven Pipelines entscheidend, weil zuerst die richtige Beschaffungsstrategie gewählt werden muss und erst danach der eigentliche Abruf. Hier gibt es keinen Evidenzpunkt zugunsten des Modells. `retry_required=false` entschärft das nicht. Es spricht nur dagegen, dass ein bloßer Formatfehler nach Wiederholung lösbar gewesen wäre.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es praktisch keinen verwertbaren Befund. P2 liegt bei 0.00, zugleich sind die Asset-Werte durchgehend n/a. Für den Produktionseinsatz heißt das: Es existiert kein Nachweis, dass das Modell abgerufene Inhalte präzise zusammenfassen, strukturieren und auf Faktenniveau stabil halten kann.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, zeigt immerhin kein Halluzinationssignal. Das ist ein positives Sicherheitsindiz, aber kein Freibrief. Ohne dokumentierte Tool-Nutzung ist nur belegt, dass kein erfundener Inhalt erkannt wurde, nicht dass das Modell zuverlässig quellengebunden arbeitet.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt prüft, wurde keine Halluzination erkannt. Das ist der richtige Sicherheitsreflex. Für Produktion ist solche Fehlertransparenz akzeptabel. Sie ersetzt aber nicht die fehlende Fähigkeit, den eigentlichen Tool-Pfad valide auszuführen.

**Betriebsprofil**

Latenz: n/as. Kosten/Run: local. Leistungsurteil daher nicht belastbar quantifizierbar.

**Fazit & Empfehlung**

Nicht für produktive MCP-Pipelines einsetzen, weder für Recherche, Fetch-basierte Extraktion, Compliance-Arbeit noch orchestrierte Multi-Step-Flows. Der einzige verwertbare positive Befund ist das Ausbleiben erkannter Halluzinationen im Honeypot- und 404-Kontext. Das reicht nicht. Freigabe wäre erst vertretbar, wenn valide MCP-Calls, belastbare Tool-Wahl zwischen Search und Fetch sowie quellengebundene Synthese unter realen Abrufen nachgewiesen sind. Für reine Direktantworten ohne Tool-Vertrauen mag das Modell separat prüfbar sein. Für Tool-Infrastruktur derzeit nicht.