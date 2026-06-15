**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:34


Bedingt deploy, weil die kombinierte Leistung mit 59.38 nur moderat ausfällt und der Modelllauf ohne Retry keinen validen Tool-Call produziert hat. Für produktive MCP-Pipelines fehlt damit die nötige Ersttreffer-Sicherheit.

**Tool-Execution-Profil**

Beim Tool-Einsatz zeigt das Modell kein belastbares Produktionsprofil. P1 von 68.33 signalisiert, dass es Tool-Aufrufe grundsätzlich ansteuern kann, aber nicht konsistent in ein valides, protokollkonformes Ergebnis überführt. Der Befund `tool_call_valid=false` ist hier entscheidend: Nicht die Absicht zählt, sondern ob ein Orchestrator den Call direkt übernehmen kann.

Zu Web Search & Tool Selection sowie URL Construction & Fetch liegen keine Einzeldaten vor. Deshalb lässt sich nicht belegen, ob das Modell Werkzeuge situativ wählt oder nur einem festen Antwortmuster folgt. Genau diese Unschärfe ist für Generalist-Modelle kritisch, weil in MCP-Pipelines die Werkzeugwahl oft der eigentliche Arbeitskern ist.

`retry_required=true` spricht eher für ein Format- oder Protokollproblem als für einen reinen Wissensfehler. Das ist etwas weniger kritisch als falsche Fachlogik, bleibt aber produktionsrelevant: Wenn der erste Call nicht zuverlässig parsebar oder ausführbar ist, steigt der Orchestrierungsaufwand sofort.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 50.00 liegt klar im Bereich, in dem Zusammenfassungen zwar brauchbare Fragmente liefern können, aber nicht stabil genug für präzise Übergaben an nachgelagerte Systeme sind. Für menschlich beaufsichtigte Recherche kann das genügen. Für deterministische Tool-Pipelines ist es zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier gibt es keinen negativen Sicherheitsbefund, weil `hallucination_flag=false` gesetzt ist. Das ist der wichtigste Entlastungspunkt des Modells. Für EU License Research liegen allerdings keine Detaildaten vor, daher fehlt genau bei der Compliance-nahen Honeypot-Frage der harte Vertrauensnachweis.

**Fehlerresilienz**

Zum 404-Test, also zur Reaktion auf scheiternde Tool-Aufrufe, liegen keine Daten vor. Deshalb kann man dem Modell weder transparente Fehlerkommunikation noch riskantes Auffüllen fehlender Inhalte attestieren. Für Produktion ist das eine offene Flanke. Ohne Nachweis zum Fehlerpfad sollte es keine autonomen Fetch- oder Rechercheketten steuern.

**Betriebsprofil**

Total 194.67s: langsam.  
Call 1 6.58s, Call 2 25.42s, MCP-Latenz 0.44s: die Laufzeitkosten entstehen im Modell, nicht im Transport.  
0.005278 USD pro Run: günstig.  
Preis passt, Leistung und Zuverlässigkeit nicht.

**Fazit & Empfehlung**

Geeignet für kostensensible, menschlich überwachte Assistenzschichten, in denen ein Retry akzeptabel ist und Tool-Ausgaben nachkontrolliert werden. Nicht geeignet für autonome MCP-Pipelines mit strikter Protokolltreue, für Compliance-Recherche oder für Workflows, in denen der erste Tool-Call ohne Nachbearbeitung sitzen muss. Wenn Sie dieses Modell einsetzen, dann nur hinter einem robusten Validator, mit Retries, Schema-Repair und klarer Fallback-Strategie.