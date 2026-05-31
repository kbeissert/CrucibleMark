**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:52:37


Bedingt deployen, weil das Modell Tools verlässlich und protokollkonform nutzt, aber die Synthesequalität mit Halluzinationsbefund nicht stabil genug für unbeaufsichtigte Endausgaben ist.

**Tool-Execution-Profil**

Bei der Tool-Ausführung ist Gemma 3 12B IT belastbar. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 von 90 zeigt, dass das Modell MCP-seitig sauber arbeitet. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den richtigen Werkzeugtyp sicher. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl im Kontext.

Schwächer ist es bei URL Construction & Fetch. Dort, wo das Modell die Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen muss, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist klar: gute Auswahl des Werkzeugtyps, etwas weniger Präzision bei der konkreten Zieladressierung. Für MCP-Orchestrierung ist das akzeptabel, solange nachgelagerte Validierung die Ziel-URL prüft.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 45.83 ist der eigentliche Engpass dieses Modells. In HTTP Fetch & Extract, also bei strukturierter Extraktion aus realem Seiteninhalt, fällt die Verdichtung deutlich ab. Auch bei Multilingual Search & Synthesis und Web Search & Tool Selection bleibt die Zusammenfassung oft zu grob. Das Modell kann Daten holen, aber es transformiert sie nicht zuverlässig in präzise, belastbare Nutzantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Trennung bei aktuellen Lizenzrestriktionen prüft, bleibt der Befund grundsätzlich vertrauensfähig: keine Halluzination, Content-Verification-State A. Gleichzeitig ist der globale Halluzinationsbefund als Sicherheitsrisiko zu werten. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als aus Werkzeugen gewonnen darstellt, wird die gesamte Infrastruktur epistemisch unsicher. Hier liegt der Kern des Vorbehalts.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsnah. Im Test Tool Failure Handling (404), der prüft, ob bei fehlgeschlagenem Abruf transparent berichtet oder Inhalt erfunden wird, kommuniziert es den Fehler sauber und halluziniert keinen Seiteninhalt. Das ist für Produktion akzeptabel. Diese Transparenz reduziert das Risiko stiller Fehlantworten deutlich.

**Souveränitätsprofil**

Lokal betreibbar und operativ attraktiv, aber nicht fleet-spitz. Das Modell läuft in der local_sovereign-Gruppe zu lokalen Kosten und liegt mit seinem Combined-Ergebnis 4.01 Punkte unter dem Fleet-Ø von 66.21. Für souveräne Umgebungen ist das nah genug am Durchschnitt, um realistisch einsetzbar zu sein.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen Tool-Auswahl, Rechercheanstoß und robuste Fehlerkommunikation wichtiger sind als hochwertige Endverdichtung. Gut einsetzbar als orchestrierendes Vorstufenmodell, Recherche-Agent oder kontrollierter Retriever mit nachgeschalteter Validierung. Nicht geeignet als alleinige letzte Instanz für Compliance, präzise Faktenextraktion oder nutzerseitige Final Answers ohne Guardrails, weil die Synthese nicht stabil genug ist und der Halluzinationsbefund das Vertrauensmodell der Pipeline angreift.