**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:54


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber die Tool-Calls nicht durchgehend valide sind und die Synthesequalität für verlässliche Ergebnisverdichtung zu schwach bleibt. Der Combined-Score von 73.00 reicht für produktive Teilaufgaben, nicht für unüberwachte End-to-End-Pipelines.

**Tool-Execution-Profil**

Das Modell zeigt grundsätzlich gutes Werkzeugverständnis. P1 mit 90.00 spricht dafür, dass es Tool-Nutzung als primären Arbeitsmodus akzeptiert und nicht reflexhaft aus Parametern antwortet. Kritisch ist aber das Signal `tool_call_valid: false`. Damit ist nicht die Bereitschaft zum Tool-Einsatz das Problem, sondern die Protokolltreue im Aufruf selbst. Für MCP-Pipelines ist das ein harter operativer Punkt, weil schon kleine Format- oder Schemafehler Orchestrierung und Logging brechen können.

Bei Web Search & Tool Selection und URL Construction & Fetch fehlen Einzeldaten. Deshalb lässt sich nicht belastbar sagen, ob das Modell aktiv zwischen Suche und Direktabruf unterscheidet oder nur einem gelernten Muster folgt. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein triviales Formatversagen und eher für punktuelle Ungenauigkeit im Call-Verhalten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 mit 56.67 ist der klare Schwachpunkt dieses Modells. Das reicht für grobe Zusammenfassungen und strukturiertes Ausgeben, aber nicht für Pipelines, in denen extrahierte Fakten präzise konsolidiert, priorisiert und widerspruchsfrei zurückgegeben werden müssen. Gerade bei mehrsprachiger Recherche oder bei dichtem Quellmaterial ist hier mit Informationsverlust zu rechnen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist besser als die Verdichtungsleistung. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, wurde keine Halluzination erkannt. Das ist wichtig. Das Modell erfindet hier keinen scheinbar aktuellen Compliance-Inhalt aus dem Trainingsstand.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei scheiterndem Abruf prüft, halluziniert das Modell keinen Ersatzinhalt. Das ist produktionsreif. Ein Tool-Fehler bleibt damit als Tool-Fehler sichtbar, statt in falsche Fakten umgeschrieben zu werden. Für robuste Pipelines ist dieses Verhalten deutlich wichtiger als sprachliche Eleganz.

**Betriebsprofil**

Call 1: 17.12s. Call 2: 59.85s. MCP-Latenz: 0.97s. Total: 467.70s.  
Lokal günstig im Run-Kostenmodell. Operativ sehr langsam im Verhältnis zur gebotenen Qualität.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Tool-Pipelines, in denen das Modell recherchieren, strukturieren und Fehler offenlegen soll, aber ein nachgelagerter Validator Tool-Calls und Ergebnisverdichtung prüft. Nicht geeignet als alleinige Instanz für Compliance, präzise Faktenaggregation oder agentische Workflows mit strikter MCP-Schemahärte. Wer lokale Souveränität und multimodale Option will, kann es als orchestrierten Worker einsetzen. Für autonome Tool-Operator-Rollen ist die Kombination aus invalider Call-Treue, schwacher Synthese und sehr hoher Laufzeit zu riskant.