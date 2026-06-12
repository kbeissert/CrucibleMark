**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:44:34


Bedingt deploy, weil die Tool-Ausführung stark und protokollsauber ist, die Synthesetreue aber mit erkannten Halluzinationen kein blindes Vertrauen in die Ergebnisverdichtung erlaubt.

**Tool-Execution-Profil**

Das Modell ist klar tool-fähig. P1 von 90 zeigt, dass es MCP-konforme Aufrufe erzeugt, valide Calls liefert und keine Retries brauchte. Für produktive Tool-Pipelines ist das die zentrale Eintrittsbedingung, und die erfüllt es.

Bei der Werkzeugwahl zeigt es echte Situationsanpassung statt reinem Musterlauf. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Fetch erzwingt, erreicht es P1 100. Das spricht dafür, dass es den Informationsbedarf korrekt erkennt. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und danach korrekt fetchen soll, landet es bei P1 80. Es kann also direkte Fetch-Pfade nutzen, aber nicht präzise genug für vollständig deterministische URL-Ableitung. Das ist kein Protokollproblem, sondern ein Präzisionsproblem an der Werkzeuggrenze.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 51.67 ist der eigentliche Warnwert dieses Laufs. Besonders schwach ist HTTP Fetch & Extract, der strukturierte Fakten aus realem Seiteninhalt verlangt, mit P2 35. Noch kritischer: Im Test Web Search & Tool Selection, der eigentlich die richtige Rechercheentscheidung misst, fällt die anschließende Verdichtung auf P2 15. Das Modell findet also Quellen, verliert aber beim Zusammenziehen der Inhalte an Genauigkeit und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt es im akzeptablen Bereich. P2 60 ist nicht stark, aber der Content-Verification-State A und keine Halluzination in diesem Test sind ein Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, untergräbt es die Verlässlichkeit der gesamten Pipeline.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert es produktionsgerecht. Im 404-Test, der transparenten Umgang mit fehlgeschlagenem Abruf statt erfundenem Seiteninhalt prüft, erreicht es P2 80 und halluziniert nicht. Das ist akzeptabel für den Einsatz. Ein Modell darf scheitern. Es darf dabei nur keinen Ersatzinhalt erfinden.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nah genug am Flottenschnitt, um lokale Nutzung ohne gravierenden Kompetenzverlust zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Coding- und Retrieval-Pipelines, in denen das Modell Tools auswählt, Aufrufe ausführt und Zwischenergebnisse mit nachgelagerter Validierung weiterreicht. Nicht geeignet als letzte autoritative Syntheseinstanz in Compliance-, Research- oder Faktenpipelines, wenn die Antwort ohne zweiten Prüfschritt direkt an Nutzer oder Systeme geht. Empfohlen ist ein Einsatz mit enger Ausgabevalidierung, Source-grounded Postprocessing und klarer Trennung zwischen Tool-Orchestrierung und finaler Ergebnisfreigabe.