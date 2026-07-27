**Deployment-Urteil**

> **Erstellt am:** 19.07.2026, 23:27:50


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, das Modell aber bei nachgewiesener Halluzination und invalidem Tool-Call nicht verlässlich genug für vertrauenskritische MCP-Pipelines arbeitet.

**Tool-Execution-Profil**

Qwen 3.6 27B zeigt echte Werkzeugwahl statt reinem Schablonenverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht für brauchbare Agentik im ersten Planungsschritt. Auch Multilingual Search & Synthesis und EU License Research erreichen in P1 volle Werte, was auf stabile Bereitschaft zur Tool-Nutzung hindeutet.

Schwächer wird es bei der präzisen Ausführung. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann fetch ausführen lässt, ist die Leistung brauchbar, aber nicht deterministisch. Noch kritischer ist der globale Befund `tool_call_valid: false`. Das heißt: Die Pipeline bekommt nicht durchgängig protokollsaubere, ausführbare Aufrufe. Für produktive MCP-Umgebungen ist das kein Detail, sondern ein Integrationsrisiko. Positiv ist nur, dass kein Retry nötig war. Das wirkt eher wie ein inhaltlich-prozedurales Zuverlässigkeitsproblem als ein bloßes Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 51.67 passt zum Asset-Bild: URL Construction & Fetch und Multilingual Search & Synthesis sind solide, HTTP Fetch & Extract bleibt bei strukturierter Faktenverdichtung schwach, und EU License Research bricht fast vollständig ein. Das Modell kann Ergebnisse zusammenführen, aber nicht konsistent mit der Präzision, die Architekten für belastbare Tool-Pipelines brauchen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, erzielt es P2=15 bei erkannter Halluzination. Das ist ein Sicherheitsrisiko. Sobald ein Modell erfundene oder vortrainierte Fakten als angebliche Tool-Ergebnisse ausgibt, verliert die gesamte Infrastruktur ihre Nachprüfbarkeit.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Seiteninhalt misst, erreicht es P2=80 und halluziniert keinen Ersatzinhalt. Das ist produktionsfähig. Das Modell scheitert also nicht primär an Fehlerkommunikation, sondern an Vertrauensbindung an echte Rechercheergebnisse.

**Betriebsprofil**

Total 159.64s pro Run. Call 1 schnell mit 3.11s. Call 2 sehr langsam mit 21.28s. MCP-Latenz 2.22s. Kosten local. Für die gezeigte Leistung zu langsam.

**Fazit & Empfehlung**

Geeignet für interne Recherche- und Vorbereitungs-Pipelines, in denen Tool-Wahl wichtig ist, Ergebnisse aber nachgelagert geprüft werden. Nicht geeignet für Compliance, Lizenzbewertung, regulatorische Recherche oder jede Pipeline, in der Tool-Ausgaben als belastbare Tatsachen weiterverarbeitet werden. Wenn Sie es einsetzen, dann nur mit harter Output-Validierung, Quellenbindung und einem Guardrail, der ungestützte Behauptungen verwirft.