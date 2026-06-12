**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:36


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen für unbeaufsichtigte Produktivpipelines begrenzen. Der Gesamteindruck ist gut, aber nicht robust genug für High-Trust-Automation.

**Tool-Execution-Profil**

Mit P1 90.00 zeigt das Modell klare operative Stärke im Umgang mit Tools. Das passt zum Profil als Coding- und Agentic-Modell. Für den Produktionseinsatz zählt aber nicht nur die Absicht, sondern Protokolltreue. Genau dort liegt der Bruch: Der Tool-Call war nicht valide. Das ist kein Randdetail, sondern ein Integrationsrisiko für MCP-gestützte Ketten, weil schon ein formal falscher Aufruf Orchestrierung, Retries und nachgelagerte Guards belastet.

Zu den Auswahltests liegt kein Asset-scharfer Einzelwert vor. Deshalb lässt sich nicht belastbar sagen, ob das Modell beim Test Web Search & Tool Selection, der die Unterscheidung zwischen Suche und direktem Fetch prüft, echte Werkzeugintelligenz zeigt oder nur einem festen Ausführungsmuster folgt. Gleiches gilt für URL Construction & Fetch, also die Fähigkeit, eine Ziel-URL korrekt herzuleiten und dann deterministisch abzurufen. Der hohe P1-Wert spricht für brauchbare Agentenmechanik, aber die invalide Call-Struktur verhindert ein uneingeschränktes Ja zur Pipeline-Übergabe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. Mit P2 59.17 liefert das Modell keine verlässlich starke Verdichtung, sondern eher funktionale als präzise Synthese. Für Engineering-Workflows ist das noch tragbar, wenn Rohdaten sichtbar bleiben. Für Compliance, Policy oder Executive Summaries ist es zu ungenau.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparentes Verhalten bei fehlschlagendem Abruf misst, hat das Modell keinen Ersatzinhalt erfunden. Das ist produktionsfähig. Ein Tool-Fehler wird damit nicht in stillschweigende Falschinformation übersetzt. Für robuste Pipelines ist genau dieses Verhalten entscheidend.

**Souveränitätsprofil**

Lokal betreibbar und damit attraktiv für sensible Umgebungen ohne externen Datentransfer. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist ein kleiner Abstand und macht das Modell als souveräne Option wettbewerbsfähig.

**Fazit & Empfehlung**

Geeignet für lokale Coding-Agents, interne Entwicklerassistenz und MCP-Pipelines mit sichtbaren Tool-Ausgaben, strikter Schema-Validierung und nachgeschalteten Antwort-Guards. Nicht geeignet für vollautonome Recherche-, Compliance- oder Entscheidungsstrecken, in denen die sprachliche Verdichtung selbst als vertrauenswürdiges Endprodukt dienen muss. Wenn Sie es einsetzen, dann als gut instrumentierten Tool-Operator, nicht als letzte Wahrheitsinstanz.