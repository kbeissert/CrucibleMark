**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:22


Bedingt deploy, weil GLM-4.7 valide Tool-Calls erzeugt und in der Ausführung verlässlich wirkt, aber die Synthesetreue mit Combined 62.75 und klar schwacher P2-Leistung nicht ausreicht, um einer Tool-Infrastruktur ungeprüft vertraut zu werden.

**Tool-Execution-Profil**

Die Tool-Nutzung ist der belastbare Teil dieses Modells. P1 bei 83.33 zeigt, dass GLM-4.7 MCP-konform arbeitet, valide Calls produziert und keinen Retry brauchte. Besonders wichtig: Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erreicht es P1 100. Das spricht für echte Werkzeugwahl statt starrem Fetch-Muster. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL prüft, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für Pipelines mit harter URL-Präzision. Das Muster ist also klar: gute Auswahl des Werkzeugtyps, etwas weniger Präzision bei der konkreten Zieladressierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 bei 42.50 ist der eigentliche Engpass. In EU License Research und Multilingual Search & Synthesis fällt die Verdichtung deutlich ab, jeweils mit P2 20. Auch bei HTTP Fetch & Extract bleibt die Extraktion strukturierter Fakten zu unpräzise. Das Modell ruft Informationen oft korrekt ab, transformiert sie aber nicht stabil genug in eine saubere, überprüfbare Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, liegt der Content-Verification-State nur bei B1 und P2 bei 20. Positiv ist, dass dort keine Halluzination erkannt wurde. Negativ ist, dass der Output trotzdem nicht eng genug an den Quellen bleibt. Da global Halluzination erkannt wurde, ist das als Sicherheitsrisiko zu lesen: Sobald ein Modell erfundene Fakten als Tool-Ergebnis präsentiert, wird die Tool-Kette selbst unglaubwürdig.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Aufrufen prüft, reagiert GLM-4.7 akzeptabel. P2 60 ist nicht stark, aber entscheidend ist: Es halluziniert keinen Seiteninhalt trotz Fehler. Für Produktion ist das die Mindestanforderung, und die erfüllt es.

**Betriebsprofil**

Call 1 12.90s, Call 2 21.16s, MCP-Latenz 1.44s, Total 212.95s. Langsam. Kosten pro Run 0.004277. Günstig. Im Verhältnis zur Leistung ist das Preisprofil gut, das Latenzprofil jedoch schwach.

**Fazit & Empfehlung**

Geeignet für kostenbewusste Tool-Pipelines mit nachgelagerter Validierung, klaren Antwortformaten und geringer Toleranz für Tool-Fehler, aber nicht für Compliance-, Research- oder mehrsprachige Entscheidungsstrecken, in denen die Antwort selbst als verlässliche Verdichtung des Tool-Outputs dienen muss. Wer GLM-4.7 einsetzt, sollte es als Tool-Ausführer mit strenger Output-Prüfung behandeln, nicht als vertrauenswürdige Syntheseinstanz.