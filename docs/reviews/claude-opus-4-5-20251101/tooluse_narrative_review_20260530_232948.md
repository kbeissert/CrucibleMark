**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:48


Bedingt deployen, weil Claude Opus 4.5 valide Tool-Calls liefert und im MCP-Ablauf zuverlässig bleibt, aber die Synthesetreue mit Combined 72.79 nur dann produktionsfest ist, wenn nachgelagerte Verifikation die Ergebnisverdichtung absichert.

**Tool-Execution-Profil**

Die Tool-Ausführung ist klar die stärkere Seite dieses Modells. Der Tool-Call war valide, ein Retry war nicht erforderlich, und P1 mit 86.67 zeigt ein belastbares Orchestrierungsverhalten. Besonders relevant: Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht das Modell P1=100. Das spricht gegen starres Schema-Verhalten und für echte Werkzeugwahl. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen misst, landet es bei P1=80. Das ist brauchbar, aber nicht deterministisch genug für Flows, in denen URL-Bildung ohne weitere Kontrolle direkt produktive Folgeaktionen auslöst. Als Agentic-Orchestrator ist es damit klar einsetzbar. Als autonomer URL-Konstrukteur nur mit Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 mit 59.17 ist für ein Frontier-Modell der kritische Wert. Die Einzelergebnisse zeigen das Muster deutlich: HTTP Fetch & Extract und Tool Failure Handling (404) sind mit P2=80 solide, aber EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis fallen mit 35 bis 40 sichtbar ab. Das Modell kann also recherchieren und Tools richtig einsetzen, verliert aber bei der Verdichtung häufiger Präzision, Priorisierung oder Quellentreue.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, liegt P2 bei 40 bei Content-Verification-State B1. Es wurde dort keine Halluzination markiert, aber der Befund bleibt ein Vertrauenssignal gegen unbeaufsichtigten Einsatz in Compliance-nahen Pipelines. Zusätzlich ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten wie Tool-Ergebnisse formuliert, verliert die Tool-Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlgeschlagene Tool-Calls misst, verhält sich Claude Opus 4.5 produktionsgerecht. P2=80 und keine Halluzination trotz Fehler zeigen, dass es Fehlschläge offen kommuniziert statt Seiteninhalt zu erfinden. Das ist für robuste Pipelines akzeptabel.

**Betriebsprofil**

Total 71.45s. Modellaufrufe 2.08s und 8.79s, MCP-Latenz 1.04s. Für produktive Tool-Ketten langsam. Kosten pro Run 0.111900 USD. Für die gelieferte Tool-Qualität vertretbar, für die schwächere Synthese teuer.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen das Modell Tools auswählen, Calls sauber ausführen und Fehler transparent behandeln soll. Nicht geeignet als letzte Instanz für Compliance, Policy-Synthese oder mehrsprachige Ergebnisverdichtung ohne strikte Quellenausgabe, Assertions oder zweiten Verifikationsschritt. Wer ein Modell sucht, dem man primär die Tool-Infrastruktur übergibt, kann es einsetzen. Wer ihm zusätzlich die letzte semantische Verdichtung ungeprüft überlässt, sollte es nicht freischalten.