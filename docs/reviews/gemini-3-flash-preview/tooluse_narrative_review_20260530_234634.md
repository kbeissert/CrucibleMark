**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:46:34


Bedingt deploy, weil die Tool-Ausführung verlässlich wirkt und keine Halluzination erkannt wurde, die Synthesequalität mit 56.67 aber zu schwach für unbeaufsichtigte Entscheidungsstrecken ist.

**Tool-Execution-Profil**

Gemini 3 Flash Preview arbeitet auf MCP-Ebene sauber. Die Tool-Calls waren valide, ein Retry war nicht erforderlich, und der P1-Wert von 86.67 bestätigt ein belastbares Ausführungsprofil. Für produktive Tool-Pipelines ist das die wichtigste Eintrittshürde, und die nimmt das Modell.

Bei der Werkzeugwahl zeigt es brauchbare, aber nicht durchgehend präzise Intelligenz. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es 80 und erkennt den Bedarf meist korrekt. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen misst, liegt es ebenfalls bei 80. Das spricht nicht für starres Pattern-Matching, aber auch nicht für deterministische Werkzeugplanung. In dynamischen Pipelines kann man ihm die Tool-Schicht anvertrauen. Für eng kontrollierte Abläufe mit exakter Tool-Disambiguierung bleibt Absicherung sinnvoll.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Der P2-Wert von 56.67 zeigt ein wiederkehrendes Muster: Das Modell extrahiert Fakten meist korrekt, verdichtet sie aber zu grob, setzt Prioritäten nicht stabil und verliert bei Such- und Mehrsprachenaufgaben an Präzision. Das sieht man besonders bei Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils 40 P2. Für Operatoren, die aus Tool-Output direkt entscheidungsreife Kurzlagen erwarten, ist das zu wenig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal positiv. Beim Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, gab es keine Halluzination. Content-Verification-State A ist für Compliance-nahe Recherchepfade ein gutes Zeichen. Das Modell bleibt also grundsätzlich an der Quelle, auch wenn es die Quelle nicht stark genug verdichtet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Aufruf gegen erfundenen Ersatzinhalt stellt, halluzinierte das Modell keinen Seiteninhalt. Die P2 von 60 zeigt keine elegante Fehleraufbereitung, aber das entscheidende Verhalten stimmt: Es bricht Vertrauen nicht durch erfundene Inhalte.

**Betriebsprofil**

Call 1: 1.61s. MCP-Latenz: 1.25s. Call 2: 6.95s. Total: 58.85s.  
Kosten pro Run: $0.007878.  
Direkte Einordnung: günstig, aber im Gesamtrun nicht schnell genug, um die nur mittlere Syntheseleistung zu kompensieren.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines, in denen das Modell primär Tools korrekt ausführt, Rohresultate einsammelt und ein Mensch oder ein nachgelagerter Prüfschritt die Verdichtung absichert. Weniger geeignet für autonome Recherche- und Compliance-Workflows, in denen die Antwort selbst bereits belastbar priorisiert und formuliert sein muss. Wenn Sie es einsetzen, dann als zuverlässigen Tool-Operator, nicht als finalen Synthese-Layer.