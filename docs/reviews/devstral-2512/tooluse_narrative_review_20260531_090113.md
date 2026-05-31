**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:01:13


Nicht deploy für autonome MCP-Tool-Pipelines, weil der kombinierte Befund mit 39.83 als weak ausfällt und zugleich kein valider Tool-Call nachgewiesen wurde. Dass keine Halluzination erkannt wurde, verhindert nur den schlimmsten Ausfallmodus. Es belegt keine belastbare Tool-Fähigkeit.

**Tool-Execution-Profil**

Das Kernproblem ist nicht ein einzelner Fehlgriff, sondern fehlende positive Evidenz für protokollkonforme Tool-Nutzung. `tool_call_valid=false` ist für produktive MCP-Umgebungen ein harter Warnhinweis, weil damit weder korrekte Werkzeugwahl noch saubere Aufrufstruktur bestätigt sind. Bei den Tests Web Search & Tool Selection, die prüfen ob ohne Hinweis `web_search` statt `fetch` gewählt wird, und URL Construction & Fetch, die die eigenständige Ableitung einer Ziel-URL messen, liegen nur n/a-Werte vor. Damit gibt es keinen belastbaren Nachweis, dass Devstral 2 Werkzeugwahl intelligent an den Informationsbedarf anpasst statt einem starren Muster zu folgen. Positiv ist nur, dass kein Retry erforderlich war. Das spricht eher gegen ein reines Formatproblem und eher für fehlende oder nicht verifizierbare Ausführungskompetenz im Ablauf selbst.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es praktisch keine verwertbare Evidenz. P2 ist durchgängig n/a, daher lässt sich nicht belegen, dass Devstral 2 extrahierte Web-Inhalte präzise zusammenführt, priorisiert und korrekt auf Deutsch verdichtet. Für Architekturen, die ein Modell als letzten semantischen Aggregator einsetzen, ist genau diese Lücke kritisch.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, hat keine Halluzination gezeigt. Das ist ein Vertrauenssignal. Es ist aber nur ein negatives Sicherheitsereignis, kein Qualitätsbeweis für echte Quellenbindung.

**Fehlerresilienz**

Im 404-Test, der transparentes Fehlverhalten gegen halluzinierten Ersatzinhalt prüft, hat Devstral 2 keinen Seiteninhalt erfunden. Das ist für Produktion wichtig. Ein Modell darf bei Tool-Fehlern stoppen und den Fehler melden. Es darf nicht kompensieren, indem es plausible Fakten erfindet. Diese Mindestanforderung erfüllt Devstral 2 nach den vorliegenden Daten.

**Souveränitätsprofil**

Lokal betreibbar ja, aber nicht fleet-kompetitiv. Devstral 2 liegt 4.01 Punkte unter dem Fleet-Ø von 66.21.

**Fazit & Empfehlung**

Geeignet höchstens als lokales Coding-Modell in eng geführten, stark validierten Pipelines, in denen externe Orchestrierung die Tool-Wahl übernimmt und jede Tool-Antwort strukturell geprüft wird. Nicht geeignet als eigenständiger MCP-Agent für Recherche, URL-Ableitung, dynamische Tool-Selektion oder synthesislastige Wissensarbeit. Wenn Sie einem Modell Infrastruktur übergeben wollen, brauchen Sie hier mehr als ein ausbleibendes Halluzinationssignal. Sie brauchen belegte Ausführungssicherheit, und die fehlt.