**Deployment-Urteil**

> **Erstellt am:** 17.06.2026, 08:04:50


Bedingt deploy, weil das Modell trotz brauchbarer Gesamtleistung keine verlässlich validen Tool-Calls liefert und bei werkzeugabhängigen Aufgaben zu oft die falsche Zugriffsstrategie wählt.

**Tool-Execution-Profil**

Das Profil ist gespalten. Wenn der Pfad klar ist, arbeitet das Modell solide. Beim HTTP Fetch & Extract extrahiert es sauber, und beim URL-Construction-Test, der prüft ob es eine Ziel-URL aus Vorwissen ableitet und dann korrekt per Fetch abruft, liegt es mit P1 80 auf produktiv nutzbarem Niveau. Auch Multilingual Search & Synthesis zeigt, dass die Ausführung über Sprachgrenzen hinweg strukturiert bleibt.

Das Kernproblem ist die Werkzeugwahl. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, fällt es mit P1 35 deutlich ab. Das spricht nicht für echte Tool-Intelligenz, sondern für ein Muster: Das Modell kann bekannte oder direkt ableitbare URLs bedienen, erkennt aber dynamische Recherchebedarfe nicht zuverlässig. Dass der Tool-Call insgesamt als nicht valide gewertet wurde, ist für MCP-Pipelines relevant. Das Risiko liegt nicht in einzelnen Syntaxfehlern, sondern in einem schwachen Protokollverständnis an der Entscheidungskante zwischen Suche und Abruf.

**Synthesetreue**

Wie gut verdichtet es? Die Verdichtungsqualität ist brauchbar, aber nicht stabil genug für hochwertige Rechercheketten. P2 63.68 bedeutet: Solide Zusammenfassungen aus vorhandenem Tool-Output, gute Extraktion bei klaren Quellen, starke Leistung bei mehrsprachiger Recherche. Sobald die Aufgabe aber Quellenbewertung oder vorsichtige Einordnung verlangt, fällt die Qualität sichtbar ab.

Bleibt es im Tool-Ergebnis? Hier ist das Vertrauenssignal gemischt. Im EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Training kommen, erreicht das Modell nur P2 20. Es wurde zwar keine Halluzination erkannt, aber es bleibt nicht verlässlich an der aktuellen Quellenlage. Für Compliance-nahe oder regulatorische Pipelines ist das ein klares Warnsignal: keine freie Freigabe ohne harte Quellenerzwingung und Output-Prüfung.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Aufruf misst, reagiert das Modell akzeptabel. P2 80 und keine halluzinierten Ersatzinhalte zeigen: Wenn ein Tool scheitert, erfindet es nicht automatisch Seiteninhalt. Das ist ein produktionsrelevanter Pluspunkt, weil Fehlerkommunikation die Pipeline intakt hält.

**Betriebsprofil**

Total 59.43s. Call 1 2.17s, MCP-Latenz 1.37s, Call 2 6.36s. Lokal betrieben, daher direkte Run-Kosten gering. Für die gebotene Leistung eher langsam.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren, vorstrukturierten Fetch-Aufgaben, Extraktion aus bekannten URLs und mehrsprachiger Verdichtung unter Guardrails. Nicht geeignet für offene Web-Recherche, Compliance-Workflows oder agentische Orchestrierung, in denen das Modell selbst das richtige Tool wählen und aktuelle Quellen strikt priorisieren muss. Wenn Sie es einsetzen, dann mit erzwungener Tool-Auswahl, Schema-Validierung und nachgelagerter Quellenkontrolle.