**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:16:27


Bedingt deploy, weil die Tool-Nutzung stark ist, aber die Synthesetreue mit Combined 79.17 nur dann tragfähig ist, wenn nachgelagerte Validierung die Antwortverdichtung kontrolliert. Halluzination wurde nicht erkannt, aber der Tool-Call war nicht durchgehend valide.

**Tool-Execution-Profil**

Das Modell ist in der Werkzeugwahl klar brauchbar. Beim Test Web Search & Tool Selection, der ohne Hinweis prüft, ob statt fetch ein Suchwerkzeug nötig ist, erkennt es den richtigen Zugriffspfad sicher. Das spricht gegen bloßes Musterausführen und für echte Werkzeugselektion. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Eigenwissen ableiten soll, bleibt es brauchbar, aber nicht deterministisch genug für Pipelines, die exakte Adressbildung voraussetzen. Insgesamt ist P1 mit 90 stark, nur die formale Validität der Tool-Calls ist nicht sauber genug, um das Modell unbeaufsichtigt an strikte MCP-Schnittstellen zu hängen. Retry war nicht nötig. Das ist eher ein Präzisions- als ein Verständnisproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die starken Tool-Aktionen übersetzen sich nicht in gleich starke Ergebnisaufbereitung. Das sieht man vor allem bei EU License Research, wo die eigentliche Recherche sitzt, die Verdichtung aber schwach bleibt, und bei Multilingual Search & Synthesis, wo die Recherche über Sprachgrenzen gelingt, die deutsche Zusammenführung aber an Präzision verliert. Für produktive Pipelines heißt das: Fakten kommen oft aus dem richtigen Kanal, aber die letzte Meile der Zusammenfassung braucht Kontrolle.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Der P2-Wert von 40 zeigt aber, dass Quellenbezug nicht automatisch zu belastbarer Verdichtung führt.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim Test Tool Failure Handling (404), der transparentes Verhalten bei einem fehlschlagenden Aufruf misst, hat das Modell keinen Seiteninhalt erfunden. Es kommuniziert Fehler also eher offen, statt Ersatzfakten zu erzeugen. Genau das braucht eine Tool-Pipeline.

**Betriebsprofil**

Total 417.80s pro Run. Langsam. Einzelaufrufe 7.92s und 60.26s, MCP-Latenz 1.45s. Kosten lokal. Wirtschaftlich vertretbar, wenn Durchsatz zweitrangig ist.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Orchestrationspipelines, in denen das Modell Tools auswählen, Suchpfade erkennen und Fehler sauber offenlegen muss. Nicht geeignet als letzte autoritative Syntheseschicht für Compliance, Lizenzbewertung oder andere textkritische Freigaben ohne zusätzliche Regel- oder Reviewer-Stufe. Wer dem Modell Infrastruktur übergibt, kann ihm die Werkzeugbedienung anvertrauen. Die Ergebnisverdichtung sollte er nicht allein abnehmen lassen.