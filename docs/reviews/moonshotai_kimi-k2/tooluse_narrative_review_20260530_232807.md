**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:07


Bedingt deploy, weil Kimi K2 valide Tool-Calls produziert und im Ablauf zuverlässig bleibt, aber die Verdichtung der Tool-Ergebnisse für produktionsnahe Wissenspipelines zu unstet ist.

**Tool-Execution-Profil**

Kimi K2 zeigt ein belastbares Tool-Profil. Die Tool-Calls waren valide, MCP-konform und ohne Retry ausführbar. Das ist für eine Tool-Pipeline der erste produktive Schwellenwert, und den erreicht das Modell klar. Besonders wichtig: Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch erzwingt, erkennt es sauber, dass zuerst web_search statt fetch nötig ist. Das spricht für echte Werkzeugwahl und nicht nur für starres Musterverhalten.

Beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen ableiten und dann fetch korrekt ausführen kann, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Es kann den nächsten Schritt planen, ist aber bei der konkreten Adressbildung weniger präzise als bei der strategischen Tool-Auswahl.

**Synthesetreue**

Wie gut verdichtet es? Nur eingeschränkt verlässlich. Der P2-Wert von 55 zeigt sich vor allem dort, wo mehrere Quellen oder Sprachräume zusammengeführt werden müssen. HTTP Fetch & Extract und Tool Failure Handling bleiben ordentlich, aber Web Search & Tool Selection fällt in der Antwortqualität deutlich ab, und Multilingual Search & Synthesis ist mit 15 klar zu schwach für belastbare Ergebnisverdichtung.

Bleibt es im Tool-Ergebnis? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, bleibt Kimi K2 im abgerufenen Material. Content-Verification-State A und keine Halluzination in diesem Test sind ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte Tool-Infrastruktur unzuverlässig, auch wenn die Tool-Ausführung selbst korrekt ist.

**Fehlerresilienz**

Im 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Call prüft, reagiert Kimi K2 produktionsgerecht. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Genau dieses Verhalten ist in laufenden Pipelines akzeptabel, weil Orchestrierung und Monitoring darauf aufsetzen können.

**Betriebsprofil**

Total 94.08s. Erste Antwort 2.93s, MCP-Latenz 1.33s, zweiter Call 11.42s. Insgesamt langsam. Kosten pro Run 0.006264. Günstig im Verhältnis zur gezeigten Tool-Kompetenz.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen Tool-Wahl, mehrstufige Ausführung und sauberes Fehlerverhalten wichtiger sind als hochwertige Endverdichtung: Recherche-Orchestrierung, Coding-Agenten, Retrieval mit menschlicher Nachsicht. Nicht geeignet für Compliance-, Policy-, Executive-Briefing- oder multilingualen Wissensoutput, wenn das Modell die Tool-Ergebnisse selbst präzise und vollständig zusammenziehen soll. Für Produktion nur mit enger Output-Kontrolle, Schema-Validierung und nachgelagerter Verifikation deployen.