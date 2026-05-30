**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:55


Nicht deploy für autonome MCP-Pipelines, weil der kombinierte Befund schwach ist, Tool-Calls nicht durchgehend valide sind und ein Halluzinationssignal im Lauf erkannt wurde.

**Tool-Execution-Profil**

Mistral Medium 1.0 zeigt kein verlässliches Werkzeugurteil. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis `web_search` statt `fetch` gewählt wird, fällt es klar ab. Das spricht gegen echte Tool-Intelligenz in offenen Situationen. Beim URL-Construction-&-Fetch-Test, der die Ableitung einer Ziel-URL aus Vorwissen misst, ist es deutlich besser. Das Muster wirkt deshalb nicht wie adaptive Werkzeugwahl, sondern wie ein engeres Erfolgsfenster bei direktem Fetch, sobald die Route schon relativ klar ist.

Die Tool-Ausführung selbst ist damit nur teilweise belastbar. HTTP Fetch & Extract und der 404-Fall gelingen brauchbar, aber die ungültigen Tool-Calls zeigen, dass das Modell das MCP-Schema nicht stabil genug hält. Dass ein Retry erforderlich war, wirkt hier eher wie ein Verständnis- und Entscheidungsproblem als ein reines Formatproblem. Es verfehlt nicht nur die Oberfläche des Protokolls, sondern oft schon die richtige Aktionslogik.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist insgesamt schwach, und das sieht man an den Rechercheaufgaben besonders deutlich. Bei EU License Research, also der Prüfung auf aktuelle Lizenzrestriktionen aus Web-Quellen, bleibt die Verdichtung unpräzise und wenig belastbar. Auch bei Web Search & Tool Selection und bei mehrsprachiger Recherche trägt es Ergebnisse nicht sauber genug zu einer belastbaren Antwort zusammen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research ist kein direkter Halluzinationsfall markiert, aber der Verifikationszustand B2 bei sehr niedriger P2 ist kein Vertrauenssignal. Das Modell bleibt also nicht sicher genug an der Quelle. Da im Gesamtlauf Halluzination erkannt wurde, ist das ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als angebliche Tool-Ergebnisse ausgibt, verliert die gesamte Tool-Infrastruktur ihren Nachweischarakter.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call misst, verhält sich das Modell akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler sauber. Das ist produktionsrelevant positiv. Es zeigt, dass Ausfälle nicht automatisch zu Ersatzfakten führen.

**Betriebsprofil**

Call 1: 5.21s  
MCP-Latenz: 0.21s  
Call 2: 4.50s  
Total: 59.59s  
Kosten/Run: local  

Langsam im Gesamtlauf. Kostenseitig lokal, aber die Laufzeit steht nicht im Verhältnis zur gezeigten Tool-Qualität.

**Fazit & Empfehlung**

Geeignet allenfalls für assistierte Pipelines mit harter Orchestrator-Kontrolle, starker Tool-Validierung und menschlichem Review nach jeder Recherche- oder Synthesestufe. Nicht geeignet für autonome Rechercheketten, Compliance-nahe Workflows, dynamische Tool-Auswahl oder Systeme, in denen Tool-Ausgaben als vertrauenswürdige Grundlage weiterverarbeitet werden. Für produktiven MCP-Einsatz braucht dieses Modell zu viel Absicherung, um noch ein sinnvoller Infrastrukturbaustein zu sein.