**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:06:31


Bedingt deploy, weil die Tool-Ausführung oft tragfähig ist, die Tool-Calls aber nicht durchgängig valide sind und die Synthesequalität für produktive MCP-Pipelines zu unstet bleibt. Der Combined-Score von 68.67 stützt ein begrenztes Ja, nicht die Freigabe als autonomes Standardmodell.

**Tool-Execution-Profil**

Gemma 4 31B Instruct zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr sicher. Das ist ein gutes Signal für dynamische Pipelines. Auch beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen ableitet und dann fetch verlangt, arbeitet es brauchbar, aber nicht deterministisch genug für sensible Abrufketten.

Das Kernproblem liegt weniger in der Absicht als in der Protokolltreue. P1 ist mit 83.33 solide, zugleich ist der Tool-Call global nicht valide. Für Architekten heißt das: Die Planungslogik ist vorhanden, aber das Modell braucht ein enges Call-Schema, Validierung vor Ausführung und sauberes Error-Gating im MCP-Layer.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 von 56.67 zeigt, dass Gemma 4 31B Instruct recherchierte Inhalte oft nur grob zusammenzieht. Das sieht man deutlich bei EU License Research und Multilingual Search & Synthesis, wo die Recherche selbst gelingt, die Verdichtung aber Präzision verliert. Für Workflows mit Compliance-, Policy- oder Detailpflicht ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die reine P2-Zahl. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Es erfindet also keine frischen Fakten aus dem Training. Das ist wichtig. Es bleibt aber nicht eng genug an den abgerufenen Inhalten.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei scheiterndem Tool-Aufruf misst, halluziniert das Modell keinen Seiteninhalt. Das ist produktionsrelevant positiv. Die Schwäche liegt in der Kommunikation und Verdichtung des Fehlers, nicht in erfundenem Ersatzinhalt. Transparente Fehlerbehandlung ist damit grundsätzlich vorhanden, aber nicht sauber genug für unbeaufsichtigte Ketten.

**Betriebsprofil**

Call 1: 17.63s. Call 2: 70.13s. MCP-Latenz: 1.20s. Total: 533.80s. Langsam für die erreichte Qualität. Kosten/Run: local. Günstig im Betrieb, aber die Zeitkosten sind hoch.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Routing-Pipelines, in denen Tool-Wahl wichtig ist, ein Orchestrator die Calls validiert und ein nachgelagerter Prüfschritt die Antwort verdichtet oder verifiziert. Nicht geeignet als freilaufendes Endmodell für Compliance, Lizenzauskünfte, mehrsprachige Entscheidungsvorlagen oder andere Pipelines, in denen die Zusammenfassung selbst belastbar sein muss. Wer lokale Souveränität und offene Gewichte will, kann es als Werkzeugnutzer einsetzen, aber nicht als letzte Instanz.