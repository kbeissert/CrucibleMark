**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:29:57


Bedingt deploy, weil die Tool-Nutzung zuverlässig und protokollkonform wirkt, die Synthesequalität aber für produktive Entscheidungsstrecken zu ungleichmäßig bleibt. Bei validen Tool-Calls, keiner erkannten Halluzination und einem guten Gesamtergebnis ist das Modell grundsätzlich übergabefähig, aber nicht ohne enge Leitplanken.

**Tool-Execution-Profil**

Das stärkste Signal ist die Werkzeugwahl. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell sauber, dass zuerst gesucht werden muss. Das spricht gegen starres Musterverhalten und für echte Tool-Intelligenz. Beim URL-Construction-and-Fetch-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines. Das ist kein MCP-Formatproblem, sondern ein Präzisionsproblem in der letzten Meile. Positiv bleibt, dass die Calls valide sind und kein Retry nötig war. Für agentische Flows ist das wichtig: Das Modell versteht die Infrastruktur und bedient sie regelkonform.

**Synthesetreue**

Wie gut verdichtet es? Nur ordentlich. Die Verdichtungsqualität liegt sichtbar unter der Ausführungsqualität. Bei HTTP Fetch & Extract hält es das Niveau, bei Multilingual Search & Synthesis bricht es deutlich ein. Das ist für produktive Pipelines relevant, weil nicht der Abruf, sondern die nachgelagerte Zusammenfassung oft in das System of Record wandert. Hier sollte man das Modell nicht ungeprüft als letzten verdichtenden Schritt einsetzen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es für EU License Research keine Honeypot-Daten. Das Vertrauensurteil bleibt daher unvollständig. Positiv ist nur der indirekte Befund: In den vorhandenen Aufgaben wurde keine Halluzination erkannt.

**Fehlerresilienz**

Beim 404-Test, der prüft ob ein Modell bei fehlschlagendem Tool transparent bleibt statt Seiteninhalt zu erfinden, reagiert Qwen akzeptabel. Es halluziniert keinen Ersatzinhalt. Das ist die Mindestanforderung für Produktion. Die P2-Schwäche zeigt aber, dass die Fehlerkommunikation nicht maximal klar und knapp verdichtet wird. Für Operations-Pipelines ist das tolerierbar. Für externe Nutzerantworten sollte man Fehlermeldungen dennoch templaten.

**Betriebsprofil**

3.13s erster Call. 34.19s zweiter Call. 190.54s total. MCP-Latenz 0.79s.  
Kosten pro Run: $0.004944.  
Fazit: günstig, aber langsam. Preislich attraktiv im Verhältnis zur Leistung. Latenzseitig nur für nicht interaktive oder asynchrone Tool-Pipelines sauber einsetzbar.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche- und Orchestrierungs-Pipelines, in denen richtige Tool-Wahl, valide Calls und transparente Fehlerbehandlung wichtiger sind als hochpräzise Endverdichtung. Nicht die erste Wahl für Compliance, Executive Summaries oder mehrsprachige Wissenssynthese ohne nachgelagerte Prüfung. Wegen des China-bezogenen Provenienzrisikos nur lokal oder in streng kontrollierter Umgebung einsetzen, wenn sensible Daten im Spiel sind. Als Tool-Operator brauchbar. Als vertrauenswürdiger finaler Synthese-Layer nur bedingt.