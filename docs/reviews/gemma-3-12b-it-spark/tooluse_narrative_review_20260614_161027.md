**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:27


Bedingt deploy, weil die Tool-Ausführung mit P1 83.33 grundsätzlich tragfähig wirkt, aber ein invalider Tool-Call und erkannte Halluzinationen die Vertrauenskette für produktive MCP-Pipelines beschädigen. Der Combined-Score von 64.38 stützt kein unüberwachtes Routing auf dieses Modell.

**Tool-Execution-Profil**

Gemma 3 12B IT zeigt auf der Ausführungsseite brauchbare Grundkompetenz. Es kann Tools offenbar in vielen Fällen anstoßen und arbeitet ohne Retry-Bedarf, was gegen ein reines Formatproblem spricht. Kritisch bleibt aber, dass der Tool-Call nicht durchgängig valide war. Für MCP-Betrieb heißt das: Die Schwäche liegt eher in der letzten Meile der Protokolltreue als in kompletter Tool-Unfähigkeit.

Bei der Werkzeugwahl bleibt das Bild unvollständig, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Damit gibt es keinen belastbaren Beleg dafür, dass das Modell situativ zwischen web_search und fetch unterscheidet, statt einem festen Antwortmuster zu folgen. Für Architekturen mit dynamischer Tool-Selektion ist das ein reales Integrationsrisiko. In deterministischen Pipelines mit vorgegebenem Tool-Pfad ist es deutlich besser aufgehoben.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher nur begrenzt zuverlässig. P2 48.33 ist für produktive Ergebnisverdichtung zu niedrig, wenn aus Fetch- oder Search-Resultaten präzise Fakten, Einschränkungen oder Versionen extrahiert werden müssen. Das Modell kann Antworten komprimieren, aber nicht stabil genug, um verdichtete Ausgaben ohne Nachkontrolle in nachgelagerte Systeme zu geben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, hat es nicht halluziniert. Das ist der wichtigste positive Befund. Gleichzeitig bleibt der globale Halluzinations-Flag ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, ist nicht nur die Antwortqualität betroffen, sondern die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, hat das Modell keinen Seiteninhalt halluziniert. Das ist produktionsreif im engeren Sinn. Ein Tool-Fehler wird damit nicht automatisch in einen inhaltlichen Fehler verwandelt. Für robuste Pipelines ist das wichtiger als reine Antwortglätte.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Setups attraktiv. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist kein Ausreißer nach unten, aber auch kein Souveränitätsbonus durch überlegene Tool-Kompetenz. Der lokale Betrieb ist hier der primäre Mehrwert, nicht die Qualitätsführerschaft.

**Fazit & Empfehlung**

Geeignet für lokale, kostenstabile Pipelines mit enger Führung: vorselektierte Tools, klare Prompts, menschliche oder regelbasierte Endkontrolle und tolerierbare Verdichtungsunschärfe. Nicht geeignet als autonomer Tool-Orchestrator, für Compliance-nahe Rechercheketten oder für Workflows, in denen die Zusammenfassung selbst als belastbares Systemartefakt weiterverarbeitet wird. Wenn Sie es einsetzen, dann als ausführendes Mid-Layer-Modell mit Guardrails, nicht als vertrauenswürdige Endinstanz.