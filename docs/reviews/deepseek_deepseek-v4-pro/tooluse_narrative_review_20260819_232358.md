**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:23:58


Bedingt deploy, weil die Tool-Nutzung stark ist, aber die Tool-Calls nicht durchgängig valide sind und die Synthesequalität für produktionsnahe Wissenspipelines nur mittel belastbar ausfällt.

**Tool-Execution-Profil**

DeepSeek V4 Pro zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch nötig ist, wählt es das richtige Werkzeug souverän und erreicht volle Ausführungssicherheit. Das spricht gegen ein starres Abrufmuster und für brauchbare Planung in dynamischen MCP-Pipelines.

Schwächer wirkt es beim URL-Construction-Test, der die präzise Ableitung einer Ziel-URL aus Eigenwissen verlangt. Dort ist die Ausführung brauchbar, aber nicht deterministisch genug für Systeme, die auf exakt reproduzierbare Fetch-Pfade angewiesen sind. Der zentrale operative Makel bleibt, dass der Tool-Call insgesamt nicht valide war. Das ist kein Kollaps der Tool-Fähigkeit, aber ein Integrationsrisiko auf Protokollebene. Positiv ist, dass kein Retry nötig war. Das spricht eher gegen ein reines Formatproblem und eher für inkonsistente Call-Präzision in einzelnen Pfaden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt, dass DeepSeek V4 Pro Ergebnisse meist korrekt zusammenzieht, aber Details nicht stabil genug priorisiert. Das sieht man auch in HTTP Fetch & Extract und URL Construction & Fetch, wo die Tool-Nutzung tragfähig ist, die verdichtete Ausgabe aber zu wenig Präzision für belastbare Downstream-Entscheidungen liefert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Modell vertrauenswürdiger als der P2-Wert vermuten lässt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert es nicht. Das ist für Compliance-nahe Recherchepfade ein wesentliches positives Signal. Es bleibt also eher konservativ im Evidenzraum, auch wenn die Zusammenfassung nicht scharf genug ist.

**Fehlerresilienz**

Beim 404-Test, der misst, ob ein Modell nach einem fehlgeschlagenen Tool-Aufruf transparent bleibt oder Ersatzinhalt erfindet, halluziniert DeepSeek V4 Pro keinen Seiteninhalt. Das ist der entscheidende Punkt. Die Reaktion ist dennoch schwach verdichtet und kommunikativ nicht sauber genug, daher der niedrige Synthesewert. Für Produktion ist das akzeptabel, weil Transparenz bei Fehlern wichtiger ist als Eleganz in der Formulierung.

**Betriebsprofil**

Total 200.37s pro Run. Langsam.  
Call-Latenzen 4.59s und 27.47s, MCP 1.34s.  
Kosten local. Preisblatt: $0.435 pro 1M Input, $0.87 pro 1M Output. Günstig für Frontier-Klasse, aber die Laufzeit ist hoch im Verhältnis zur Ergebnisqualität.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, lange Kontexte und vorsichtige Fehlerbehandlung wichtiger sind als perfekte Endverdichtung. Nicht die erste Wahl für Compliance-Freigaben, präzise Faktenextraktion oder streng deterministische MCP-Strecken mit harten Schema- und URL-Anforderungen. Deploy nur mit enger Tool-Call-Validierung, Output-Checks und einem nachgelagerten Verifier für Synthesequalität.