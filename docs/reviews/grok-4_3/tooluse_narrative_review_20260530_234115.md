**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:15


Bedingt deploy, weil Grok 4.3 valide Tool-Calls produziert und keine Halluzination im Lauf gezeigt hat, aber die Synthesetreue für produktionsnahe Tool-Pipelines zu unzuverlässig bleibt.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet das Modell grundsätzlich verwertbar. Die Calls waren valide, MCP-konform und ohne Retry ausführbar. Das ist für Integratoren der erste Schwellenwert, und den erfüllt Grok 4.3. Auffällig ist aber das Profil: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erreicht es nur solide statt sichere Leistung. Beim URL-Construction-Test, der die korrekte Ziel-URL aus eigenem Wissen ableitet und dann fetch ausführt, bleibt es auf demselben Niveau. Das spricht eher für brauchbare Standardheuristik als für robuste Werkzeugintelligenz. Es erkennt oft den richtigen Pfad, aber nicht mit der Präzision, die man für deterministische Agentenketten erwartet.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Schwäche. Die P2-Leistung ist insgesamt niedrig, und das sieht man in den Einzelergebnissen deutlich: EU License Research nur 20, mehrere weitere Aufgaben bei 40. Nur HTTP Fetch & Extract sowie Multilingual Search & Synthesis wirken tragfähig. Das Modell kann also Inhalte aus Tools übernehmen, verdichtet sie aber zu oft unvollständig, unscharf oder mit zu wenig Verifikationsdisziplin.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist das Vertrauenssignal gemischt. Positiv: keine Halluzination erkannt. Kritisch: P2=20 bei Content-Verification-State B2. Das Modell erfindet hier nichts, aber es bleibt auch nicht sauber genug an den abgerufenen Evidenzen. Für Compliance-nahe oder regulatorische Pipelines ist das zu wenig.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf misst, halluziniert Grok 4.3 keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Antwortqualität bleibt mit P2=40 nur mäßig, aber transparente Fehlerkommunikation ist akzeptabel. Damit bricht das Modell im Fehlerfall nicht das Vertrauen in die Tool-Infrastruktur.

**Betriebsprofil**

Call 1: 2.70s. MCP-Latenz: 0.92s. Call 2: 5.17s. Gesamt: 52.75s.  
Kosten pro Run: $0.011412.  
Direktes Urteil: moderat schnell in den Einzelaufrufen, aber langsam im End-to-End-Lauf. Günstig bis moderat im Preis, gemessen an einer nur mittleren Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für allgemeine Recherche-Pipelines, interne Assistenten und Workflows, in denen Tools korrekt aufgerufen werden müssen und Fehler offen benannt werden dürfen. Nicht geeignet für Compliance, Lizenzprüfung, regulatorische Auswertung oder andere Ketten, in denen die Verdichtung von Tool-Ergebnissen selbst belastbar sein muss. Wenn Sie Grok 4.3 einsetzen, dann mit nachgelagerter Validierung, enger Output-Schematisierung und klarer Trennung zwischen Tool-Resultat und freier Zusammenfassung.