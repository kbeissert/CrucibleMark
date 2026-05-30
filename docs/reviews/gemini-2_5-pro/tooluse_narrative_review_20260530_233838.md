**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:38


Bedingt deploy, weil Gemini 2.5 Pro valide Tool-Calls produziert, nicht halluziniert und im Tool-Use belastbar wirkt, aber die Synthesequalität für produktive Entscheidungsstrecken zu inkonsistent bleibt.

**Tool-Execution-Profil**

Die operative Grundlage ist stark. Das Modell wählt Werkzeuge zielgerichtet, produziert protokollkonforme MCP-Calls und brauchte keinen Retry. Besonders relevant ist der Unterschied zwischen den Auswahltests: Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch nötig ist, erkennt es die passende Werkzeugklasse sicher. Das spricht für echte Tool-Intelligenz statt für starres Musterfolgen. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL aus eigenem Wissen misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Kurz: Es entscheidet gut zwischen Such- und Abrufwerkzeugen, ist aber schwächer, wenn es die exakte Zieladresse selbst konstruieren muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung von 60 zeigt, dass Gemini 2.5 Pro abgerufene Informationen oft korrekt zusammenzieht, aber nicht konstant scharf genug verdichtet. Das sieht man an EU License Research mit nur 20 Punkten in der Synthese trotz perfekter Ausführung und an mehreren 60er-Ergebnissen bei URL Construction & Fetch sowie Multilingual Search & Synthesis. Für reine Retrieval-Pipelines reicht das oft. Für Compliance, Policy oder Executive Briefing ist diese Verdichtung zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Training kommen, wurde keine Halluzination erkannt. Der niedrige P2-Wert ist damit kein Sicherheitsbruch, sondern ein Verdichtungsproblem. Das ist ein wichtiger Unterschied für Produktionsbetrieb.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt prüft, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt trotz fehlgeschlagenem Tool-Aufruf. Diese Fehlerdisziplin ist für Tool-Pipelines entscheidend und hier klar vorhanden.

**Betriebsprofil**

Call 1: 8.11s. Call 2: 11.54s. MCP-Latenz: 0.93s. Total pro Run: 123.44s. Das ist langsam. Kosten pro Run: $0.023781. Das ist für ein Frontier-Modell moderat, gemessen an der nur guten Gesamtleistung aber nicht günstig.

**Fazit & Empfehlung**

Geeignet für agentische Orchestrierung, Recherche-Pipelines, mehrstufige Tool-Flows und Systeme, in denen saubere Tool-Ausführung wichtiger ist als präzise Endverdichtung. Nicht die erste Wahl für Compliance-Ausgaben, regulatorische Zusammenfassungen oder andere Pipelines, in denen die letzte textliche Verdichtung selbst entscheidungsrelevant ist. Wenn Sie es einsetzen, dann mit nachgelagerter Verifikation oder einem stärkeren Synthese-Gate.