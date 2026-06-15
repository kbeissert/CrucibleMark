**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:26


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthesetreue aber für produktive Entscheidungs- oder Compliance-Pipelines nicht stabil genug wirkt. Der kombinierte Eindruck ist gut, aber das Halluzinationssignal und die schwache Verdichtung begrenzen das Vertrauensniveau.

**Tool-Execution-Profil**

Claude Opus 4.5 verhält sich auf MCP-Ebene kontrolliert. Die Tool-Calls waren valide, ein Retry war nicht erforderlich, und P1 von 86.67 zeigt eine belastbare operative Basis. Besonders wichtig: Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt werden muss, erkennt das Modell den richtigen Werkzeugtyp sicher. Das spricht gegen starres Schema-Verhalten und für echte Werkzeugwahl.

Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und anschließendes Fetch misst, bleibt die Ausführung brauchbar, aber weniger deterministisch. P1 80 ist ordentlich, zeigt aber: Es kann URLs konstruieren und abrufen, liefert dabei jedoch nicht die Präzision, die man für fragile, strikt formatierte Pipelines ohne Guardrails voraussetzen sollte.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 59.17 ist der klare Schwachpunkt. Die starken P1-Werte kippen in mehreren Aufgaben nicht in saubere Ergebnisverdichtung um. Das sieht man besonders bei EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis, wo die Tool-Nutzung funktioniert, die inhaltliche Zusammenführung aber zu grob oder unvollständig bleibt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht zuverlässig genug für Hochvertrauen. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis gezogen werden, lag P2 nur bei 40 bei Verification-State B1. Zwar wurde dort keine Halluzination markiert. Trotzdem ist der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als toolgestützte Antwort ausgeben kann, verliert die gesamte Tool-Infrastruktur ihre Beweiskraft.

**Fehlerresilienz**

Bei Tool-Fehlern ist das Modell produktionstauglich. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, blieb Claude Opus 4.5 sauber. Keine Halluzination trotz Fehler, P2 80. Das ist das Mindestniveau für robuste Agenten-Pipelines und hier erfüllt.

**Betriebsprofil**

Total 71.45s pro Run. Langsam.  
MCP-Latenz 1.04s, Modelllaufzeit dominiert die Gesamtdauer.  
Kosten 0.111900 USD pro Run. Teuer.  
Für die gezeigte Syntheseleistung ist das Kosten-Latenz-Profil nur bedingt attraktiv.

**Fazit & Empfehlung**

Geeignet für agentische Orchestrierung, Rechercheketten mit klaren Tool-Grenzen und Pipelines, in denen nachgelagerte Validierung die Endantwort prüft. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Workflows, in denen die natürliche Sprache selbst als vertrauenswürdiges Endprodukt dienen muss. Wenn Sie es einsetzen, dann als starken Tool-Bediener mit strikter Ergebnisverifikation, nicht als letzte Instanz für verdichtete Wahrheitsaussagen.