**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:20:53


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue zu schwach und der Tool-Call nicht durchgängig valide war. Für produktive MCP-Pipelines reicht reine Ausführungsstärke hier nicht aus.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den richtigen Zugriffspfad sehr zuverlässig. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen prüft, arbeitet es brauchbar, aber weniger deterministisch. Das spricht für sinnvolle Tool-Wahl, aber nicht für durchgehend präzise Ausführung.

Kritisch bleibt, dass der Tool-Call insgesamt nicht als valide markiert wurde. Das ist kein Retry-Thema und damit eher ein Protokoll- oder Formatrisiko im Erstlauf als ein bloßer Flüchtigkeitsfehler. Für MCP-Infrastrukturen bedeutet das: gute Planungslogik, aber zusätzlicher Guardrail-Bedarf bei Call-Validierung und Schema-Prüfung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 56.67 der klare Schwachpunkt des Modells. Man sieht das besonders bei EU License Research und Multilingual Search & Synthesis: Es beschafft Informationen, verdichtet sie dann aber zu grob, lässt relevante Einschränkungen liegen oder priorisiert Nebenaspekte. Für reine Retrieval-Pipelines ist das noch handhabbar. Für Compliance, Policy oder entscheidungsnahe Zusammenfassungen ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training kommen, halluziniert es nicht. Das ist der zentrale Vertrauenspunk. Der sehr niedrige P2-Wert dort zeigt also kein freies Erfinden, sondern unzureichende Auswertung real beschaffter Inhalte. Das ist besser als Halluzination, aber für sensible Domänen noch nicht ausreichend.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlschlagende Tool-Calls prüft, verhält sich das Modell produktionstauglich. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler nachvollziehbar. Genau dieses Verhalten braucht eine Tool-Pipeline: sichtbarer Fehler statt plausibel klingender Fiktion.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit souverän einsetzbar. Mit 71.29 Combined liegt es n/a-Punkte unter dem Fleet-Ø von 68.12. Inhaltlich heißt das: lokal und dennoch fleet-kompetent, aber nicht robust genug, um ohne zusätzliche Kontrollschicht als eigenständige Tool-Syntheseinstanz zu laufen.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Orchestrierungspipelines, in denen das Modell Tools auswählt, Suchpfade anstößt und Rohresultate an nachgelagerte Validatoren oder strengere Summarizer übergibt. Nicht geeignet als letzte Instanz für Compliance-Zusammenfassungen, mehrsprachige Verdichtung oder jede Pipeline, in der das Modell Tool-Ergebnisse selbst verbindlich interpretieren muss. Empfehlung: als lokaler Tool-Operator mit harter Call-Validierung und separater Answer-Verification einsetzen, nicht als autonomer Endentscheider.