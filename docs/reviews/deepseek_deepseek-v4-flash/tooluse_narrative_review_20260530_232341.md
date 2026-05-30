**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:23:41


Bedingt deploy, weil die Tool-Ausführung belastbar wirkt, die Synthese jedoch mit Combined 67.92 nur moderat ist und eine erkannte Halluzination das Vertrauen in unbeaufsichtigte Ergebnisverdichtung begrenzt.

**Tool-Execution-Profil**

DeepSeek V4 Flash produziert valide Tool-Calls und brauchte keinen Retry. Das spricht für saubere MCP-Protokolltreue und gegen ein reines Formatproblem. Der P1-Wert von 86.67 ist für produktive Tool-Pipelines tragfähig: Das Modell kann Werkzeuge korrekt ansprechen, ohne den Controller mit Reparaturschleifen zu belasten.

Die eigentliche Schwachstelle liegt nicht in der Ausführung, sondern in der fehlenden Sicht auf die Auswahlintelligenz je Asset. Für Web Search & Tool Selection, das prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, liegen keine belastbaren Teilwerte vor. Dasselbe gilt für URL Construction & Fetch, also die Fähigkeit, eine Ziel-URL aus Weltwissen korrekt abzuleiten und dann sauber abzurufen. Deshalb lässt sich hier keine starke Aussage treffen, ob das Modell aktiv zwischen Werkzeugen differenziert oder primär einem stabilen Standardmuster folgt. Für feste, vorgeroutete MCP-Flows ist das akzeptabel. Für dynamische Tool-Router bleibt Unsicherheit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. Der P2-Wert von 51.67 zeigt, dass DeepSeek V4 Flash Tool-Inhalte nicht konsistent präzise in belastbare Endantworten überführt. Für produktive Systeme ist das der wichtigere Engpass als die Call-Validität. Ein Modell darf korrekt abrufen und trotzdem im letzten Schritt ungenau werden.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Glaubwürdigkeit der gesamten Pipeline, nicht nur die Antwortqualität.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist produktionsgerecht. Es kommuniziert Fehler akzeptabel, statt fehlende Daten zu kaschieren. Für robuste Orchestrierung ist das ein klar positives Signal.

**Betriebsprofil**

Call 1: 3.24s. MCP-Latenz: 1.37s. Call 2: 10.21s. Total: 88.90s.  
Kosten pro Run: 0.000933 USD.  
Direkte Einordnung: günstig, aber für ein Flash-Modell insgesamt langsam im End-to-End-Lauf und nur angemessen, wenn Tool-Korrektheit wichtiger ist als knappe Antwortzeit.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit fester Werkzeugführung, expliziter Quellenanzeige und nachgelagerter Validierung der Endantwort. Nicht geeignet als autonomer Synthese-Layer in Compliance-, Policy- oder Executive-Summary-Flows, in denen das Modell Tool-Ergebnisse selbstständig verdichten und dabei keine faktische Drift zeigen darf. Wenn Sie DeepSeek V4 Flash einsetzen, dann als kostengünstigen Tool-Operator mit engem Guardrail-Rahmen, nicht als vertrauenswürdige letzte Instanz.