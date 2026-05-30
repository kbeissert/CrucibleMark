**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:21


Bedingt deploy, weil GLM-4.7 valide Tool-Calls produziert und die Tool-Ausführung solide ist, aber die Synthesetreue mit Combined 62.75 nur mäßig ausfällt und ein Halluzinationssignal in der Gesamtauswertung für produktive Tool-Pipelines ein Sicherheitsrisiko bleibt.

**Tool-Execution-Profil**

GLM-4.7 arbeitet auf der Ausführungsebene brauchbar. P1 83.33 zeigt, dass es MCP-konforme Aufrufe erzeugt, das Protokoll einhält und ohne Retry auskommt. Das ist für Orchestrierung wichtig, weil kein zusätzlicher Kontrollpfad für Formatfehler nötig wird.

Bei der Werkzeugwahl zeigt das Modell echtes Unterscheidungsvermögen, nicht nur ein starres Fetch-Muster. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Abruf prüft, erreicht es P1 100 und erkennt den Bedarf für web_search zuverlässig. Im Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen prüft, bleibt es mit P1 80 solide, aber nicht deterministisch genug für fragile Pipelines mit harter URL-Abhängigkeit. Das Muster ist klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei vorab konstruierten Endpunkten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 42.50 ist der eigentliche Engpass. Die Ausführung bringt Daten in die Pipeline, aber das Modell verdichtet sie oft zu grob oder verliert relevante Details. Das sieht man besonders bei EU License Research mit P2 20 und Multilingual Search & Synthesis mit P2 20. Für Workflows, in denen extrahierte Fakten präzise in eine Entscheidungsvorlage überführt werden müssen, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Halluzinationssignal zwar aus, aber der Content-Verification-State B1 und P2 20 zeigen kein belastbares Quellenhalten. Das ist kein bloßer Qualitätsmangel. Wenn ein Modell in einer Tool-Pipeline erfundene oder unzureichend verifizierte Fakten als Tool-Ergebnis ausgibt, wird die Infrastruktur selbst unzuverlässig.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call prüft, bleibt GLM-4.7 akzeptabel. P2 60 ist nicht stark, aber entscheidend ist: Es halluziniert keinen Seiteninhalt trotz Fehler. Damit ist das Modell bei Tool-Ausfällen eher defensiv als erfinderisch. Das ist produktionsfähig.

**Betriebsprofil**

Call 1: 12.90s. Call 2: 21.16s. MCP-Latenz: 1.44s. Total: 212.95s.  
Langsam für die erreichte Qualität.  
Kosten/Run: 0.004277. Günstig.

**Fazit & Empfehlung**

GLM-4.7 passt in kostengetriebene Pipelines, in denen Tools primär korrekt aufgerufen werden müssen und ein nachgelagerter Validator die Ergebnisverdichtung prüft, etwa Recherche-Vorstufen, Discovery-Schritte oder fehlertolerante Assistenten. Für Compliance, Lizenzprüfung, mehrsprachige Recherche mit deutscher Endsynthese und jede Pipeline, in der Tool-Ergebnisse ohne menschliche Kontrolle in Entscheidungen oder Kundenausgaben gehen, würde ich es nicht freigeben. Die Tool-Schicht ist brauchbar. Die Vertrauensschicht ist es noch nicht.